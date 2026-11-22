#!/usr/bin/env python3
"""Acquire four original GFM COG bands, keeping orbit/datatake and Item identity.

Metadata uses the pinned Atlantis backend. No daily merge, coarsening, or native
pixel changes occur here. Completed files and resumable .part files stay local.
"""

from __future__ import annotations
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date
import csv
import importlib.metadata
import json
from pathlib import Path
import sys
import subprocess
import os
import shutil
import time
from urllib.parse import urlparse
import requests

sys.path.insert(0, str(Path(__file__).resolve().parent))
from gfm_common import (
    DEFAULT_BBOX,
    DEFAULT_DATE,
    LAYERS,
    parse_source,
    protect_old,
    run_metrics,
    save_json,
    sha256,
    utc_now,
)


def catalogue(root, when, bbox, offline):
    request = dict(date=when, bbox=list(bbox), collection="GFM")
    spec, path = (
        root / "metadata/catalogue_request.json",
        root / "metadata/stac_items.json",
    )
    if spec.exists():
        if json.loads(spec.read_text()) != request:
            raise ValueError(
                "Different request in this output directory; choose a new output directory"
            )
        return json.loads(path.read_text())
    if offline:
        raise ValueError("No matching cached catalogue for offline mode")
    from atlantis.fetchers.gfm.backend import GfmStacBackend
    from atlantis.models.event import FloodEvent

    backend = GfmStacBackend()
    items = backend.search(
        FloodEvent(
            "Rhine_2021_3sec",
            tuple(bbox),
            date.fromisoformat(when),
            date.fromisoformat(when),
            ["gfm"],
        )
    )
    if len(items) >= backend.max_items:
        raise ValueError("STAC safety cap reached; catalogue completeness is unknown")
    data = items.to_dict()
    save_json(path, data)
    save_json(spec, request)
    return data


def orbit_metadata(root, pass_id, sources, offline, reuse_data_dir=None):
    """Optional official enrichment; orbit/datatake grouping does not depend on it."""
    path = root / "metadata" / f"orbit_{pass_id}.json"
    if path.exists():
        return json.loads(path.read_text())
    if reuse_data_dir is not None:
        source_path = reuse_data_dir / "metadata" / f"orbit_{pass_id}.json"
        if source_path.exists():
            result = json.loads(source_path.read_text())
            save_json(path, result)
            return result
    if offline:
        return dict(status="not available offline", products=[])
    clauses = " or ".join("startswith(Name,'" + n + "_')" for n in sorted(sources))
    endpoint = "https://catalogue.dataspace.copernicus.eu/odata/v1/Products"
    params = {
        "$filter": "Collection/Name eq 'SENTINEL-1' and (" + clauses + ")",
        "$expand": "Attributes",
        "$top": 100,
    }
    try:
        response = requests.get(endpoint, params=params, timeout=(20, 90))
        response.raise_for_status()
        result = dict(
            status="ok",
            endpoint=response.url,
            products=response.json().get("value", []),
        )
    except requests.RequestException as exc:
        result = dict(status=f"{type(exc).__name__}: {exc}", products=[])
        print(f"  Orbit enrichment unavailable: {exc}", flush=True)
    save_json(path, result)
    return result


def groups_for(data, root, offline, reuse_data_dir=None):
    groups = {}
    for item in data["features"]:
        source = parse_source(item)
        group = groups.setdefault(
            source["pass_id"],
            dict(
                pass_id=source["pass_id"],
                platform=source["platform"],
                absolute_orbit=source["absolute_orbit"],
                datatake=source["datatake"],
                items=[],
            ),
        )
        group["items"].append(dict(stac=item, **source))
    for group in groups.values():
        group["items"].sort(key=lambda x: (x["start_utc"], x["stac"]["id"]))
        group["start_utc"] = min(x["start_utc"] for x in group["items"])
        group["end_utc"] = max(x["end_utc"] for x in group["items"])
        result = orbit_metadata(
            root,
            group["pass_id"],
            {x["source_id"] for x in group["items"]},
            offline,
            reuse_data_dir,
        )
        group["orbit_metadata_status"] = result["status"]
        for field, attr in [
            ("relative_orbit", "relativeOrbitNumber"),
            ("orbit_direction", "orbitDirection"),
        ]:
            values = {
                x["Value"]
                for p in result["products"]
                for x in p.get("Attributes", [])
                if x["Name"] == attr
            }
            if len(values) > 1:
                raise ValueError(f"Conflicting {field} metadata in {group['pass_id']}")
            group[field] = next(iter(values)) if values else None
    return groups


def inspect_head(url):
    r = requests.head(url, timeout=(20, 90), allow_redirects=True)
    r.raise_for_status()
    if "Content-Length" not in r.headers:
        raise ValueError(f"No source size from HEAD: {url}")
    return dict(
        expected_bytes=int(r.headers["Content-Length"]),
        etag=r.headers.get("ETag"),
        last_modified=r.headers.get("Last-Modified"),
    )


def download_asset(asset, root, offline, reuse_data_dir=None):
    path = root / asset["path"]
    if path.exists():
        actual = sha256(path)
        if path.stat().st_size != asset["expected_bytes"] or (
            asset.get("sha256") and actual != asset["sha256"]
        ):
            raise ValueError(
                f"Existing asset is incomplete/changed; preserved for inspection: {path}"
            )
        return dict(
            sha256=actual, bytes=path.stat().st_size, reused=True, transferred_bytes=0
        )
    reused = False
    if reuse_data_dir is not None:
        source_path = reuse_data_dir / asset["path"]
        if source_path.exists():
            source_size = source_path.stat().st_size
            source_sha = sha256(source_path)
            if source_size != asset["expected_bytes"] or (
                asset.get("sha256") and source_sha != asset["sha256"]
            ):
                raise ValueError(
                    f"Existing reusable asset is incomplete/changed; preserved for inspection: {source_path}"
                )
            path.parent.mkdir(parents=True, exist_ok=True)
            part = path.with_suffix(path.suffix + ".part")
            shutil.copyfile(source_path, part)
            if part.stat().st_size != asset["expected_bytes"] or sha256(part) != source_sha:
                raise ValueError(f"Copied reusable asset failed integrity check: {part}")
            part.replace(path)
            asset["sha256"] = source_sha
            asset["reused_from"] = str(source_path)
            reused = True
            print(f"  Reused existing COG: {source_path}", flush=True)
            transferred = 0
        elif offline:
            raise ValueError(f"Missing local asset in offline mode: {source_path}")
        else:
            transferred = None
    else:
        transferred = None
    if transferred is None:
        if offline:
            raise ValueError(f"Missing local asset in offline mode: {path}")
        path.parent.mkdir(parents=True, exist_ok=True)
        part = path.with_suffix(path.suffix + ".part")
        transferred = 0
        for attempt in range(3):
            offset = part.stat().st_size if part.exists() else 0
            if offset > asset["expected_bytes"]:
                raise ValueError(f"Oversized partial file; inspect {part}")
            if offset == asset["expected_bytes"]:
                part.replace(path)
                break
            headers = {"User-Agent": "CaMa-Tutorial11-GFM/1.0"}
            if offset:
                headers["Range"] = f"bytes={offset}-"
                if asset.get("etag"):
                    headers["If-Range"] = asset["etag"]
            try:
                with requests.get(
                    asset["url"], stream=True, headers=headers, timeout=(20, 120)
                ) as r:
                    r.raise_for_status()
                    append = offset > 0 and r.status_code == 206
                    if append and not r.headers.get("Content-Range", "").startswith(
                        f"bytes {offset}-"
                    ):
                        raise ValueError(f"Invalid resume range for {path.name}")
                    with part.open("ab" if append else "wb") as stream:
                        for chunk in r.iter_content(1024 * 1024):
                            stream.write(chunk)
                            transferred += len(chunk)
                if part.stat().st_size != asset["expected_bytes"]:
                    raise requests.ConnectionError(f"Incomplete body: {part.name}")
                part.replace(path)
                break
            except requests.RequestException:
                if attempt == 2:
                    raise
                time.sleep(1)
    import rasterio

    with rasterio.open(path) as src:
        src.read(1, window=((0, 1), (0, 1)))
        geometry = dict(
            shape=[src.height, src.width],
            crs=src.crs.to_wkt(),
            transform=list(src.transform),
            nodata=src.nodata,
            dtype=src.dtypes[0],
            layout=src.tags(ns="IMAGE_STRUCTURE").get("LAYOUT"),
        )
    return dict(
        sha256=sha256(path),
        bytes=path.stat().st_size,
        reused=reused,
        transferred_bytes=transferred,
        geometry=geometry,
    )


def atlantis_commit():
    """Read the actual backend checkout; never label another version as pinned."""
    try:
        import atlantis
    except ModuleNotFoundError:
        return None

    module = Path(atlantis.__file__).resolve()
    for parent in module.parents:
        if (parent / ".git").exists():
            return subprocess.check_output(
                ["git", "-C", str(parent), "rev-parse", "HEAD"],
                text=True,
                env={**os.environ, "GIT_OPTIONAL_LOCKS": "0"},
            ).strip()
    return None  # A wheel may have version metadata without a Git checkout.


def atlantis_version():
    try:
        return importlib.metadata.version("opageo-atlantis")
    except importlib.metadata.PackageNotFoundError:
        return None


def acquire_selected_passes(args):
    """Read Step 2/3a handoffs and run the existing one-pass downloader per pass."""
    selection_path = args.selection_json.resolve()
    domain_path = args.domain_config.resolve()
    selection = json.loads(selection_path.read_text())
    declared_domain = (selection_path.parent / selection["source_domain_config"]).resolve()
    if declared_domain != domain_path:
        raise ValueError(
            "The supplied domain configuration does not match source_domain_config"
        )
    domain = json.loads(domain_path.read_text())
    bbox = domain["satellite_analysis"]["domain"]["bbox_west_south_east_north"]
    if len(bbox) != 4:
        raise ValueError("Satellite-analysis bbox must contain W, S, E, N")
    bbox = [float(value) for value in bbox]
    layers = selection["required_gfm_layers"]
    if not layers or len(set(layers)) != len(layers) or set(layers) - set(LAYERS):
        raise ValueError("required_gfm_layers must be unique supported GFM layers")
    passes = selection["passes"]
    if not passes:
        raise ValueError("No selected GFM passes are present in the selection file")

    for selected in passes:
        pass_id = selected["pass_id"]
        pass_date = selected["catalogue_date"]
        print(
            f"Step 3b input: {pass_id}, {pass_date}, bbox={bbox}, layers={layers}",
            flush=True,
        )
        pass_args = argparse.Namespace(**vars(args))
        pass_args.selection_json = None
        pass_args.domain_config = None
        pass_args.catalogue_root = None
        pass_args.run_root = None
        pass_args.date = pass_date
        pass_args.group = pass_id
        pass_args.bbox = bbox
        pass_args.layers = layers
        pass_args.output = args.catalogue_root / pass_date
        pass_args.work_dir = args.run_root / f"download_{pass_id}"
        acquire(pass_args)


def acquire(args):
    if args.selection_json is not None:
        if not all([args.domain_config, args.catalogue_root, args.run_root]):
            raise ValueError(
                "Selection mode requires --domain-config, --catalogue-root and --run-root"
            )
        return acquire_selected_passes(args)

    args.layers = tuple(args.layers or LAYERS)
    reuse_data_dir = args.reuse_data_dir.resolve() if args.reuse_data_dir else None
    start = time.monotonic()
    root = protect_old(
        args.output or args.work_dir / "data/Rhine_2021_3sec", args.work_dir
    )
    logs = protect_old(args.work_dir / "logs", args.work_dir)
    logs.mkdir(parents=True, exist_ok=True)
    data = catalogue(root, args.date, args.bbox, args.offline)
    groups = groups_for(data, root, args.offline, reuse_data_dir)
    summary = []
    for group in sorted(groups.values(), key=lambda x: x["start_utc"]):
        row = {k: v for k, v in group.items() if k != "items"}
        row["item_count"] = len(group["items"])
        row["timestamps"] = sorted({x["start_utc"] for x in group["items"]})
        summary.append(row)
        print(
            f"PASS {row['pass_id']}: {row['item_count']} Items, {row['start_utc']} — {row['end_utc']}, relative={row['relative_orbit']}, {row['orbit_direction']}",
            flush=True,
        )
    save_json(root / "metadata/pass_groups.json", summary)
    with (root / "metadata/item_inventory.csv").open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(
            [
                "item_id",
                "datetime_utc",
                "platform",
                "absolute_orbit",
                "datatake",
                "pass_id",
                "Equi7Tile",
                "source_product",
            ]
        )
        for g in groups.values():
            for x in g["items"]:
                w.writerow(
                    [
                        x["stac"]["id"],
                        x["start_utc"],
                        x["platform"],
                        x["absolute_orbit"],
                        x["datatake"],
                        x["pass_id"],
                        x["stac"]["properties"]["Equi7Tile"],
                        x["source_id"],
                    ]
                )
    if args.catalogue_only:
        save_json(
            logs / "gfm_catalogue_metrics.json",
            run_metrics(start, item_count=len(data["features"])),
        )
        return
    if args.group not in groups:
        raise ValueError(
            "Choose exactly one --group from the printed verified pass IDs"
        )
    group = groups[args.group]
    manifest_path = root / "metadata" / f"acquisition_{args.group}.json"
    reuse_manifest = None
    if reuse_data_dir is not None:
        source_manifest_path = (
            reuse_data_dir / "metadata" / f"acquisition_{args.group}.json"
        )
        if source_manifest_path.exists():
            reuse_manifest = json.loads(source_manifest_path.read_text())
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text())
        if (
            manifest["bbox"] != list(args.bbox)
            or manifest["date"] != args.date
            or manifest["layers"] != list(args.layers)
        ):
            raise ValueError(
                f"Existing acquisition manifest does not match requested date, bbox or layers: {manifest_path}"
            )
    else:
        assets, items = {}, []
        for number, x in enumerate(group["items"], 1):
            record = {k: v for k, v in x.items() if k != "stac"}
            record.update(
                item_id=x["stac"]["id"], index=number, stac=x["stac"], assets={}
            )
            for layer in args.layers:
                url = x["stac"]["assets"][layer]["href"]
                key = __import__("hashlib").sha256(url.encode()).hexdigest()[:16]
                name = Path(urlparse(url).path).name
                local = f"raw/{args.group}/assets/{key}_{name}"
                assets.setdefault(key, dict(url=url, path=local))
                record["assets"][layer] = key
            items.append(record)
        if reuse_manifest is not None:
            if (
                reuse_manifest.get("date") != args.date
                or reuse_manifest.get("bbox") != list(args.bbox)
                or reuse_manifest.get("layers") != list(args.layers)
            ):
                raise ValueError(
                    f"Reusable acquisition manifest does not match the requested pass: {source_manifest_path}"
                )
            for key, asset in assets.items():
                old_asset = reuse_manifest.get("assets", {}).get(key, {})
                if old_asset.get("url") == asset["url"]:
                    for field in ["expected_bytes", "etag", "last_modified", "sha256"]:
                        if field in old_asset:
                            asset[field] = old_asset[field]
        unresolved_assets = {
            key: asset for key, asset in assets.items() if "expected_bytes" not in asset
        }
        if unresolved_assets and args.offline:
            raise ValueError(
                "Offline mode needs existing size metadata for every selected COG"
            )
        if unresolved_assets:
            print(
                f"Inspecting compressed sizes for {len(unresolved_assets)} distinct native COGs",
                flush=True,
            )
            with ThreadPoolExecutor(max_workers=args.workers) as pool:
                futures = {
                    pool.submit(inspect_head, x["url"]): key
                    for key, x in unresolved_assets.items()
                }
                for future in as_completed(futures):
                    assets[futures[future]].update(future.result())
        total = sum(x["expected_bytes"] for x in assets.values())
        print(
            f"Complete native COGs: {total:,} bytes ({total / 2**20:.2f} MiB); preserving full original files",
            flush=True,
        )
        if total > args.max_download_mib * 2**20:
            raise ValueError(
                "Full-file budget exceeded: inspect metadata before selecting a new explicit budget/crop method"
            )
        manifest = dict(
            schema=1,
            event="Rhine_2021_3sec",
            date=args.date,
            bbox=list(args.bbox),
            pass_metadata={k: v for k, v in group.items() if k != "items"},
            layers=list(args.layers),
            atlantis_version=(
                reuse_manifest.get("atlantis_version")
                if reuse_manifest is not None
                else atlantis_version()
            ),
            atlantis_commit=(
                reuse_manifest.get("atlantis_commit")
                if reuse_manifest is not None
                else atlantis_commit()
            ),
            reused_source_manifest=(
                str(source_manifest_path) if reuse_manifest is not None else None
            ),
            assets=assets,
            items=items,
            created_utc=utc_now(),
            method="complete original COG; shared URLs stored once per pass",
        )
        save_json(manifest_path, manifest)
    transferred, reused = 0, 0
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = {
            pool.submit(download_asset, x, root, args.offline, reuse_data_dir): key
            for key, x in manifest["assets"].items()
        }
        for count, future in enumerate(as_completed(futures), 1):
            key = futures[future]
            result = future.result()
            manifest["assets"][key].update(result)
            transferred += result["transferred_bytes"]
            reused += int(result["reused"])
            save_json(manifest_path, manifest)
            print(
                f"[{count}/{len(futures)} assets] {'REUSE' if result['reused'] else 'GET'} {Path(manifest['assets'][key]['path']).name} ({result['bytes']:,} B)",
                flush=True,
            )
    for item in manifest["items"]:
        local = dict(item["stac"])
        item_dir = root / "raw" / args.group / "items"
        local["assets"] = {}
        for layer, key in item["assets"].items():
            asset = manifest["assets"][key]
            local["assets"][layer] = dict(
                href=os.path.relpath(root / asset["path"], item_dir),
                type="image/tiff; application=geotiff; profile=cloud-optimized",
                source_href=asset["url"],
                sha256=asset["sha256"],
            )
        save_json(item_dir / (item["item_id"] + ".json"), local)
        print(
            f"ITEM {item['index']}/{len(manifest['items'])} local: {item['item_id']}",
            flush=True,
        )
    metrics = run_metrics(
        start,
        pass_id=args.group,
        item_count=len(manifest["items"]),
        assets=len(manifest["assets"]),
        reused_assets=reused,
        transferred_bytes=transferred,
        complete_source_bytes=sum(x["bytes"] for x in manifest["assets"].values()),
        offline=args.offline,
    )
    save_json(
        logs / f"gfm_acquisition_{args.group}{'_offline' if args.offline else ''}.json",
        metrics,
    )
    print(json.dumps(metrics, indent=2), flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--work-dir", type=Path, default=Path.home() / "work/Atlantis")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--date", default=DEFAULT_DATE)
    parser.add_argument("--bbox", type=float, nargs=4, default=DEFAULT_BBOX)
    parser.add_argument("--group")
    parser.add_argument("--layers", nargs="+")
    parser.add_argument("--selection-json", type=Path)
    parser.add_argument("--domain-config", type=Path)
    parser.add_argument("--catalogue-root", type=Path)
    parser.add_argument("--run-root", type=Path)
    parser.add_argument("--reuse-data-dir", type=Path)
    parser.add_argument("--catalogue-only", action="store_true")
    parser.add_argument("--offline", action="store_true")
    parser.add_argument("--workers", type=int, choices=[1, 2], default=2)
    parser.add_argument("--max-download-mib", type=float, default=1024)
    args = parser.parse_args()
    acquire(args)


if __name__ == "__main__":
    main()

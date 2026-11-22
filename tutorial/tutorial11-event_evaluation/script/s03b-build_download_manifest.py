#!/usr/bin/env python3
"""Validate existing native GFM downloads and write the p03c handover files."""

from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from event_gfm_common import parse_source


FIELDS = [
    "pass_id",
    "stac_item_id",
    "item_datetime_utc",
    "asset_layer",
    "asset_key",
    "source_url",
    "local_path",
    "status",
    "file_size_bytes",
    "bbox",
    "crs",
    "sha256",
    "error",
]


def digest(path: Path) -> str:
    checksum = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            checksum.update(chunk)
    return checksum.hexdigest()


def atomic_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n")
    os.replace(temporary, path)


def atomic_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    os.replace(temporary, path)


def inspect_asset(path: Path, record: dict) -> dict:
    if not path.is_file():
        return dict(status="missing", file_size_bytes="", crs="", sha256="",
                    error="Expected asset file is missing")

    size = path.stat().st_size
    checksum = digest(path)
    errors = []
    if record.get("expected_bytes") is not None and size != record["expected_bytes"]:
        errors.append(
            f"size {size} != expected {record['expected_bytes']} bytes"
        )
    expected_hash = record.get("sha256")
    if expected_hash and checksum != expected_hash:
        errors.append("SHA-256 differs from acquisition metadata")

    crs = ""
    try:
        import rasterio

        with rasterio.open(path) as dataset:
            if dataset.count < 1 or dataset.width < 1 or dataset.height < 1:
                raise ValueError("Raster has no readable band or pixels")
            dataset.read(1, window=((0, 1), (0, 1)))
            crs = dataset.crs.to_string() if dataset.crs else ""
            if not crs:
                errors.append("Raster CRS is missing")
    except Exception as exc:
        errors.append(f"GeoTIFF read failed: {type(exc).__name__}: {exc}")

    return dict(
        status="failed" if errors else "success",
        file_size_bytes=size,
        crs=crs,
        sha256=checksum,
        error="; ".join(errors),
    )


def build_for_pass(
    atlantis_root: Path,
    catalogue_root: Path,
    selected: dict,
    layers: list[str],
    expected_bbox: list[float],
) -> dict:
    pass_id = selected["pass_id"]
    date = selected["catalogue_date"]
    date_root = catalogue_root / date
    acquisition_path = date_root / "metadata" / f"acquisition_{pass_id}.json"
    if not acquisition_path.is_file():
        raise FileNotFoundError(f"Acquisition manifest is missing: {acquisition_path}")
    acquisition = json.loads(acquisition_path.read_text())
    if acquisition.get("date") != date or acquisition.get("bbox") != expected_bbox:
        raise ValueError(f"Acquisition date or bbox does not match Step 2: {acquisition_path}")
    if acquisition.get("layers") != layers:
        raise ValueError(f"Acquisition layers do not match Step 3a selection: {acquisition_path}")
    if acquisition.get("pass_metadata", {}).get("pass_id") != pass_id:
        raise ValueError(f"Acquisition pass ID does not match selection: {acquisition_path}")

    catalogue_path = date_root / "metadata" / "stac_items.json"
    if not catalogue_path.is_file():
        raise FileNotFoundError(f"Cached STAC catalogue is missing: {catalogue_path}")
    catalogue = json.loads(catalogue_path.read_text())
    selected_items = []
    ungrouped_item_count = 0
    for feature in catalogue.get("features", []):
        try:
            feature_pass = parse_source(feature)["pass_id"]
        except (KeyError, ValueError):
            ungrouped_item_count += 1
            continue
        if feature_pass == pass_id:
            selected_items.append(feature)
    selected_items.sort(key=lambda item: item.get("id", ""))

    asset_records = acquisition.get("assets", {})
    acquired_items = {
        item.get("stac", {}).get("id", item.get("item_id", "")): item
        for item in acquisition.get("items", [])
    }
    validation = {}
    rows = []
    expected_keys = set()
    item_layer_references = 0
    mapped_references = 0

    for stac in selected_items:
        item_id = stac.get("id", "")
        bbox = json.dumps(stac.get("bbox"), separators=(",", ":")) if stac.get("bbox") else ""
        acquired_item = acquired_items.get(item_id, {})
        item_assets = acquired_item.get("assets", {})
        stac_assets = stac.get("assets", {})
        for layer in layers:
            item_layer_references += 1
            source_url = stac_assets.get(layer, {}).get("href", "")
            asset_key = hashlib.sha256(source_url.encode()).hexdigest()[:16] if source_url else ""
            asset = asset_records.get(asset_key, {}) if asset_key else {}
            mapping_ok = (
                bool(acquired_item)
                and item_assets.get(layer) == asset_key
                and asset.get("url") == source_url
            )
            if mapping_ok:
                mapped_references += 1
            if asset_key:
                expected_keys.add(asset_key)
                relative_asset = asset.get("path")
                name = Path(source_url.split("?", 1)[0]).name
                relative_asset = relative_asset or f"raw/{pass_id}/assets/{asset_key}_{name}"
            else:
                relative_asset = ""

            local_path = (date_root / relative_asset) if relative_asset else None
            cache_key = asset_key or f"{item_id}:{layer}"
            if cache_key not in validation:
                if local_path is None:
                    validation[cache_key] = dict(
                        status="missing", file_size_bytes="", crs="", sha256="",
                        error="No matching asset URL or acquisition record",
                    )
                else:
                    validation[cache_key] = inspect_asset(local_path, asset)
            check = validation[cache_key]
            status = check["status"]
            error = check["error"]
            if not mapping_ok:
                if status != "missing":
                    status = "failed"
                error = "; ".join(
                    filter(
                        None,
                        [error, "STAC Item/layer is not matched by the acquisition manifest"],
                    )
                )
            rows.append(
                dict(
                    pass_id=pass_id,
                    stac_item_id=item_id,
                    item_datetime_utc=stac.get("properties", {}).get("datetime", ""),
                    asset_layer=layer,
                    asset_key=asset_key,
                    source_url=source_url,
                    local_path=(
                        local_path.relative_to(atlantis_root).as_posix()
                        if local_path is not None
                        else ""
                    ),
                    status=status,
                    file_size_bytes=check["file_size_bytes"],
                    bbox=bbox,
                    crs=check["crs"] or asset.get("geometry", {}).get("crs", ""),
                    sha256=check["sha256"],
                    error=error,
                )
            )

    for asset_key, asset in asset_records.items():
        if asset_key in expected_keys:
            continue
        path = date_root / asset.get("path", "")
        check = inspect_asset(path, asset)
        check["status"] = "failed"
        check["error"] = "; ".join(
            filter(None, [check["error"], "Asset is not linked to a selected Item/layer"])
        )
        validation[asset_key] = check
        rows.append(
            dict(
                pass_id=pass_id,
                stac_item_id="",
                item_datetime_utc="",
                asset_layer="",
                asset_key=asset_key,
                source_url=asset.get("url", ""),
                local_path=(path.relative_to(atlantis_root).as_posix()),
                status=check["status"],
                file_size_bytes=check["file_size_bytes"],
                bbox="",
                crs=check["crs"] or asset.get("geometry", {}).get("crs", ""),
                sha256=check["sha256"],
                error=check["error"],
            )
        )

    item_count = len(selected_items)
    acquisition_item_count = len(acquisition.get("items", []))
    expected_item_count = selected.get("stac_item_count")
    acquisition_ids = set(acquired_items)
    selected_ids = {item.get("id", "") for item in selected_items}
    item_count_matches = (
        (expected_item_count is None or item_count == expected_item_count)
        and acquisition_ids == selected_ids
    )
    target_file_count = len(expected_keys)
    good_keys = {
        key
        for key in expected_keys
        if validation.get(key, {}).get("status") == "success"
        and key in asset_records
        and any(
            row["asset_key"] == key and row["status"] == "success"
            for row in rows
        )
    }
    missing_keys = sorted(
        key
        for key in expected_keys
        if validation.get(key, {}).get("status") == "missing"
    )
    failed_keys = sorted(
        key
        for key in expected_keys
        if validation.get(key, {}).get("status") == "failed"
        or any(row["asset_key"] == key and row["status"] == "failed" for row in rows)
    )
    unknown_missing = sum(1 for row in rows if row["status"] == "missing" and not row["asset_key"])
    unlinked_keys = sorted(set(asset_records) - expected_keys)
    asset_keys_match_selection = set(asset_records) == expected_keys
    summary = {
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "pass_id": pass_id,
        "catalogue_date": date,
        "selection_status": selected.get("status"),
        "layers": layers,
        "bbox_west_south_east_north": expected_bbox,
        "dataset_root": "Atlantis",
        "acquisition_manifest": acquisition_path.relative_to(atlantis_root).as_posix(),
        "manifest_path": "",
        "manifest_rows": len(rows),
        "expected_stac_item_count": expected_item_count,
        "selected_catalogue_item_count": item_count,
        "acquisition_stac_item_count": acquisition_item_count,
        "un_grouped_catalogue_item_count": ungrouped_item_count,
        "item_count_matches_selection": item_count_matches,
        "expected_item_layer_references": (
            expected_item_count * len(layers)
            if expected_item_count is not None
            else None
        ),
        "item_layer_references": item_layer_references,
        "mapped_item_layer_references": mapped_references,
        "asset_keys_match_selection": asset_keys_match_selection,
        "target_file_count": target_file_count,
        "verified_file_count": len(good_keys),
        "missing_file_count": len(missing_keys) + unknown_missing,
        "failed_file_count": len(failed_keys) + len(unlinked_keys),
        "total_verified_bytes": sum(
            validation[key].get("file_size_bytes", 0) for key in good_keys
        ),
        "missing_asset_keys": missing_keys,
        "failed_asset_keys": sorted(set(failed_keys) | set(unlinked_keys)),
        "ready_for_p03c": (
            item_count_matches
            and item_layer_references == mapped_references
            and item_layer_references
            == (
                expected_item_count * len(layers)
                if expected_item_count is not None
                else item_layer_references
            )
            and asset_keys_match_selection
            and all(row["status"] == "success" for row in rows)
            and len(good_keys) == target_file_count
            and not missing_keys
            and not failed_keys
            and unknown_missing == 0
        ),
    }

    metadata_dir = date_root / "metadata"
    manifest_path = metadata_dir / f"download_manifest_{pass_id}.csv"
    summary_path = metadata_dir / f"download_summary_{pass_id}.json"
    summary["manifest_path"] = manifest_path.relative_to(atlantis_root).as_posix()
    atomic_csv(manifest_path, rows)
    summary["manifest_sha256"] = digest(manifest_path)
    atomic_json(summary_path, summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Validate existing p03b COGs and write a p03c handover manifest."
    )
    parser.add_argument("--selection-json", type=Path, required=True)
    parser.add_argument("--catalogue-root", type=Path, required=True)
    parser.add_argument("--atlantis-root", type=Path, required=True)
    args = parser.parse_args()

    selection_path = args.selection_json.resolve()
    atlantis_root = args.atlantis_root.resolve()
    catalogue_root = args.catalogue_root.resolve()
    selection = json.loads(selection_path.read_text())
    domain_path = (selection_path.parent / selection["source_domain_config"]).resolve()
    domain = json.loads(domain_path.read_text())
    bbox = [
        float(value)
        for value in domain["satellite_analysis"]["domain"][
            "bbox_west_south_east_north"
        ]
    ]
    layers = selection["required_gfm_layers"]
    summaries = [
        build_for_pass(atlantis_root, catalogue_root, selected, layers, bbox)
        for selected in selection["passes"]
    ]
    for summary in summaries:
        print(
            f"{summary['pass_id']}: {summary['verified_file_count']}/"
            f"{summary['target_file_count']} files verified; "
            f"ready_for_p03c={str(summary['ready_for_p03c']).lower()}"
        )


if __name__ == "__main__":
    main()

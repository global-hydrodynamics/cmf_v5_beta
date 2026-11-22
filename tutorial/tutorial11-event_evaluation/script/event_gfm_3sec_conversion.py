#!/usr/bin/env python3
"""Mosaic one verified GFM pass on its native grid and derive a CaMa 3-second tile.

Only local complete COGs are read. Supports remain floating area fractions/m²;
raw class codes and integer-rounded Atlantis diagnostic counts are never averaged.
"""

from __future__ import annotations
import argparse
from collections import Counter
from contextlib import ExitStack
import hashlib
import json
import math
from pathlib import Path
import sys
import time
import numpy as np
import rasterio
from rasterio.transform import from_origin
from rasterio.warp import reproject, transform_bounds, Resampling
from rasterio.windows import Window
from pyproj import Geod

sys.path.insert(0, str(Path(__file__).resolve().parent))
from event_gfm_common import (
    LAYERS,
    NODATA,
    merge_observation,
    protect_old,
    run_metrics,
    save_json,
    sha256,
)

STEP = 1 / 1200
BANDS = [
    "flooded",
    "water",
    "valid",
    "observed",
    "excluded",
    "reference",
    "exclusion",
    "source_owner",
]


def profile(width, height, transform, crs, dtype="float32", nodata=NODATA, block=256):
    return dict(
        driver="GTiff",
        width=width,
        height=height,
        count=1,
        dtype=dtype,
        nodata=nodata,
        transform=transform,
        crs=crs,
        tiled=True,
        blockxsize=block,
        blockysize=block,
        compress="DEFLATE",
        predictor=3 if dtype.startswith("float") else 2,
    )


def windows(width, height, block):
    for row in range(0, height, block):
        for col in range(0, width, block):
            yield Window(col, row, min(block, width - col), min(block, height - row))


def cama_grid(map_dir, bbox):
    """Verify the nine-column CaMa location schema and the actual NetCDF centres."""
    location = Path(map_dir) / "1min_nc/location.txt"
    lines = location.read_text().splitlines()
    if lines[1].split() != [
        "iarea",
        "carea",
        "west",
        "east",
        "south",
        "north",
        "nx",
        "ny",
        "csize",
    ]:
        raise ValueError("Unexpected CaMa location schema")
    areas = [x.split() for x in lines[2:] if x.strip()]
    if len(areas) != int(lines[0].split()[0]):
        raise ValueError("CaMa location record count mismatch")
    w, s, e, n = bbox
    candidates = [
        a
        for a in areas
        if float(a[2]) <= w
        and float(a[3]) >= e
        and float(a[4]) <= s
        and float(a[5]) >= n
    ]
    if len(candidates) != 1:
        raise ValueError(
            "Choose an AOI contained in exactly one CaMa 1-minute file unit"
        )
    area = candidates[0]
    west, north, spacing = float(area[2]), float(area[5]), float(area[8])
    if not math.isclose(spacing, 1 / 60, rel_tol=0, abs_tol=1e-14):
        raise ValueError("Reference is not the requested one-minute grid")
    offsets = [
        (w - west) / spacing,
        (e - west) / spacing,
        (north - n) / spacing,
        (north - s) / spacing,
    ]
    if not all(abs(x - round(x)) < 1e-7 for x in offsets):
        raise ValueError("AOI edges do not coincide with full one-minute cell edges")
    col0, col1, row0, row1 = map(lambda x: int(round(x)), offsets)
    width, height = (col1 - col0) * 20, (row1 - row0) * 20
    target = from_origin(w, n, STEP, STEP)
    import netCDF4

    native_nc = location.parent / (area[1] + ".catmxy.nc")
    with netCDF4.Dataset(native_nc) as nc:
        lon = nc.variables["lon"][col0:col1]
        lat = nc.variables["lat"][row0:row1]
        sub_lon = w + (np.arange(width) + 0.5) * STEP
        sub_lat = n - (np.arange(height) + 0.5) * STEP
        # The stored decimal csize (.016666666666667) differs slightly from
        # exact 1/60. Bound its accumulated index error plus floating arithmetic;
        # do not silently tolerate a geometrically meaningful grid shift.
        lon_tol = (col1 + 1) * abs(spacing - 1 / 60) + 16 * np.finfo(
            lon.dtype
        ).eps * max(abs(west), abs(e), 1)
        lat_tol = (row1 + 1) * abs(spacing - 1 / 60) + 16 * np.finfo(
            lat.dtype
        ).eps * max(abs(north), abs(s), 1)
        lon_error = float(np.max(np.abs(sub_lon.reshape(-1, 20).mean(1) - lon)))
        lat_error = float(np.max(np.abs(sub_lat.reshape(-1, 20).mean(1) - lat)))
        if not np.allclose(sub_lon.reshape(-1, 20).mean(1), lon, rtol=0, atol=lon_tol):
            raise ValueError(
                "3-second longitude centres do not nest in the actual NetCDF grid"
            )
        if not np.allclose(sub_lat.reshape(-1, 20).mean(1), lat, rtol=0, atol=lat_tol):
            raise ValueError(
                "3-second latitude centres do not nest in the actual NetCDF grid"
            )
    return (
        target,
        width,
        height,
        dict(
            location_sha256=sha256(location),
            source_area=area,
            coarse_window=[col0, col1, row0, row1],
            subdivision=20,
            netcdf_centres_verified=True,
            centre_error_degrees=[lon_error, lat_error],
            centre_tolerance_degrees=[lon_tol, lat_tol],
        ),
    )


def native_window(src, window, canvas_transform):
    """Read the exact common-grid window; missing tile edges stay class 255."""
    dx = (canvas_transform.c - src.transform.c) / src.transform.a
    dy = (canvas_transform.f - src.transform.f) / src.transform.e
    if abs(dx - round(dx)) > 1e-6 or abs(dy - round(dy)) > 1e-6:
        raise ValueError(
            "Native grid offset is not integral (possible half-pixel shift)"
        )
    x, y = int(round(dx)) + int(window.col_off), int(round(dy)) + int(window.row_off)
    out = np.full((int(window.height), int(window.width)), 255, dtype="uint8")
    x0, y0 = max(0, x), max(0, y)
    x1, y1 = (
        min(src.width, x + int(window.width)),
        min(src.height, y + int(window.height)),
    )
    if x1 > x0 and y1 > y0:
        out[y0 - y : y1 - y, x0 - x : x1 - x] = src.read(
            1, window=Window(x0, y0, x1 - x0, y1 - y0)
        )
    return out


def native_mosaic(root, manifest, scratch, fingerprint, block, rebuild):
    path, info_path = scratch / "native_mosaic.tif", scratch / "native_mosaic.json"
    if path.exists() and info_path.exists() and not rebuild:
        info = json.loads(info_path.read_text())
        if info["fingerprint"] == fingerprint and sha256(path) == info["sha256"]:
            print("REUSE validated native mosaic", flush=True)
            return path, info, True
    scratch.mkdir(parents=True, exist_ok=True)
    with ExitStack() as stack:
        sources = {
            k: stack.enter_context(rasterio.open(root / a["path"]))
            for k, a in manifest["assets"].items()
        }
        first = next(iter(sources.values()))
        step = first.transform.a
        if abs(step - 20) > 1e-8 or abs(first.transform.e + 20) > 1e-8:
            raise ValueError("Expected original 20 m Equi7 pixel geometry")
        for src in sources.values():
            if (
                src.crs != first.crs
                or src.transform.a != step
                or src.transform.e != -step
                or src.transform.b
                or src.transform.d
            ):
                raise ValueError("Native assets do not share an axis-aligned 20 m grid")
            if src.nodata != 255 or src.dtypes[0] != "uint8":
                raise ValueError("Unexpected native GFM dtype/nodata")
        b = transform_bounds("EPSG:4326", first.crs, *manifest["bbox"], densify_pts=61)
        # A padded full rectangle supplies zero support outside SAR/tile coverage.
        # Thus average resampling does not renormalize away missing edge support.
        left = (
            first.transform.c
            + math.floor((b[0] - first.transform.c) / step) * step
            - 4 * step
        )
        right = (
            first.transform.c
            + math.ceil((b[2] - first.transform.c) / step) * step
            + 4 * step
        )
        bottom = (
            first.transform.f
            + math.floor((b[1] - first.transform.f) / step) * step
            - 4 * step
        )
        top = (
            first.transform.f
            + math.ceil((b[3] - first.transform.f) / step) * step
            + 4 * step
        )
        transform = from_origin(left, top, step, step)
        width, height = (
            int(round((right - left) / step)),
            int(round((top - bottom) / step)),
        )
        p = profile(width, height, transform, first.crs, "uint16", None, 512)
        p["count"] = 8
        temp = path.with_suffix(".partial.tif")
        stats = Counter()
        with rasterio.open(temp, "w", **p) as dst:
            for band, name in enumerate(BANDS, 1):
                dst.set_band_description(band, name)
            total = math.ceil(width / block) * math.ceil(height / block)
            for ordinal, win in enumerate(windows(width, height, block), 1):
                data = np.zeros((8, int(win.height), int(win.width)), dtype="uint16")
                data[5:7] = 255
                for item in manifest["items"]:
                    arrays = [
                        native_window(sources[item["assets"][name]], win, transform)
                        for name in LAYERS
                    ]
                    stats.update(merge_observation(data, *arrays, item["index"]))
                assert np.array_equal(data[2] > 0, data[7] > 0)
                assert np.all(data[0] <= data[2]) and np.all(data[1] <= data[2])
                assert np.all(data[2] + data[4] <= data[3])
                stats["unique_valid_native_pixels"] += int(data[2].sum())
                stats["flood_water_disagreement"] += int(
                    np.count_nonzero(data[0] > data[1])
                )
                dst.write(data, window=win)
                if ordinal == 1 or ordinal % 50 == 0 or ordinal == total:
                    print(
                        f"NATIVE blocks {ordinal}/{total}; unique valid={stats['unique_valid_native_pixels']:,}",
                        flush=True,
                    )
        temp.replace(path)
    info = dict(
        fingerprint=fingerprint,
        shape=[height, width],
        transform=list(transform),
        crs=first.crs.to_wkt(),
        bounds=[left, bottom, right, top],
        padding_native_pixels=4,
        sha256=sha256(path),
        statistics=dict(stats),
        statistics_scope="native padded rectangle, not geographic AOI area",
        priority="earliest common-valid Item; one owner per native pixel",
    )
    save_json(info_path, info)
    return path, info, False


def warp_band(
    native,
    band,
    path,
    grid,
    width,
    height,
    resampling,
    dtype="float32",
    source_nodata=None,
    dest_nodata=NODATA,
):
    with (
        rasterio.open(native) as src,
        rasterio.open(
            path, "w", **profile(width, height, grid, "EPSG:4326", dtype, dest_nodata)
        ) as dst,
    ):
        reproject(
            source=rasterio.band(src, band),
            destination=rasterio.band(dst, 1),
            src_nodata=source_nodata,
            dst_nodata=dest_nodata,
            resampling=resampling,
            num_threads=1,
            warp_mem_limit=64,
        )


def source_owners(native, items, scratch, out, grid, width, height):
    """Trace contributing Items with the SAME binary-area kernel as valid support.

    GDAL min/max and average use different edge footprints under reprojection.
    Warping categorical IDs directly can miss tiny valid edge contributions.
    Instead warp each native owner's binary support and record all positive
    contributors. The supports must sum back to the warped valid fraction.
    """
    indicator = scratch / "owner_indicator.tif"
    weight = scratch / "owner_weight.tif"
    closure = scratch / "owner_closure.tif"
    low = out / "rhine3sec.source_item_min.tif"
    high = out / "rhine3sec.source_item_max.tif"
    with ExitStack() as stack:
        readers = stack.enter_context(rasterio.open(native))
        lo = stack.enter_context(
            rasterio.open(
                low, "w+", **profile(width, height, grid, "EPSG:4326", "uint16", 0)
            )
        )
        hi = stack.enter_context(
            rasterio.open(
                high, "w+", **profile(width, height, grid, "EPSG:4326", "uint16", 0)
            )
        )
        total = stack.enter_context(
            rasterio.open(
                closure,
                "w+",
                **profile(width, height, grid, "EPSG:4326", "float32", None),
            )
        )
        for win in windows(width, height, 256):
            zero = np.zeros((int(win.height), int(win.width)), dtype="uint16")
            lo.write(zero, 1, window=win)
            hi.write(zero, 1, window=win)
            total.write(zero.astype("float32"), 1, window=win)
        for item in items:
            owner = item["index"]
            print(f"WARP source support {owner}/{len(items)}", flush=True)
            present = False
            with rasterio.open(
                indicator,
                "w",
                **profile(
                    readers.width,
                    readers.height,
                    readers.transform,
                    readers.crs,
                    "uint8",
                    None,
                    512,
                ),
            ) as mask:
                for win in windows(readers.width, readers.height, 512):
                    selected = (readers.read(8, window=win) == owner).astype("uint8")
                    present |= bool(selected.any())
                    mask.write(selected, 1, window=win)
            if not present:
                continue
            warp_band(indicator, 1, weight, grid, width, height, Resampling.average)
            with rasterio.open(weight) as weights:
                for win in windows(width, height, 256):
                    w = weights.read(1, window=win)
                    a, b = lo.read(1, window=win), hi.read(1, window=win)
                    use = w > 0
                    a[use & ((a == 0) | (owner < a))] = owner
                    b[use & (owner > b)] = owner
                    lo.write(a, 1, window=win)
                    hi.write(b, 1, window=win)
                    total.write(total.read(1, window=win) + w, 1, window=win)
        error = 0.0
        with rasterio.open(out / "rhine3sec.valid_fraction.tif") as valid:
            for win in windows(width, height, 256):
                v = valid.read(1, window=win)
                error = max(error, float(np.max(np.abs(v - total.read(1, window=win)))))
                if not np.array_equal(v > 0, lo.read(1, window=win) > 0):
                    raise ValueError(
                        "Contributing Item support does not match valid support"
                    )
        if error > 1e-6:
            raise ValueError(f"Item-support sum differs from valid support: {error}")
    return dict(
        method="per-owner binary area average; positive support contributors",
        support_sum_max_abs_error=error,
    )


def convert(args):
    started = time.monotonic()
    root = protect_old(
        args.input or args.work_dir / "data/Rhine_2021_3sec", args.work_dir
    )
    output_root = protect_old(args.output or root / "tiles_3sec", args.work_dir)
    scratch_root = protect_old(
        args.intermediate or root / "intermediate", args.work_dir
    )
    manifest_path = root / "metadata" / f"acquisition_{args.group}.json"
    manifest = json.loads(manifest_path.read_text())
    if (
        manifest["layers"] != list(LAYERS)
        or manifest["pass_metadata"]["pass_id"] != args.group
    ):
        raise ValueError("Input is not exactly the selected four-layer pass")
    for key, asset in manifest["assets"].items():
        path = root / asset["path"]
        if not path.resolve().is_relative_to(root.resolve()) or "://" in asset["path"]:
            raise ValueError(
                "Conversion accepts local paths inside the acquisition root only"
            )
        if (
            sha256(path) != asset.get("sha256")
            or path.stat().st_size != asset["expected_bytes"]
        ):
            raise ValueError(f"Incomplete/changed native input: {path}")
    print(
        f"Validated {len(manifest['assets'])} local COGs; no catalogue/download API is used",
        flush=True,
    )
    grid, width, height, alignment = cama_grid(args.cama_map, manifest["bbox"])
    sources = {
        k: dict(sha256=a["sha256"], path=a["path"])
        for k, a in manifest["assets"].items()
    }
    signature = dict(
        assets=sources,
        items=[
            dict(id=i["item_id"], index=i["index"], assets=i["assets"])
            for i in manifest["items"]
        ],
        bbox=manifest["bbox"],
        pass_id=args.group,
        code={
            n: sha256(Path(__file__).resolve().parent / n)
            for n in ["event_gfm_common.py", Path(__file__).name]
        },
    )
    fingerprint = hashlib.sha256(
        json.dumps(signature, sort_keys=True).encode()
    ).hexdigest()
    out = output_root / args.group
    scratch = scratch_root / args.group
    out.mkdir(parents=True, exist_ok=True)
    scratch.mkdir(parents=True, exist_ok=True)
    with rasterio.Env(
        GDAL_CACHEMAX=128 * 1024 * 1024, GDAL_PAM_ENABLED="NO", PROJ_NETWORK="OFF"
    ):
        native, native_info, reused = native_mosaic(
            root, manifest, scratch, fingerprint, args.block, args.rebuild_native
        )
        destinations = {}
        for name, band in [
            ("flood_area_fraction", 1),
            ("water_area_fraction", 2),
            ("valid_fraction", 3),
            ("observed_fraction", 4),
            ("excluded_fraction", 5),
        ]:
            path = (
                scratch if name.endswith("area_fraction") else out
            ) / f"rhine3sec.{name}.tif"
            print("WARP average", name, flush=True)
            warp_band(native, band, path, grid, width, height, Resampling.average)
            destinations[name] = path
        for name, band, method, dtype, nodata in [
            ("reference_water", 6, Resampling.mode, "uint8", 255),
            ("exclusion_mask", 7, Resampling.mode, "uint8", 255),
        ]:
            print("WARP categorical/owner", name, flush=True)
            path = out / f"rhine3sec.{name}.tif"
            warp_band(
                native, band, path, grid, width, height, method, dtype, nodata, nodata
            )
            destinations[name] = path
        owner_info = source_owners(
            native, manifest["items"], scratch, out, grid, width, height
        )
        names = [
            "flood_fraction",
            "water_fraction",
            "flooded_support",
            "water_support",
            "valid_support",
            "cell_area",
        ]
        stats = Counter()
        extrema = {n: [float("inf"), float("-inf")] for n in names + ["valid_fraction"]}
        geod = Geod(ellps="WGS84")
        w, s, e, n = manifest["bbox"]
        areas = np.array(
            [
                abs(
                    geod.polygon_area_perimeter(
                        [w, w + STEP, w + STEP, w],
                        [
                            n - r * STEP,
                            n - r * STEP,
                            n - (r + 1) * STEP,
                            n - (r + 1) * STEP,
                        ],
                    )[0]
                )
                for r in range(height)
            ],
            dtype="float64",
        )
        with ExitStack() as stack:
            arrays = {
                k: stack.enter_context(rasterio.open(destinations[k]))
                for k in [
                    "flood_area_fraction",
                    "water_area_fraction",
                    "valid_fraction",
                    "observed_fraction",
                    "excluded_fraction",
                ]
            }
            writers = {
                k: stack.enter_context(
                    rasterio.open(
                        out / f"rhine3sec.{k}.tif",
                        "w",
                        **profile(width, height, grid, "EPSG:4326"),
                    )
                )
                for k in names
            }
            for win in windows(width, height, 256):
                f, water, valid, observed, excluded = [
                    arrays[k].read(1, window=win) for k in arrays
                ]
                if not all(
                    np.all(np.isfinite(x) & (x >= 0) & (x <= 1 + 1e-6))
                    for x in [f, water, valid, observed, excluded]
                ):
                    raise ValueError(
                        "Support outside [0,1] or padded source did not fully cover target"
                    )
                if (
                    np.any(f > valid + 1e-6)
                    or np.any(water > valid + 1e-6)
                    or np.any(valid + excluded > observed + 1e-6)
                ):
                    raise ValueError("Inconsistent flooded/valid/observed support")
                good = valid > 0
                ff = np.divide(
                    f, valid, out=np.full(f.shape, NODATA, dtype="float32"), where=good
                )
                wf = np.divide(
                    water,
                    valid,
                    out=np.full(f.shape, NODATA, dtype="float32"),
                    where=good,
                )
                area = np.broadcast_to(
                    areas[int(win.row_off) : int(win.row_off + win.height), None],
                    f.shape,
                )
                values = dict(
                    flood_fraction=ff,
                    water_fraction=wf,
                    flooded_support=f * area,
                    water_support=water * area,
                    valid_support=valid * area,
                    cell_area=area,
                )
                for name, x in values.items():
                    writers[name].write(x.astype("float32"), 1, window=win)
                    finite = x[x != NODATA]
                    if finite.size:
                        extrema[name] = [
                            min(extrema[name][0], float(finite.min())),
                            max(extrema[name][1], float(finite.max())),
                        ]
                extrema["valid_fraction"] = [
                    min(extrema["valid_fraction"][0], float(valid.min())),
                    max(extrema["valid_fraction"][1], float(valid.max())),
                ]
                stats["cells"] += ff.size
                stats["some_valid_input"] += int(good.sum())
                stats["missing_fraction_cells"] += int((~good).sum())
                stats["positive_flood_cells"] += int(np.count_nonzero(good & (ff > 0)))
                stats["valid_support_m2"] += float((valid * area).sum())
                stats["flooded_support_m2"] += float((f * area).sum())
        for path in out.glob("rhine3sec.*.tif"):
            name = path.name[len("rhine3sec.") : -4]
            with rasterio.open(path, "r+") as dst:
                dst.set_band_description(1, name)
                dst.update_tags(
                    pass_id=args.group,
                    acquisition_start=manifest["pass_metadata"]["start_utc"],
                    acquisition_end=manifest["pass_metadata"]["end_utc"],
                    provenance="provenance.json",
                    units="m2"
                    if name.endswith("support") or name == "cell_area"
                    else "1",
                    validity="flood and water classified AND exclusion=0",
                    workflow_fingerprint=fingerprint,
                )
    (out / "location.txt").write_text(
        "     1     narea\n iarea     carea      west      east     south     north      nx      ny               csize\n"
        + f"     1 rhine3sec {w:.12f} {e:.12f} {s:.12f} {n:.12f} {width} {height} {STEP:.18f}\n"
    )
    provenance = dict(
        fingerprint=fingerprint,
        date=manifest["date"],
        bbox=manifest["bbox"],
        width=width,
        height=height,
        resolution=STEP,
        alignment=alignment,
        pass_metadata=manifest["pass_metadata"],
        source_items=[
            {k: v for k, v in i.items() if k != "stac"} for i in manifest["items"]
        ],
        source_assets=manifest["assets"],
        native_mosaic=str(native),
        native_statistics=native_info["statistics"],
        validity="FE in {0,1} AND OWE in {0,1} AND exclusion=0; reference not a validity source",
        overlap="earliest valid Item wins once on common native grid",
        area_method="GDAL binary-support overlap average; support times WGS84 target-cell area; local warp approximation",
        extrema=extrema,
        statistics=dict(stats),
        source_owner_validation=owner_info,
        output_files=[
            dict(name=p.name, bytes=p.stat().st_size, sha256=sha256(p))
            for p in sorted(out.glob("*.tif"))
        ],
    )
    save_json(out / "provenance.json", provenance)
    metrics = run_metrics(
        started,
        pass_id=args.group,
        native_reused=reused,
        block=args.block,
        output=str(out),
        output_bytes=sum(p.stat().st_size for p in out.glob("*") if p.is_file()),
        statistics=dict(stats),
    )
    logs = protect_old(args.work_dir / "logs", args.work_dir)
    save_json(logs / f"gfm_conversion_{output_root.name}_{args.group}.json", metrics)
    print(json.dumps(metrics, indent=2), flush=True)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--work-dir", type=Path, default=Path.home() / "work/Atlantis")
    p.add_argument("--input", type=Path)
    p.add_argument("--output", type=Path)
    p.add_argument("--intermediate", type=Path)
    p.add_argument("--group", required=True)
    p.add_argument(
        "--cama-map",
        type=Path,
        default=Path(__file__).resolve().parents[3] / "map/glb_15min",
    )
    p.add_argument("--block", type=int, choices=[128, 256, 512], default=512)
    p.add_argument("--rebuild-native", action="store_true")
    args = p.parse_args()
    convert(args)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Export one same-pass GFM observation as a compact native 20 m class COG."""
from __future__ import annotations

import argparse
from collections import Counter
from contextlib import ExitStack
import json
import math
from pathlib import Path
import tempfile
import time

import numpy as np
import rasterio
from rasterio.enums import Resampling
from rasterio.windows import Window, bounds as window_bounds, from_bounds
from rasterio.warp import transform_bounds
from rasterio.shutil import copy as raster_copy

from gfm_common import LAYERS, merge_observation, protect_old, save_json, sha256

GROUP = "S1A_o038784_dt049389"
DATE = "2021-07-15"
BLOCK = 512
CLASS_NAMES = {
    0: "Land",
    1: "Flood",
    2: "Permanent water",
    3: "Seasonal water",
    4: "Other water",
    5: "Exclusion",
    6: "Inconsistent",
    255: "NoData",
}
COLORS = {
    0: "#d9e5c7",
    1: "#e53935",
    2: "#174a7e",
    3: "#49a6cf",
    4: "#8764a8",
    5: "#5a5a5a",
    6: "#f39c12",
    255: "#eeeeee",
}


def native_window(src, window, canvas_transform):
    """Read a source window on the exact native 20 m grid; uncovered pixels=255."""
    dx = (canvas_transform.c - src.transform.c) / src.transform.a
    dy = (canvas_transform.f - src.transform.f) / src.transform.e
    if abs(dx - round(dx)) > 1e-6 or abs(dy - round(dy)) > 1e-6:
        raise ValueError("Native grid offset is not integral; pixel alignment differs")
    x = int(round(dx)) + int(window.col_off)
    y = int(round(dy)) + int(window.row_off)
    out = np.full((int(window.height), int(window.width)), 255, dtype="uint8")
    x0, y0 = max(0, x), max(0, y)
    x1 = min(src.width, x + int(window.width))
    y1 = min(src.height, y + int(window.height))
    if x1 > x0 and y1 > y0:
        out[y0-y:y1-y, x0-x:x1-x] = src.read(
            1, window=Window(x0, y0, x1-x0, y1-y0)
        )
    return out


def encode_classification(mosaic):
    """Map the existing eight-band mosaic state to mutually exclusive classes."""
    flooded, water, valid, observed, excluded, reference = mosaic[:6]
    out = np.full(valid.shape, 255, dtype="uint8")
    use = valid > 0
    out[use & (flooded == 0) & (water == 0)] = 0
    out[use & (flooded == 1) & (water == 1)] = 1
    observed_water = use & (flooded == 0) & (water == 1)
    out[observed_water & (reference == 1)] = 2
    out[observed_water & (reference == 2)] = 3
    out[observed_water & ~np.isin(reference, [1, 2])] = 4
    # Quality exclusion takes precedence only when no common-valid observation
    # was selected by merge_observation's earliest-valid-item rule.
    out[(valid == 0) & (excluded > 0)] = 5
    # Partial F/W classification or F=1,W=0 is retained as ambiguity, not dry.
    out[use & (flooded > water)] = 6
    out[(valid == 0) & (observed > 0) & (excluded == 0)] = 6
    return out


def count_combinations(counts, arrays):
    f, w, r, e = arrays
    present = (f != 255) | (w != 255) | (r != 255) | (e != 255)
    if not present.any():
        return
    # Four uint8 codes fit exactly in a uint32 key; avoid a 4-column sort.
    packed = ((f[present].astype("uint32") << 24)
              | (w[present].astype("uint32") << 16)
              | (r[present].astype("uint32") << 8)
              | e[present].astype("uint32"))
    unique, number = np.unique(packed, return_counts=True)
    for code, count in zip(unique, number):
        f_code, w_code = (int(code >> 24), int((code >> 16) & 255))
        r_code, e_code = (int((code >> 8) & 255), int(code & 255))
        key = f"flood={f_code},water={w_code},reference={r_code},exclusion={e_code}"
        counts[key] += int(count)


def grid_from_metadata(root, group, assets):
    info_path = root / "intermediate" / group / "native_mosaic.json"
    info = json.loads(info_path.read_text())
    height, width = map(int, info["shape"])
    transform_values = info["transform"]
    transform = rasterio.Affine(*transform_values[:6])
    with rasterio.open(next(iter(assets.values()))) as first:
        if first.crs is None or first.crs != rasterio.crs.CRS.from_wkt(info["crs"]):
            raise ValueError("Raw source CRS does not match native mosaic metadata")
        if first.transform.a != 20 or first.transform.e != -20:
            raise ValueError("Expected native 20 m source pixels")
        for src_path in assets.values():
            with rasterio.open(src_path) as src:
                if src.crs != first.crs or src.dtypes[0] != "uint8" or src.nodata != 255:
                    raise ValueError(f"Unexpected source raster contract: {src_path}")
                if src.transform.a != 20 or src.transform.e != -20:
                    raise ValueError(f"Unexpected source pixel size: {src_path}")
                dx = (transform.c - src.transform.c) / 20
                dy = (transform.f - src.transform.f) / -20
                if abs(dx - round(dx)) > 1e-6 or abs(dy - round(dy)) > 1e-6:
                    raise ValueError(f"Source is not aligned to saved native grid: {src_path}")
        bounds = rasterio.transform.array_bounds(height, width, transform)
        if not np.allclose(bounds, info["bounds"], rtol=0, atol=1e-7):
            raise ValueError("Saved native mosaic bounds and transform disagree")
        return height, width, transform, first.crs, info_path


def source_inventory(root, manifest):
    assets = {}
    records = []
    for asset_id, asset in manifest["assets"].items():
        path = (root / asset["path"]).resolve()
        if not path.is_relative_to(root.resolve()):
            raise ValueError(f"Source asset resolves outside acquisition root: {asset_id}")
        if not path.is_file() or path.stat().st_size != asset["expected_bytes"]:
            raise ValueError(f"Source asset missing or size changed: {path}")
        digest = sha256(path)
        if asset.get("sha256") and digest != asset["sha256"]:
            raise ValueError(f"Source asset checksum differs from acquisition manifest: {path}")
        assets[asset_id] = path
        records.append({"asset_id": asset_id, "relative_path": asset["path"],
                        "bytes": path.stat().st_size, "sha256": digest})
    if len(assets) != 37:
        raise ValueError(f"Expected 37 local source COGs, found {len(assets)}")
    return assets, records


def render_figure(path, figure_path, title, bounds=None, max_size=1800):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.colors import ListedColormap, BoundaryNorm
    from matplotlib.patches import Patch

    palette = [COLORS[i] for i in [0, 1, 2, 3, 4, 5, 6, 255]]
    cmap = ListedColormap(palette)
    norm = BoundaryNorm([-0.5, 0.5, 1.5, 2.5, 3.5, 4.5, 5.5, 6.5, 255.5], cmap.N)
    with rasterio.open(path) as src:
        if bounds:
            projected = transform_bounds("EPSG:4326", src.crs, *bounds, densify_pts=21)
            win = from_bounds(*projected, transform=src.transform).round_offsets().round_lengths()
            win = win.intersection(Window(0, 0, src.width, src.height))
        else:
            win = Window(0, 0, src.width, src.height)
        scale = min(1.0, max_size / max(int(win.width), int(win.height)))
        shape = (max(1, round(win.height * scale)), max(1, round(win.width * scale)))
        data = src.read(1, window=win, out_shape=shape, resampling=Resampling.nearest)
        extent = window_bounds(win, src.transform)
    fig, ax = plt.subplots(figsize=(11, 10), constrained_layout=True)
    ax.set_facecolor(COLORS[255])
    ax.imshow(data, extent=(extent[0]/1000, extent[2]/1000, extent[1]/1000, extent[3]/1000),
              cmap=cmap, norm=norm, interpolation="nearest", origin="upper")
    ax.set_title(title)
    ax.set_xlabel("Equi7 Europe easting [km]")
    ax.set_ylabel("Equi7 Europe northing [km]")
    labels = ["Land", "Flood", "Permanent water", "Seasonal water", "Other water", "Exclusion", "Inconsistent", "NoData"]
    handles = [Patch(facecolor=COLORS[i], edgecolor="black", linewidth=0.25, label=label)
               for i, label in zip([0,1,2,3,4,5,6,255], labels)]
    ax.legend(handles=handles, loc="lower right", framealpha=0.95, fontsize=8)
    figure_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(figure_path, dpi=160)
    plt.close(fig)


def export(args):
    started = time.monotonic()
    root = Path(args.input_root).resolve()
    group = args.group
    if group != GROUP:
        raise ValueError(f"This scoped exporter only accepts {GROUP}")
    manifest_path = root / "metadata" / f"acquisition_{group}.json"
    manifest = json.loads(manifest_path.read_text())
    if manifest["layers"] != list(LAYERS) or manifest["pass_metadata"]["pass_id"] != group:
        raise ValueError("Manifest does not describe the requested four-layer pass")
    assets, asset_records = source_inventory(root, manifest)
    height, width, transform, crs, mosaic_metadata_path = grid_from_metadata(root, group, assets)
    out_dir = Path(args.output_dir).resolve() if args.output_dir else root / "tiles_20m" / group
    protect_old(out_dir, root)
    tif = out_dir / f"gfm_{DATE.replace('-', '')}_20m_class.tif"
    report_path = out_dir / "classification.json"
    if not args.force and (tif.exists() or report_path.exists()):
        raise FileExistsError(f"Output exists; pass --force to replace: {out_dir}")
    out_dir.mkdir(parents=True, exist_ok=True)

    counts = Counter()
    combos = Counter()
    mosaic_stats = Counter()
    tile_order = manifest["items"]
    profile = dict(driver="GTiff", width=width, height=height, count=1, dtype="uint8",
                   nodata=255, crs=crs, transform=transform, tiled=True,
                   blockxsize=512, blockysize=512, compress="DEFLATE", predictor=1)
    with tempfile.TemporaryDirectory(prefix="cmf_gfm20m_") as temp_dir:
        temp_tif = Path(temp_dir) / "classification_work.tif"
        with ExitStack() as stack:
            sources = {k: stack.enter_context(rasterio.open(v)) for k, v in assets.items()}
            with rasterio.open(temp_tif, "w", **profile) as dst:
                total = math.ceil(width / BLOCK) * math.ceil(height / BLOCK)
                ordinal = 0
                for y in range(0, height, BLOCK):
                    for x in range(0, width, BLOCK):
                        ordinal += 1
                        win = Window(x, y, min(BLOCK, width-x), min(BLOCK, height-y))
                        mosaic = np.zeros((8, int(win.height), int(win.width)), dtype="uint16")
                        mosaic[5:7] = 255
                        for item in tile_order:
                            arrays = [native_window(sources[item["assets"][name]], win, transform)
                                      for name in LAYERS]
                            count_combinations(combos, arrays)
                            mosaic_stats.update(merge_observation(mosaic, *arrays, item["index"]))
                        mosaic_stats["selected_valid_pixels"] += int((mosaic[2] > 0).sum())
                        mosaic_stats["selected_flood_pixels"] += int(
                            np.count_nonzero((mosaic[2] > 0) & (mosaic[0] == 1))
                        )
                        mosaic_stats["selected_water_pixels"] += int(
                            np.count_nonzero((mosaic[2] > 0) & (mosaic[1] == 1))
                        )
                        mosaic_stats["selected_exclusion_pixels"] += int(
                            np.count_nonzero((mosaic[2] == 0) & (mosaic[4] > 0))
                        )
                        mosaic_stats["selected_partial_pixels"] += int(
                            np.count_nonzero((mosaic[2] == 0) & (mosaic[3] > 0) & (mosaic[4] == 0))
                        )
                        mosaic_stats["selected_reference_only_pixels"] += int(
                            np.count_nonzero((mosaic[2] == 0) & (mosaic[3] == 0) & (mosaic[5] != 255))
                        )
                        mosaic_stats["selected_direct_flood_water_conflict"] += int(
                            np.count_nonzero((mosaic[2] > 0) & (mosaic[0] == 1) & (mosaic[1] == 0))
                        )
                        classified = encode_classification(mosaic)
                        allowed = np.isin(classified, [0,1,2,3,4,5,6,255])
                        if not allowed.all():
                            raise ValueError("Classification produced an undefined code")
                        values, number = np.unique(classified, return_counts=True)
                        counts.update({int(k): int(v) for k, v in zip(values, number)})
                        dst.write(classified, 1, window=win)
                        if ordinal == 1 or ordinal % 50 == 0 or ordinal == total:
                            print(f"CLASSIFY blocks {ordinal}/{total}", flush=True)
        # COG conversion uses lossless ZSTD; categorical overviews use nearest.
        temp_cog = Path(temp_dir) / "classification_cog.tif"
        raster_copy(temp_tif, temp_cog, driver="COG", compress="ZSTD", blocksize=512,
                    predictor=1, overview_resampling="NEAREST")
        compression = "ZSTD"
        # Read the completed COG before replacing the requested output.
        check_counts = Counter()
        with rasterio.open(temp_tif) as source, rasterio.open(temp_cog) as result:
            if (result.count != 1 or result.dtypes != ("uint8",) or result.nodata != 255
                    or result.width != width or result.height != height
                    or result.crs != crs or result.transform != transform):
                raise ValueError("Output COG contract differs from the native 20 m grid")
            for y in range(0, height, BLOCK):
                win = Window(0, y, width, min(BLOCK, height-y))
                actual = result.read(1, window=win)
                expected = source.read(1, window=win)
                if not np.array_equal(actual, expected):
                    raise ValueError(f"Decoded COG values changed at row {y}")
                values, number = np.unique(actual, return_counts=True)
                check_counts.update({int(k): int(v) for k, v in zip(values, number)})
        if check_counts != counts:
            raise ValueError("Output COG class counts differ from classified input")
        temp_cog.replace(tif)

    # Flood area is compared on the selected common-valid mosaic, before class priority.
    flood_pixels = counts.get(1, 0)
    selected_flood_pixels = mosaic_stats.get("selected_flood_pixels", 0)
    planar_pixel_area_m2 = 400.0
    class_count_total = sum(counts.values())
    if class_count_total != width * height:
        raise ValueError("Class count does not cover the complete native mosaic rectangle")
    with rasterio.open(tif) as result:
        image_structure = result.tags(ns="IMAGE_STRUCTURE")
        grid_info = {"width": width, "height": height, "crs_wkt": result.crs.to_wkt(),
                     "transform": list(result.transform), "bounds": list(result.bounds),
                     "pixel_size_m": [result.transform.a, abs(result.transform.e)],
                     "nodata": result.nodata, "dtype": result.dtypes[0],
                     "image_structure": image_structure}
    output_bytes = tif.stat().st_size
    report = {
        "schema": "cmf-v5-gfm-native-classification-1",
        "date": DATE,
        "pass_id": group,
        "acquisition_interval_utc": manifest["pass_metadata"],
        "input_manifest": manifest_path.name,
        "native_mosaic_metadata": str(mosaic_metadata_path.relative_to(root)),
        "native_mosaic_raster_available": (root / "intermediate" / group / "native_mosaic.tif").exists(),
        "source_assets": asset_records,
        "source_combination_counts": dict(sorted(combos.items())),
        "mosaic_selection_statistics": dict(mosaic_stats),
        "class_codes": {str(code): {"name": name, "meaning": meaning}
                         for code, name, meaning in [
                             (0,"Land","F=0 and W=0 in selected common-valid observation"),
                             (1,"Flood","F=1 and W=1 in selected common-valid observation"),
                             (2,"Permanent water","F=0,W=1 and reference=1"),
                             (3,"Seasonal water","F=0,W=1 and reference=2"),
                             (4,"Other water","F=0,W=1 and reference is 0 or 255"),
                             (5,"Exclusion","no common-valid observation; selected mosaic marks excluded area"),
                             (6,"Inconsistent","valid F=1,W=0 or observed partial F/W classification"),
                             (255,"NoData","no valid, excluded, or partial F/W observation")
                         ]},
        "priority": ["existing merge_observation order: earliest joint-valid observation with exclusion=0",
                     "when no joint-valid observation exists, Exclusion precedes partial-class Inconsistent",
                     "reference water refines only an observed W=1 class; reference-only pixels remain NoData"],
        "class_pixel_counts": {str(k): counts.get(k, 0) for k in CLASS_NAMES},
        "grid": grid_info,
        "output": {"file": tif.name, "bytes": output_bytes,
                   "sha256": sha256(tif), "compression": compression,
                   "format": "single-band lossless COG"},
        "area_note": "Planar 20 m pixel area is 400 m2 in Equi7 coordinates; this is projected area, not ellipsoidal geodesic area.",
        "flood_area_comparison": {
            "selected_source_flood_pixels": selected_flood_pixels,
            "class_flood_pixels": flood_pixels,
            "source_flood_area_projected_km2": selected_flood_pixels * planar_pixel_area_m2 / 1e6,
            "class_flood_area_projected_km2": flood_pixels * planar_pixel_area_m2 / 1e6,
            "difference_km2": (flood_pixels-selected_flood_pixels) * planar_pixel_area_m2 / 1e6,
        },
        "software": {"rasterio": rasterio.__version__, "gdal": rasterio.__gdal_version__},
        "runtime_seconds": time.monotonic() - started,
        "license_note": "Source is Copernicus EMS Global Flood Monitoring. Consult the applicable CEMS/GFM terms and provide required attribution before redistribution; dataset-specific redistribution clearance for this derived file remains to be confirmed.",
    }
    save_json(report_path, report)
    if args.figure:
        render_figure(tif, Path(args.figure).resolve(),
                      "GFM 20 m native classification — 15 July 2021, S1A morning pass")
    print(json.dumps({"output": str(tif), "bytes": output_bytes,
                      "class_pixel_counts": report["class_pixel_counts"],
                      "sha256": report["output"]["sha256"]}, indent=2))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-root", type=Path,
                        default=Path.home() / "work/Atlantis/data/Rhine_2021_3sec")
    parser.add_argument("--group", default=GROUP)
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--figure", type=Path,
                        default=Path(__file__).resolve().parents[1] / "figure/gfm_20210715_20m_class.png")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    export(args)


if __name__ == "__main__":
    main()

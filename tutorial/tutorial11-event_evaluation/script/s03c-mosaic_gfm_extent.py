#!/usr/bin/env python3
"""Classify and mosaic one selected GFM pass on its native 20 m grid."""

from __future__ import annotations

import argparse
from collections import Counter
from contextlib import ExitStack
from datetime import datetime
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import sys
import tempfile
import time

import numpy as np
import rasterio
from rasterio import Affine
from rasterio.windows import Window
from rasterio.shutil import copy as raster_copy
from rasterio.warp import transform_bounds

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))
from gfm_common import LAYERS, merge_observation, save_json, sha256


CLASSIFIER_PATH = SCRIPT_DIR / "s04-export_gfm_20m_class.py"
CLASSIFIER_SPEC = importlib.util.spec_from_file_location(
    "gfm_20m_classification", CLASSIFIER_PATH
)
CLASSIFIER = importlib.util.module_from_spec(CLASSIFIER_SPEC)
CLASSIFIER_SPEC.loader.exec_module(CLASSIFIER)

BLOCK = 512
CLASS_MEANINGS = {
    0: "F=0 and W=0 in selected common-valid observation",
    1: "F=1 and W=1 in selected common-valid observation",
    2: "F=0,W=1 and reference=1",
    3: "F=0,W=1 and reference=2",
    4: "F=0,W=1 and reference is 0 or 255",
    5: "No common-valid observation; the selected mosaic marks exclusion",
    6: "Valid F=1,W=0 or observed partial F/W classification",
    255: "No flood/water observation; includes reference-only coverage",
}


def checked_path(root: Path, relative: str) -> Path:
    path = (root / relative).resolve()
    if not path.is_relative_to(root.resolve()):
        raise ValueError(f"Manifest path resolves outside {root}: {relative}")
    return path


def utc_datetime(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError(f"STAC Item datetime must include a timezone: {value}")
    return parsed


def read_pass_inputs(
    tutorial_root: Path,
    atlantis_root: Path,
    selected: dict,
    layers: list[str],
) -> tuple[Path, dict, dict, list[dict], dict]:
    pass_id = selected["pass_id"]
    date = selected["catalogue_date"]
    summary_path = atlantis_root / "catalogue" / date / "metadata" / f"download_summary_{pass_id}.json"
    if not summary_path.is_file():
        raise FileNotFoundError(f"p03b Summary is missing: {summary_path}")
    summary = json.loads(summary_path.read_text())
    if summary.get("pass_id") != pass_id or summary.get("catalogue_date") != date:
        raise ValueError(f"p03b Summary does not match selected pass: {summary_path}")
    if summary.get("layers") != layers:
        raise ValueError("p03b Summary layers do not match the Step 3a selection")
    if not summary.get("ready_for_p03c", False):
        raise ValueError(
            "p03b Summary reports files are not ready for p03c: "
            f"missing={summary.get('missing_asset_keys', [])}, "
            f"failed={summary.get('failed_asset_keys', [])}"
        )

    dataset_root = checked_path(tutorial_root, summary["dataset_root"])
    manifest_path = checked_path(dataset_root, summary["manifest_path"])
    if not manifest_path.is_file():
        raise FileNotFoundError(f"p03b Manifest is missing: {manifest_path}")
    expected_manifest_hash = summary.get("manifest_sha256")
    if expected_manifest_hash and sha256(manifest_path) != expected_manifest_hash:
        raise ValueError(f"p03b Manifest checksum differs from Summary: {manifest_path}")

    import csv

    with manifest_path.open(newline="") as stream:
        rows = list(csv.DictReader(stream))
    if not rows:
        raise ValueError(f"p03b Manifest has no item/layer rows: {manifest_path}")
    if any(row.get("status") != "success" for row in rows):
        failures = [
            f"{row.get('stac_item_id')}:{row.get('asset_layer')}={row.get('status')}"
            for row in rows
            if row.get("status") != "success"
        ]
        raise ValueError("p03b Manifest contains non-success rows: " + ", ".join(failures[:12]))

    assets: dict[str, dict] = {}
    items: dict[str, dict] = {}
    for row in rows:
        item_id = row["stac_item_id"]
        layer = row["asset_layer"]
        if layer not in layers:
            raise ValueError(f"Unexpected layer in p03b Manifest: {layer}")
        when = utc_datetime(row["item_datetime_utc"])
        path = checked_path(dataset_root, row["local_path"])
        if not path.is_file():
            raise FileNotFoundError(f"Manifest input is missing: {path}")
        key = row["asset_key"]
        asset = dict(
            path=path,
            relative_path=row["local_path"],
            url=row["source_url"],
            bytes=int(row["file_size_bytes"]),
            sha256=row["sha256"],
        )
        if key in assets and assets[key] != asset:
            raise ValueError(f"Conflicting Manifest records for asset {key}")
        assets[key] = asset

        item = items.setdefault(item_id, {"datetime": when, "assets": {}})
        if item["datetime"] != when:
            raise ValueError(f"Inconsistent Item datetime across layers: {item_id}")
        if layer in item["assets"] and item["assets"][layer] != key:
            raise ValueError(f"Duplicate conflicting layer rows for {item_id}:{layer}")
        item["assets"][layer] = key

    for item_id, item in items.items():
        if set(item["assets"]) != set(layers):
            raise ValueError(f"Item does not have exactly the selected layers: {item_id}")
    if len(assets) != summary.get("target_file_count"):
        raise ValueError("Manifest unique file count differs from p03b Summary")
    if len(items) != summary.get("selected_catalogue_item_count"):
        raise ValueError("Manifest Item count differs from p03b Summary")

    ordered_items = [
        {"item_id": item_id, **value}
        for item_id, value in sorted(
            items.items(), key=lambda pair: (pair[1]["datetime"], pair[0])
        )
    ]
    return manifest_path, summary, assets, ordered_items, dataset_root


def validate_sources(assets: dict[str, dict]) -> tuple[dict, rasterio.crs.CRS]:
    grids = {}
    reference_crs = None
    for key, asset in assets.items():
        path = asset["path"]
        if path.stat().st_size != asset["bytes"]:
            raise ValueError(f"Input file size differs from p03b Manifest: {path}")
        if sha256(path) != asset["sha256"]:
            raise ValueError(f"Input checksum differs from p03b Manifest: {path}")
        with rasterio.open(path) as src:
            if src.count != 1 or src.dtypes != ("uint8",) or src.nodata != 255:
                raise ValueError(f"Unexpected GFM source type/bands/NoData: {path}")
            if src.crs is None:
                raise ValueError(f"GFM source has no CRS: {path}")
            if reference_crs is None:
                reference_crs = src.crs
            elif src.crs != reference_crs:
                raise ValueError(f"GFM source CRS differs: {path}")
            transform = src.transform
            if (
                transform.a != 20.0
                or transform.e != -20.0
                or transform.b != 0.0
                or transform.d != 0.0
            ):
                raise ValueError(f"GFM source is not north-up native 20 m: {path}")
            grids[key] = dict(
                width=src.width,
                height=src.height,
                transform=transform,
                crs=src.crs,
            )
    if reference_crs is None:
        raise ValueError("No GFM source assets were found in the Manifest")

    origin_x = min(grid["transform"].c for grid in grids.values())
    origin_y = max(grid["transform"].f for grid in grids.values())
    for key, grid in grids.items():
        transform = grid["transform"]
        col = (transform.c - origin_x) / 20.0
        row = (origin_y - transform.f) / 20.0
        if abs(col - round(col)) > 1e-6 or abs(row - round(row)) > 1e-6:
            raise ValueError(f"Source COG pixel alignment differs: asset {key}")
        grid["col"] = int(round(col))
        grid["row"] = int(round(row))

    width = max(grid["col"] + grid["width"] for grid in grids.values())
    height = max(grid["row"] + grid["height"] for grid in grids.values())
    transform = Affine(20.0, 0.0, origin_x, 0.0, -20.0, origin_y)
    return dict(width=width, height=height, transform=transform, assets=grids), reference_crs


def aligned_aoi_grid(source_grid: dict, crs: rasterio.crs.CRS, bbox: list[float]):
    """Project the WGS84 AOI envelope and align its smallest covering grid."""
    if len(bbox) != 4 or not all(math.isfinite(float(value)) for value in bbox):
        raise ValueError("Satellite analysis bbox must contain four finite WGS84 values")
    west, south, east, north = map(float, bbox)
    if west >= east or south >= north:
        raise ValueError(f"Invalid west/south/east/north AOI bounds: {bbox}")

    projected_bounds = transform_bounds(
        "EPSG:4326", crs, west, south, east, north, densify_pts=101
    )
    if not all(math.isfinite(value) for value in projected_bounds):
        raise ValueError("WGS84 satellite analysis bbox did not project to finite bounds")

    source_transform = source_grid["transform"]
    resolution = source_transform.a
    col_start = math.floor((projected_bounds[0] - source_transform.c) / resolution)
    col_stop = math.ceil((projected_bounds[2] - source_transform.c) / resolution)
    row_start = math.floor((source_transform.f - projected_bounds[3]) / resolution)
    row_stop = math.ceil((source_transform.f - projected_bounds[1]) / resolution)
    width = col_stop - col_start
    height = row_stop - row_start
    if width <= 0 or height <= 0:
        raise ValueError("Projected satellite analysis bbox has no native-grid pixels")

    return (
        dict(
            width=width,
            height=height,
            col_off=col_start,
            row_off=row_start,
            transform=source_transform * Affine.translation(col_start, row_start),
        ),
        tuple(projected_bounds),
    )


def mosaic_pass(
    tutorial_root: Path,
    atlantis_root: Path,
    selected: dict,
    aoi_bbox: list[float],
    manifest_path: Path,
    summary: dict,
    assets: dict[str, dict],
    items: list[dict],
    dataset_root: Path,
    output_dir: Path,
    figure_dir: Path,
    force: bool,
) -> dict:
    source_grid, crs = validate_sources(assets)
    grid, projected_aoi = aligned_aoi_grid(source_grid, crs, aoi_bbox)
    width, height, transform = grid["width"], grid["height"], grid["transform"]
    satellite = selected["satellite"]
    pass_id = selected["pass_id"]
    date = selected["catalogue_date"]
    stem = f"GFM_{satellite}_{date.replace('-', '')}_{pass_id.split('_', 1)[1]}_extent20m"
    output_path = output_dir / f"{stem}.tif"
    metadata_path = output_dir / f"{stem}.json"
    if not force and (output_path.exists() or metadata_path.exists()):
        raise FileExistsError(
            f"p03c output exists; pass --force to replace: {output_path}"
        )
    output_dir.mkdir(parents=True, exist_ok=True)
    figure_dir.mkdir(parents=True, exist_ok=True)

    started = time.monotonic()
    class_counts = Counter()
    mosaic_stats = Counter()
    profile = dict(
        driver="GTiff",
        width=width,
        height=height,
        count=1,
        dtype="uint8",
        nodata=255,
        crs=crs,
        transform=transform,
        tiled=True,
        blockxsize=512,
        blockysize=512,
        compress="DEFLATE",
        predictor=1,
    )

    with tempfile.TemporaryDirectory(prefix="cmf_gfm_p03c_") as temp_dir:
        temp_dir = Path(temp_dir)
        temporary_tif = temp_dir / "classification_work.tif"
        with ExitStack() as stack:
            readers = {
                key: stack.enter_context(rasterio.open(asset["path"]))
                for key, asset in assets.items()
            }
            with rasterio.open(temporary_tif, "w", **profile) as dst:
                total = math.ceil(width / BLOCK) * math.ceil(height / BLOCK)
                ordinal = 0
                for y in range(0, height, BLOCK):
                    for x in range(0, width, BLOCK):
                        ordinal += 1
                        window = Window(
                            x,
                            y,
                            min(BLOCK, width - x),
                            min(BLOCK, height - y),
                        )
                        block = np.zeros(
                            (8, int(window.height), int(window.width)),
                            dtype="uint16",
                        )
                        block[5:7] = 255
                        for index, item in enumerate(items, start=1):
                            arrays = [
                                CLASSIFIER.native_window(
                                    readers[item["assets"][layer]],
                                    window,
                                    transform,
                                )
                                for layer in LAYERS
                            ]
                            mosaic_stats.update(
                                merge_observation(block, *arrays, index)
                            )
                        mosaic_stats["selected_valid_pixels"] += int(
                            (block[2] > 0).sum()
                        )
                        mosaic_stats["selected_flood_pixels"] += int(
                            np.count_nonzero((block[2] > 0) & (block[0] == 1))
                        )
                        mosaic_stats["selected_water_pixels"] += int(
                            np.count_nonzero((block[2] > 0) & (block[1] == 1))
                        )
                        mosaic_stats["selected_exclusion_pixels"] += int(
                            np.count_nonzero((block[2] == 0) & (block[4] > 0))
                        )
                        mosaic_stats["selected_partial_pixels"] += int(
                            np.count_nonzero(
                                (block[2] == 0) & (block[3] > 0) & (block[4] == 0)
                            )
                        )
                        mosaic_stats["selected_reference_only_pixels"] += int(
                            np.count_nonzero(
                                (block[2] == 0) & (block[3] == 0) & (block[5] != 255)
                            )
                        )
                        classified = CLASSIFIER.encode_classification(block)
                        allowed = np.isin(classified, list(CLASSIFIER.CLASS_NAMES))
                        if not allowed.all():
                            raise ValueError("Classification produced an undefined code")
                        values, counts = np.unique(classified, return_counts=True)
                        class_counts.update(
                            {int(code): int(count) for code, count in zip(values, counts)}
                        )
                        dst.write(classified, 1, window=window)
                        if ordinal == 1 or ordinal % 100 == 0 or ordinal == total:
                            print(f"CLASSIFY blocks {ordinal}/{total}", flush=True)

        temporary_cog = temp_dir / "classification_cog.tif"
        raster_copy(
            temporary_tif,
            temporary_cog,
            driver="COG",
            compress="ZSTD",
            blocksize=512,
            predictor=1,
            overview_resampling="NEAREST",
        )
        with rasterio.open(temporary_tif) as source, rasterio.open(temporary_cog) as result:
            if (
                result.count != 1
                or result.dtypes != ("uint8",)
                or result.nodata != 255
                or result.width != width
                or result.height != height
                or result.crs != crs
                or result.transform != transform
                or result.transform.a != 20.0
                or result.transform.e != -20.0
            ):
                raise ValueError("Output COG contract differs from the native 20 m grid")
            checked_counts = Counter()
            for y in range(0, height, BLOCK):
                window = Window(0, y, width, min(BLOCK, height - y))
                expected = source.read(1, window=window)
                actual = result.read(1, window=window)
                if not np.array_equal(actual, expected):
                    raise ValueError(f"Decoded COG values changed at row {y}")
                values, counts = np.unique(actual, return_counts=True)
                checked_counts.update(
                    {int(code): int(count) for code, count in zip(values, counts)}
                )
            if checked_counts != class_counts:
                raise ValueError("Decoded COG class counts differ from generated pixels")

        temporary_cog.replace(output_path)

    figure_path = figure_dir / f"{stem}_inspection.png"
    CLASSIFIER.render_figure(
        output_path,
        figure_path,
        f"GFM native 20 m classification — {date}, {pass_id}",
    )
    with rasterio.open(output_path) as output:
        image_structure = output.tags(ns="IMAGE_STRUCTURE")
        grid_metadata = {
            "width": width,
            "height": height,
            "dimensions": [width, height],
            "crs_wkt": output.crs.to_wkt(),
            "transform": list(output.transform),
            "bounds": list(output.bounds),
            "pixel_size_m": [output.transform.a, abs(output.transform.e)],
            "dtype": output.dtypes[0],
            "count": output.count,
            "nodata": output.nodata,
            "image_structure": image_structure,
        }
    file_bytes = output_path.stat().st_size
    raw_bytes = width * height
    metadata = {
        "schema": "cmf-tutorial11-gfm-native-classification-1",
        "pass_id": pass_id,
        "satellite": satellite,
        "date": date,
        "orbit_direction": selected.get("orbit_direction"),
        "selection_status": selected.get("status"),
        "input_manifest": str(manifest_path.relative_to(tutorial_root)),
        "input_manifest_sha256": sha256(manifest_path),
        "aoi_wgs84_bbox_west_south_east_north": list(map(float, aoi_bbox)),
        "aoi_projected_bounds": list(projected_aoi),
        "aoi_projected_crs": crs.to_string(),
        "input_summary": str(
            (summary_path := atlantis_root / "catalogue" / date / "metadata"
             / f"download_summary_{pass_id}.json").relative_to(tutorial_root)
        ),
        "input_summary_sha256": sha256(summary_path),
        "dataset_root_relative_to_tutorial": str(dataset_root.relative_to(tutorial_root)),
        "input_item_count": len(items),
        "input_unique_cog_count": len(assets),
        "input_layers": LAYERS,
        "item_processing_order": [
            {"stac_item_id": item["item_id"], "datetime_utc": item["datetime"].isoformat()}
            for item in items
        ],
        "source_files": [
            {
                "asset_key": key,
                "local_path": asset["relative_path"],
                "file_size_bytes": asset["bytes"],
                "sha256": asset["sha256"],
            }
            for key, asset in sorted(assets.items())
        ],
        "source_class_codes": {
            "ensemble_flood_extent": {"0": "not flooded", "1": "flooded", "255": "NoData"},
            "ensemble_water_extent": {"0": "not water", "1": "water", "255": "NoData"},
            "reference_water_mask": {"0": "not reference water", "1": "permanent", "2": "seasonal", "255": "NoData"},
            "exclusion_mask": {"0": "not excluded", "1": "excluded", "255": "NoData"},
        },
        "classification_codes": {
            str(code): {
                "class": CLASSIFIER.CLASS_NAMES[code],
                "meaning": CLASS_MEANINGS[code],
                "pixel_count": int(class_counts.get(code, 0)),
            }
            for code in CLASSIFIER.CLASS_NAMES
        },
        "classification_precedence": [
            "Reuse script/s04-export_gfm_20m_class.py encode_classification and gfm_common.merge_observation without changing their rules.",
            "Per-pixel owner is the earliest Item with Flood and Water both known and Exclusion=0; ties are ordered by STAC Item ID.",
            "Reference water refines only an observed W=1 class; reference-only pixels remain NoData.",
            "NoData and Exclusion are distinct; partial Flood/Water observations use Inconsistent.",
        ],
        "mosaic_selection_statistics": dict(mosaic_stats),
        "grid": grid_metadata,
        "output": {
            "file": output_path.name,
            "bytes": file_bytes,
            "sha256": sha256(output_path),
            "format": "single-band lossless COG",
            "compression": image_structure.get("COMPRESSION"),
            "raw_uint8_bytes": raw_bytes,
            "compression_ratio": raw_bytes / file_bytes,
            "inspection_figure": str(figure_path.relative_to(tutorial_root)),
        },
        "software": {
            "python": sys.version.split()[0],
            "rasterio": rasterio.__version__,
            "gdal": rasterio.__gdal_version__,
        },
        "runtime_seconds": time.monotonic() - started,
        "license_note": "Source is Copernicus EMS Global Flood Monitoring. Confirm applicable CEMS/GFM redistribution terms before publishing the derived GeoTIFF.",
    }
    save_json(metadata_path, metadata)
    print(
        json.dumps(
            {
                "output": str(output_path),
                "bytes": file_bytes,
                "grid": [width, height],
                "class_pixel_counts": {
                    str(code): int(class_counts.get(code, 0))
                    for code in CLASSIFIER.CLASS_NAMES
                },
                "sha256": metadata["output"]["sha256"],
                "inspection_figure": str(figure_path),
            },
            indent=2,
        )
    )
    return metadata


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tutorial-root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--selection-json", type=Path)
    parser.add_argument("--domain-json", type=Path)
    parser.add_argument("--atlantis-root", type=Path)
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--figure-dir", type=Path)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    tutorial_root = args.tutorial_root.resolve()
    selection_path = args.selection_json or tutorial_root / "metadata/03a_selected_passes.json"
    selection = json.loads(selection_path.read_text())
    layers = selection["required_gfm_layers"]
    if layers != list(LAYERS):
        raise ValueError("Step 3a selection does not request the required four native GFM layers")
    domain_path = args.domain_json or tutorial_root / "metadata/02_domain_selection.json"
    domain_config = json.loads(domain_path.read_text())
    aoi_bbox = domain_config["satellite_analysis"]["domain"][
        "bbox_west_south_east_north"
    ]
    atlantis_root = (args.atlantis_root or tutorial_root / "Atlantis").resolve()
    output_dir = (args.output_dir or tutorial_root / "observation/GFM_extent").resolve()
    figure_dir = (args.figure_dir or atlantis_root / "runs/p03c").resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    results = []
    for selected in selection["passes"]:
        manifest_path, summary, assets, items, dataset_root = read_pass_inputs(
            tutorial_root, atlantis_root, selected, layers
        )
        if not args.force:
            stem = f"GFM_{selected['satellite']}_{selected['catalogue_date'].replace('-', '')}_{selected['pass_id'].split('_', 1)[1]}_extent20m"
            if (output_dir / f"{stem}.tif").exists() or (output_dir / f"{stem}.json").exists():
                raise FileExistsError(
                    f"p03c output exists; rerun with --force to replace: {output_dir / (stem + '.tif')}"
                )
        results.append(
            mosaic_pass(
                tutorial_root,
                atlantis_root,
                selected,
                aoi_bbox,
                manifest_path,
                summary,
                assets,
                items,
                dataset_root,
                output_dir,
                figure_dir,
                args.force,
            )
        )


if __name__ == "__main__":
    main()

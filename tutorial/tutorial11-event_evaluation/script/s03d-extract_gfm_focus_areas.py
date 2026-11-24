#!/usr/bin/env python3
"""Extract selected GFM focus boxes on the original Equi7 20 m pixel grid.

Inputs: selected focus-area JSON, native classification TIFF and provenance JSON.
Outputs: native-grid cropped GeoTIFFs and their extraction manifest.
Workflow:
    1. Project each WGS84 focus rectangle and snap its envelope outward.
    2. Copy the corresponding integral source window without resampling.
    3. Check retained geometry/sample values and record counts/provenance.
Classes and NoData=255 are unchanged; the projected envelope may extend beyond
the original geographic rectangle.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path

import numpy as np
import rasterio
from rasterio.windows import Window, bounds as window_bounds, from_bounds
from rasterio.warp import transform_bounds

CLASS_CODES = (0, 1, 2, 3, 4, 5, 6, 255)


def sha256(path: Path) -> str:
    """Return the SHA-256 digest of the original file bytes."""
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def aligned_window(src: rasterio.io.DatasetReader, bbox: list[float]) -> Window:
    """Project a densified WGS84 rectangle and snap its envelope outward to pixels."""
    west, south, east, north = map(float, bbox)
    bounds = transform_bounds(
        "EPSG:4326", src.crs, west, south, east, north, densify_pts=101
    )
    floating = from_bounds(*bounds, transform=src.transform)
    col0 = math.floor(floating.col_off + 1e-9)
    row0 = math.floor(floating.row_off + 1e-9)
    col1 = math.ceil(floating.col_off + floating.width - 1e-9)
    row1 = math.ceil(floating.row_off + floating.height - 1e-9)
    window = Window(col0, row0, col1 - col0, row1 - row0)
    full = Window(0, 0, src.width, src.height)
    clipped = window.intersection(full)
    if clipped != window:
        raise ValueError(f"Projected focus bbox extends outside source raster: {bbox}")
    return window


def extract(args: argparse.Namespace) -> None:
    """Copy integral native-grid focus windows, verify retained codes and save the manifest."""

    #*** 1. Read source provenance and geographic focus selections
    tutorial_dir = Path(args.tutorial_dir).resolve()
    focus_path = Path(args.focus_areas).resolve()
    source_path = Path(args.source_tiff).resolve()
    source_metadata_path = Path(args.source_metadata).resolve()
    output_dir = Path(args.output_dir).resolve()
    output_metadata_path = Path(args.output_metadata).resolve()

    focus_config = json.loads(focus_path.read_text(encoding="utf-8"))
    source_metadata = json.loads(source_metadata_path.read_text(encoding="utf-8"))
    areas = focus_config["focus_areas"]
    if not areas:
        raise ValueError(f"No focus areas are defined in {focus_path}")
    pass_id = str(source_metadata["pass_id"])
    satellite = str(source_metadata["satellite"])
    date = str(source_metadata["date"])
    date_tag = date.replace("-", "")
    class_definitions = source_metadata["classification_codes"]

    #*** 2. Copy exact native windows and check saved geometry/sample values
    with rasterio.open(source_path) as src:
        if src.count != 1 or src.dtypes[0] != "uint8" or src.nodata != 255:
            raise ValueError("Expected a one-band uint8 source with NoData=255")
        if src.crs is None or src.transform.a != 20 or src.transform.e != -20:
            raise ValueError("Expected source CRS and native 20 m north-up grid")
        if src.transform.b != 0 or src.transform.d != 0:
            raise ValueError("Rotated source grids are not supported")
        if rasterio.crs.CRS.from_wkt(source_metadata["grid"]["crs_wkt"]) != src.crs:
            raise ValueError("Source metadata CRS differs from the source GeoTIFF")

        output_areas = []
        total_bytes = 0
        for area in areas:
            bbox = list(map(float, area["bbox_west_south_east_north"]))
            window = aligned_window(src, bbox)
            data = src.read(1, window=window)
            classes, counts = np.unique(data, return_counts=True)
            observed_codes = set(map(int, classes))
            if not observed_codes.issubset(CLASS_CODES):
                raise ValueError(f"Unexpected classification codes: {sorted(observed_codes)}")

            filename = f"GFM_{satellite}_{date_tag}_{pass_id}_{area['id']}_extent20m.tif"
            output_path = output_dir / filename
            temporary_path = output_path.with_name(output_path.stem + ".tmp.tif")
            temporary_path.unlink(missing_ok=True)
            profile = src.profile.copy()
            profile.update(
                width=int(window.width), height=int(window.height),
                transform=src.window_transform(window), compress="ZSTD",
                zstd_level=9, tiled=True, blockxsize=512, blockysize=512,
                predictor=1, BIGTIFF="IF_SAFER",
            )
            try:
                with rasterio.open(temporary_path, "w", **profile) as dst:
                    dst.write(data, 1)
                    dst.set_band_description(1, src.descriptions[0] or "GFM 20 m classification")
                    dst.update_tags(**src.tags())
                    dst.update_tags(
                        focus_area_id=area["id"], focus_area_name=area["name"],
                        source_classification=source_path.name,
                        source_focus_config=focus_path.name,
                    )
                temporary_path.replace(output_path)
            finally:
                temporary_path.unlink(missing_ok=True)

            actual_bounds = list(window_bounds(window, src.transform))
            actual_transform = src.window_transform(window)
            with rasterio.open(output_path) as check:
                if (check.crs != src.crs or check.dtypes[0] != "uint8" or
                        check.nodata != 255 or check.count != 1 or
                        check.transform != actual_transform or
                        check.width != int(window.width) or
                        check.height != int(window.height)):
                    raise ValueError(f"Output grid contract failed: {output_path}")
                sample_points = (
                    (0, 0), (0, check.width - 1),
                    (check.height - 1, 0),
                    (check.height - 1, check.width - 1),
                    (check.height // 2, check.width // 2),
                )
                for row, col in sample_points:
                    expected = int(data[row, col])
                    observed = int(check.read(1, window=Window(col, row, 1, 1))[0, 0])
                    if observed != expected:
                        raise ValueError(f"Representative source value changed at {row},{col}")

            pixel_counts = {str(code): int(np.count_nonzero(data == code)) for code in CLASS_CODES}
            if sum(pixel_counts.values()) != data.size:
                raise AssertionError("Class pixel counts do not sum to the output dimensions")
            file_bytes = output_path.stat().st_size
            total_bytes += file_bytes
            output_areas.append({
                "id": area["id"],
                "name": area["name"],
                "source_wgs84_bbox_west_south_east_north": bbox,
                "extracted_equi7_bounds_west_south_east_north": actual_bounds,
                "output_file": str(output_path.relative_to(tutorial_dir)),
                "width": int(window.width),
                "height": int(window.height),
                "file_size_bytes": file_bytes,
                "sha256": sha256(output_path),
                "class_pixel_counts": pixel_counts,
            })
            print(f"{area['id']}: {filename} {window.width}x{window.height}, {file_bytes:,} bytes")

    #*** 3. Save the crop inventory and source provenance
    output_record = {
        "schema": "cmf-tutorial11-gfm-focus-extractions-1",
        "source_focus_areas": str(focus_path.relative_to(tutorial_dir)),
        "focus_selection_status": focus_config.get("status", "unspecified"),
        "source_classification_raster": str(source_path.relative_to(tutorial_dir)),
        "source_classification_sha256": sha256(source_path),
        "satellite": satellite,
        "date": date,
        "pass_id": pass_id,
        "orbit_direction": source_metadata.get("orbit_direction"),
        "crs": source_metadata["grid"]["crs_wkt"],
        "crs_authority": source_metadata["grid"].get("crs"),
        "resolution_m": [20, 20],
        "dtype": "uint8",
        "band_count": 1,
        "nodata": 255,
        "pixel_alignment": "Every output transform is an integer pixel window of the source raster; no reprojection, resampling, or class conversion is performed.",
        "compression": "ZSTD level 9, lossless",
        "class_codes": class_definitions,
        "output_areas": output_areas,
        "total_output_file_size_bytes": total_bytes,
        "total_output_file_size_mib": round(total_bytes / 1024**2, 3),
    }
    output_metadata_path.parent.mkdir(parents=True, exist_ok=True)
    temporary_metadata = output_metadata_path.with_suffix(output_metadata_path.suffix + ".tmp")
    temporary_metadata.write_text(
        json.dumps(output_record, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    temporary_metadata.replace(output_metadata_path)
    print(f"Manifest: {output_metadata_path}")
    print(f"Total: {total_bytes:,} bytes ({total_bytes / 1024**2:.3f} MiB)")


def main() -> None:
    """Parse source/focus/output paths and extract native-grid crops."""
    # Preserve the established CLI description while expanding source documentation.
    parser = argparse.ArgumentParser(description='Extract selected GFM focus boxes on the original Equi7 20 m pixel grid.')
    parser.add_argument("--tutorial-dir", required=True)
    parser.add_argument("--focus-areas", required=True)
    parser.add_argument("--source-tiff", required=True)
    parser.add_argument("--source-metadata", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--output-metadata", required=True)
    extract(parser.parse_args())


if __name__ == "__main__":
    main()

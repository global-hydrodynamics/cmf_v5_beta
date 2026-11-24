#!/usr/bin/env python3
"""Aggregate native GFM classes and plot WGS84 1 arc-minute flood fractions.

Inputs: native 20 m classification, domain/focus JSON, and contextual map/CSV data.
Outputs: flood fraction [%], valid source-pixel counts, and an overview PNG.
Workflow:
    1. Read the domain, focus areas, and Shell-supplied settings.
    2. Aggregate classified source-pixel centres, or read an existing fraction.
    3. Save the derived rasters when aggregating, then render the overview.

The denominator counts classes 0–4, not the area of the whole geographic cell.
Classes 5, 6, and 255 are excluded; cells without valid support remain NoData.
Rendering hides valid zero fractions without changing the saved raster values.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path
import sys

import matplotlib

# Select a noninteractive backend before pyplot; this workflow saves PNGs.
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import PowerNorm
from matplotlib.lines import Line2D
from matplotlib.patches import Rectangle
import matplotlib.patheffects as path_effects
import numpy as np
import rasterio
from rasterio.transform import Affine
from rasterio.warp import transform as transform_coordinates

SCRIPT_DIR = Path(__file__).resolve().parent
TUTORIAL_DIR = SCRIPT_DIR.parent
REPO_ROOT = TUTORIAL_DIR.parents[1]
sys.path.insert(0, str(REPO_ROOT / "visualization/river_map/script"))
import f06_common as river

FRACTION_NODATA = -9999.0  # No valid source support; distinct from valid 0% flood.


def read_aoi(config_path: Path) -> tuple[float, float, float, float]:
    """Read validated WGS84 bounds in west, south, east, north order [degrees]."""
    config = json.loads(config_path.read_text(encoding="utf-8"))
    bbox = config["satellite_analysis"]["domain"]["bbox_west_south_east_north"]
    if len(bbox) != 4:
        raise ValueError("Satellite analysis bbox must contain west, south, east, north")
    west, south, east, north = map(float, bbox)
    if not (-180 <= west < east <= 180 and -90 <= south < north <= 90):
        raise ValueError(f"Invalid WGS84 satellite analysis bbox: {bbox}")
    return west, south, east, north


def aggregate_fraction(source_path: Path, aoi: tuple[float, float, float, float]):
    """Compute 100 × class-1 count / class-0–4 count on a global 1-minute grid.

    Select source centres with west <= lon < east and south <= lat < north.
    Return float32 fractions [%], uint32 valid-pixel counts, the WGS84 grid
    transform, count/provenance metadata, and the source raster profile.
    Arrays are (north-to-south row, west-to-east column); uncovered cells use
    FRACTION_NODATA. Counts are pixel-weighted support, not physical cell area.
    """
    #*** 1. Allocate the global-minute-aligned output grid
    west, south, east, north = aoi
    west_minute = math.floor(west * 60)
    east_minute = math.ceil(east * 60)
    south_minute = math.floor(south * 60)
    north_minute = math.ceil(north * 60)
    width, height = east_minute - west_minute, north_minute - south_minute
    flood_count = np.zeros((height, width), dtype=np.uint32)
    valid_count = np.zeros((height, width), dtype=np.uint32)
    source_flood_in_aoi = 0
    source_valid_in_aoi = 0

    #*** 2. Bin valid source centres without loading the full native raster
    with rasterio.open(source_path) as source:
        if source.count != 1 or source.dtypes[0] != "uint8":
            raise ValueError(f"Expected single-band uint8 classification raster: {source_path}")
        if source.crs is None:
            raise ValueError(f"Classification raster has no CRS: {source_path}")
        transform = source.transform
        if not (transform.a > 0 and transform.e < 0 and transform.b == 0 and transform.d == 0):
            raise ValueError("Expected a north-up, unrotated source pixel grid")

        for _, window in source.block_windows(1):
            classes = source.read(1, window=window)
            unexpected = (classes > 6) & (classes != 255)
            if np.any(unexpected):
                codes = np.unique(classes[unexpected]).tolist()
                raise ValueError(f"Unexpected source classification codes: {codes}")
            # Exclusion/NoData pixels must not enter the fraction denominator.
            valid = (classes >= 0) & (classes <= 4)
            if not np.any(valid):
                continue
            rows, cols = np.nonzero(valid)
            rows = rows.astype(np.float64) + window.row_off + 0.5
            cols = cols.astype(np.float64) + window.col_off + 0.5
            xs = transform.c + cols * transform.a + rows * transform.b
            ys = transform.f + cols * transform.d + rows * transform.e
            lon, lat = transform_coordinates(
                source.crs, "EPSG:4326", xs.tolist(), ys.tolist()
            )
            lon = np.asarray(lon)
            lat = np.asarray(lat)
            in_aoi = (
                (lon >= west) & (lon < east) &
                (lat >= south) & (lat < north)
            )
            if not np.any(in_aoi):
                continue

            selected_rows, selected_cols = np.nonzero(valid)
            chosen_classes = classes[selected_rows[in_aoi], selected_cols[in_aoi]]
            source_valid_in_aoi += int(chosen_classes.size)
            source_flood_in_aoi += int(np.count_nonzero(chosen_classes == 1))
            minute_x = np.floor(lon[in_aoi] * 60).astype(np.int64) - west_minute
            minute_y = north_minute - 1 - np.floor(lat[in_aoi] * 60).astype(np.int64)
            if (
                np.any(minute_x < 0) or np.any(minute_x >= width) or
                np.any(minute_y < 0) or np.any(minute_y >= height)
            ):
                raise ValueError("A pixel centre inside the AOI mapped outside the output grid")
            flat = minute_y * width + minute_x
            valid_count += np.bincount(flat, minlength=height * width).reshape(height, width).astype(np.uint32)
            flood_flat = flat[chosen_classes == 1]
            flood_count += np.bincount(
                flood_flat, minlength=height * width
            ).reshape(height, width).astype(np.uint32)

        source_profile = source.profile.copy()
        source_crs = source.crs.to_string()
        source_transform = tuple(source.transform)

    #*** 3. Verify count conservation and derive percentages on valid support
    if int(valid_count.sum()) != source_valid_in_aoi:
        raise AssertionError("Aggregated valid-pixel count does not match AOI source pixels")
    if int(flood_count.sum()) != source_flood_in_aoi:
        raise AssertionError("Aggregated flood count does not match AOI source Flood pixels")
    if np.any(flood_count > valid_count):
        raise AssertionError("Flood count exceeds valid classified pixel count")

    fraction = np.full((height, width), FRACTION_NODATA, dtype=np.float32)
    covered = valid_count > 0
    fraction[covered] = (
        flood_count[covered].astype(np.float64) * 100.0 /
        valid_count[covered].astype(np.float64)
    ).astype(np.float32)
    if np.any((fraction[covered] < 0) | (fraction[covered] > 100)):
        raise AssertionError("Flood fraction lies outside 0–100 percent")

    #*** 4. Describe the pixel-edge geometry and aggregation provenance
    grid_transform = Affine(
        1 / 60, 0, west_minute / 60,
        0, -1 / 60, north_minute / 60,
    )
    metadata = {
        "aoi_bbox_wgs84_wsen": list(aoi),
        "aoi_pixel_center_rule": "west <= lon < east and south <= lat < north",
        "bin_assignment": "floor(longitude*60), floor(latitude*60), global 1-arc-minute cells",
        "source_classification_raster": str(source_path),
        "source_crs": source_crs,
        "source_transform": list(source_transform),
        "valid_class_codes": "0,1,2,3,4",
        "flood_class_code": 1,
        "excluded_class_codes": "5,6,255",
        "source_valid_pixels_in_aoi": source_valid_in_aoi,
        "source_flood_pixels_in_aoi": source_flood_in_aoi,
        "aggregated_valid_pixels": int(valid_count.sum()),
        "aggregated_flood_pixels": int(flood_count.sum()),
        "covered_1min_cells": int(np.count_nonzero(covered)),
        "covered_zero_fraction_cells": int(np.count_nonzero(covered & (flood_count == 0))),
        "uncovered_1min_cells": int(np.count_nonzero(~covered)),
        "maximum_valid_pixels_per_cell": int(valid_count.max(initial=0)),
        "fraction_nodata": FRACTION_NODATA,
    }
    return fraction, valid_count, grid_transform, metadata, source_profile


def write_rasters(
    fraction_path: Path, coverage_path: Path, fraction: np.ndarray,
    valid_count: np.ndarray, transform: Affine, source_profile: dict,
    metadata: dict,
) -> None:
    """Write fraction [%] and valid-count GeoTIFFs with the aggregation metadata.

    Fraction NoData is -9999; valid zero percentages are preserved. Coverage
    zero means no valid source pixels. Temporary rasters replace destinations
    only after both writes finish; remaining temporary files are cleaned up.
    """
    fraction_path.parent.mkdir(parents=True, exist_ok=True)
    coverage_path.parent.mkdir(parents=True, exist_ok=True)
    height, width = fraction.shape
    common = dict(
        driver="GTiff", width=width, height=height, crs="EPSG:4326",
        transform=transform, tiled=True, blockxsize=256, blockysize=256,
        compress="DEFLATE", zlevel=6,
    )
    fraction_tmp = fraction_path.with_name(fraction_path.stem + ".tmp.tif")
    coverage_tmp = coverage_path.with_name(coverage_path.stem + ".tmp.tif")
    try:
        with rasterio.open(
            fraction_tmp, "w", **common, count=1,
            dtype="float32", nodata=FRACTION_NODATA, predictor=3,
        ) as dst:
            dst.write(fraction, 1)
            dst.set_band_description(1, "Flood fraction among valid classified 20 m pixels [%]")
            dst.update_tags(
                AREA_OR_POINT="Area",
                aggregation="class 1 count / class 0-4 count * 100",
                source_resolution="20 m native Equi7 pixels; centres transformed to WGS84",
                source_crs=str(source_profile.get("crs")),
                aoi_bbox_wgs84_wsen=json.dumps(metadata["aoi_bbox_wgs84_wsen"]),
                aoi_pixel_center_rule=metadata["aoi_pixel_center_rule"],
                bin_assignment=metadata["bin_assignment"],
                excluded_class_codes=metadata["excluded_class_codes"],
                source_valid_pixels_in_aoi=str(metadata["source_valid_pixels_in_aoi"]),
                source_flood_pixels_in_aoi=str(metadata["source_flood_pixels_in_aoi"]),
                covered_1min_cells=str(metadata["covered_1min_cells"]),
                uncovered_1min_cells=str(metadata["uncovered_1min_cells"]),
            )
        with rasterio.open(
            coverage_tmp, "w", **common, count=1, dtype="uint32", predictor=2,
        ) as dst:
            dst.write(valid_count, 1)
            dst.set_band_description(1, "Valid classified source pixels (classes 0-4)")
            dst.update_tags(
                AREA_OR_POINT="Area",
                source_resolution="20 m native Equi7 pixels; centres transformed to WGS84",
                aoi_bbox_wgs84_wsen=json.dumps(metadata["aoi_bbox_wgs84_wsen"]),
                aoi_pixel_center_rule=metadata["aoi_pixel_center_rule"],
                valid_class_codes=metadata["valid_class_codes"],
            )
        fraction_tmp.replace(fraction_path)
        coverage_tmp.replace(coverage_path)
    finally:
        fraction_tmp.unlink(missing_ok=True)
        coverage_tmp.unlink(missing_ok=True)


def read_focus_areas(
    settings_path: Path, aoi: tuple[float, float, float, float],
) -> list[dict]:
    """Read focus-area definitions and check their bounds lie within the AOI."""
    settings = json.loads(settings_path.read_text(encoding="utf-8"))
    areas = settings["focus_areas"]
    if not areas:
        raise ValueError(f"No focus areas in {settings_path}")
    west_aoi, south_aoi, east_aoi, north_aoi = aoi
    for area in areas:
        west, south, east, north = map(
            float, area["bbox_west_south_east_north"]
        )
        if not (
            west_aoi <= west < east <= east_aoi and
            south_aoi <= south < north <= north_aoi
        ):
            raise ValueError(f"Focus area {area.get('id')} is outside the satellite AOI")
    return areas


def create_figure(
    fraction: np.ndarray, transform: Affine,
    aoi: tuple[float, float, float, float],
    map_dir: Path, tile_cache: Path, impact_locations: Path,
    focus_areas: list[dict], output_path: Path,
    no_osm: bool = False, *, fig_width=12.5, fig_height=8.2, dpi=180,
    cmap_name="Reds", vmin=0, vmax=100, gamma=0.55,
) -> None:
    """Plot positive fractions with contextual rivers, focus boxes and localities.

    The input fraction is a north-up percentage raster; transform describes
    pixel edges. NoData and valid zero fractions are transparent only in this
    display. Shell-supplied limits and gamma control PowerNorm, not the data.
    """
    #*** 1. Prepare the geographic view and optional OSM context
    west, south, east, north = aoi
    margin = 0.5
    view = (west - margin, south - margin, east + margin, north + margin)
    _, _, segments, classes = river.read_network(map_dir, view)
    figure, ax = plt.subplots(figsize=(fig_width, fig_height))
    river.draw_osm(ax, view, tile_cache, alpha=0.68, white_mix=0.42) if not no_osm else None

    #*** 2. Draw positive fractions and analysis/focus-area boundaries
    visible_fraction = np.ma.masked_where(
        (fraction == FRACTION_NODATA) | (fraction <= 0), fraction
    )
    cmap = plt.get_cmap(cmap_name).copy()
    cmap.set_bad((1, 1, 1, 0))
    norm = PowerNorm(gamma=gamma, vmin=vmin, vmax=vmax)
    west_edge, east_edge = transform.c, transform.c + fraction.shape[1] * transform.a
    north_edge, south_edge = transform.f, transform.f + fraction.shape[0] * transform.e
    image = ax.imshow(
        visible_fraction, extent=(west_edge, east_edge, south_edge, north_edge),
        origin="upper", interpolation="nearest", cmap=cmap, norm=norm,
        alpha=0.93, zorder=2,
    )
    ax.add_patch(Rectangle(
        (west, south), east - west, north - south, fill=False,
        edgecolor="#d47b00", linewidth=1.7, linestyle="--", zorder=3.4,
    ))
    river.draw_network(ax, segments, classes)
    for area in focus_areas:
        west, south, east, north = map(
            float, area["bbox_west_south_east_north"]
        )
        ax.add_patch(Rectangle(
            (west, south), east - west, north - south, fill=False,
            edgecolor="#007f73", linewidth=1.8, zorder=5,
        ))
        ax.text(
            west + 0.012, north - 0.012, area["id"].upper(),
            fontsize=7, fontweight="bold", color="#005f56",
            ha="left", va="top", zorder=7,
            path_effects=[path_effects.withStroke(linewidth=2.5, foreground="white")],
        )
    river.format_axes(ax, view, 1.0, 1.0)

    #*** 3. Add reported-impact localities as contextual information
    with impact_locations.open(newline="", encoding="utf-8") as stream:
        points = list(csv.DictReader(stream))
    if not points:
        raise ValueError(f"No reported impact locations in {impact_locations}")
    point_styles = {
        group: {"color": "#7b3294", "label": "Reported flood impacts", "size": 18}
        for group in {point["plot_group"] for point in points}
    }
    river.draw_point_groups(ax, points, point_styles, show_labels=False)
    west_view, east_view = ax.get_xlim()
    south_view, north_view = ax.get_ylim()
    for point in points:
        lon, lat = float(point["longitude"]), float(point["latitude"])
        if not (west_view <= lon <= east_view and south_view <= lat <= north_view):
            continue
        dx, dy = float(point["label_dx"]), float(point["label_dy"])
        ax.annotate(
            point["plot_label"], (lon, lat), xytext=(lon + dx, lat + dy),
            textcoords="data", fontsize=7, color="#3f174c",
            ha="left" if dx >= 0 else "right", va="center",
            path_effects=[path_effects.withStroke(linewidth=2.2, foreground="white")],
            arrowprops=dict(arrowstyle="-", color="#7b3294", linewidth=0.45, alpha=0.8),
            zorder=6,
        )

    #*** 4. Label the maintained acquisition view and save the Figure
    ax.set_title(
        "GFM Flood Fraction · 1 arc-minute\n"
        "Sentinel-1A · 2021-07-15 · S1A_o038784_dt049389",
        fontsize=12, pad=9,
    )
    colorbar = figure.colorbar(image, ax=ax, pad=0.035, ticks=[0, 1, 5, 10, 25, 50, 75, 100])
    colorbar.set_label("Flood Fraction [%]")
    ax.legend(
        handles=[
            Line2D([0], [0], color="#d47b00", linewidth=1.7, linestyle="--",
                   label="Satellite analysis domain (candidate)"),
            Line2D([0], [0], color="#285A9B", linewidth=1.5,
                   label="CaMa-Flood river network"),
            Rectangle((0, 0), 1, 1, fill=False, edgecolor="#007f73",
                      linewidth=1.8, label="Selected focus areas"),
            Line2D([0], [0], marker="o", linestyle="none", markersize=5,
                   markerfacecolor="#7b3294", markeredgecolor="white",
                   label="Reported flood impacts"),
        ],
        loc="upper left", framealpha=0.9, fontsize=8,
    )
    river.draw_attribution(ax)
    river.save_figure(figure, output_path, dpi)


def main() -> int:
    """Read settings, aggregate or reuse fraction data, and save the overview."""
    #*** 1. Read the Shell-facing input, output and display options
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--domain-config", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--coverage-output", type=Path, required=True)

    parser.add_argument("--impact-locations", type=Path, required=True)
    parser.add_argument("--focus-areas", type=Path, required=True)
    parser.add_argument("--figure-output", type=Path, required=True)
    parser.add_argument("--map-dir", type=Path, default=REPO_ROOT / "map/glb_15min")
    parser.add_argument(
        "--tile-cache", type=Path, default=Path.home() / ".cache/cmf_flood_osm_tiles",
    )
    parser.add_argument(
        "--render-only", action="store_true",
        help="Regenerate the Figure from the existing fraction raster",
    )
    parser.add_argument(
        "--no-osm", action="store_true",
        help="Render rivers and data without requesting OSM tiles",
    )

    parser.add_argument("--fig-width", type=float, default=12.5, help="Canvas width [inches]")
    parser.add_argument("--fig-height", type=float, default=8.2, help="Canvas height [inches]")
    parser.add_argument("--dpi", type=int, default=180, help="PNG resolution [pixels/inch]")
    parser.add_argument("--cmap", default="Reds")
    parser.add_argument("--vmin", type=float, default=0)
    parser.add_argument("--vmax", type=float, default=100)
    parser.add_argument("--gamma", type=float, default=0.55)
    args = parser.parse_args()

    #*** 2. Read the authoritative domain and focus-area definitions
    aoi = read_aoi(args.domain_config)
    focus_areas = read_focus_areas(args.focus_areas, aoi)

    #*** 3. Reuse the saved fraction for a render-only invocation
    if args.render_only:
        with rasterio.open(args.output) as existing:
            if existing.crs is None or existing.crs.to_epsg() != 4326:
                raise ValueError(f"Existing fraction raster must be WGS84: {args.output}")
            if existing.count != 1 or existing.dtypes[0] != "float32":
                raise ValueError(f"Existing fraction raster must be single-band float32: {args.output}")
            fraction = existing.read(1)
            grid_transform = existing.transform
        create_figure(
            fraction, grid_transform, aoi, args.map_dir,
            args.tile_cache, args.impact_locations, focus_areas,
            args.figure_output, args.no_osm, fig_width=args.fig_width,
            fig_height=args.fig_height, dpi=args.dpi, cmap_name=args.cmap,
            vmin=args.vmin, vmax=args.vmax, gamma=args.gamma,
        )
        print(f"figure={args.figure_output} ({args.figure_output.stat().st_size} bytes)")
        return 0

    #*** 4. Aggregate native classes and save fraction/count rasters
    fraction, valid_count, grid_transform, metadata, source_profile = aggregate_fraction(
        args.input, aoi
    )
    write_rasters(
        args.output, args.coverage_output, fraction, valid_count,
        grid_transform, source_profile, metadata,
    )

    #*** 5. Render the overview and report generated products
    create_figure(
        fraction, grid_transform, aoi, args.map_dir,
        args.tile_cache, args.impact_locations, focus_areas,
        args.figure_output, args.no_osm, fig_width=args.fig_width,
        fig_height=args.fig_height, dpi=args.dpi, cmap_name=args.cmap,
        vmin=args.vmin, vmax=args.vmax, gamma=args.gamma,
    )
    print(json.dumps(metadata, indent=2))
    print(f"fraction_raster={args.output} ({args.output.stat().st_size} bytes)")
    print(f"valid_count_raster={args.coverage_output} ({args.coverage_output.stat().st_size} bytes)")
    print(f"figure={args.figure_output} ({args.figure_output.stat().st_size} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

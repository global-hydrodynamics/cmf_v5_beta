#!/usr/bin/env python3
"""Render extracted GFM focus rasters with OSM context."""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import BoundaryNorm, ListedColormap, to_rgba
from matplotlib.patches import Patch
from matplotlib.ticker import MaxNLocator
import numpy as np
from PIL import Image
import rasterio
from rasterio.enums import Resampling
from rasterio.vrt import WarpedVRT

SCRIPT_DIR = Path(__file__).resolve().parent
TUTORIAL_DIR = SCRIPT_DIR.parent
REPO_ROOT = TUTORIAL_DIR.parents[1]
sys.path.insert(0, str(REPO_ROOT / "visualization/river_map/script"))
import f06_common as river

CLASS_CODES = (0, 1, 2, 3, 4, 5, 6, 255)
CLASS_NAMES = {
    0: "Land", 1: "Flood", 2: "Permanent water", 3: "Seasonal water",
    4: "Other water", 5: "Exclusion", 6: "Inconsistent", 255: "NoData (transparent)",
}
CLASS_COLORS = {
    0: "#f7f7f2", 1: "#e53935", 2: "#00aedd", 3: "#0066ad",
    4: "#8764a8", 5: "#c9c9c9", 6: "#f39c12", 255: "#eeeeee",
}
CLASS_OPACITY = {0: 0.50, 1: 0.60, 2: 0.60, 3: 0.60,
                 4: 0.60, 5: 0.50, 6: 0.85, 255: 0.0}
OSM_CONTEXT_EXTENT = (3.5, 48.7, 9.8, 51.9)


def focus_view(bbox: list[float]) -> tuple[float, float, float, float]:
    west, south, east, north = map(float, bbox)
    dx, dy = east - west, north - south
    padx, pady = max(dx * 0.16, 0.025), max(dy * 0.16, 0.025)
    return west - padx, south - pady, east + padx, north + pady


def load_display_raster(path: Path, max_size: int = 720):
    with rasterio.open(path) as source:
        if source.crs is None or source.count != 1 or source.dtypes[0] != "uint8":
            raise ValueError(f"Unexpected extracted classification raster: {path}")
        with WarpedVRT(source, crs="EPSG:4326", resampling=Resampling.nearest) as view:
            scale = min(1.0, max_size / max(view.width, view.height))
            shape = (max(1, round(view.height * scale)), max(1, round(view.width * scale)))
            data = view.read(1, out_shape=shape, resampling=Resampling.nearest)
            bounds = view.bounds
    return data, (bounds.left, bounds.right, bounds.bottom, bounds.top)


def crop_osm(image: np.ndarray, extent: tuple[float, float, float, float],
             output_size: tuple[int, int]) -> np.ndarray:
    west, south, east, north = extent
    context_west, context_south, context_east, context_north = OSM_CONTEXT_EXTENT
    height, width = image.shape[:2]
    x0 = max(0, math.floor((west-context_west)/(context_east-context_west)*width))
    x1 = min(width, math.ceil((east-context_west)/(context_east-context_west)*width))
    y0 = max(0, math.floor((context_north-north)/(context_north-context_south)*height))
    y1 = min(height, math.ceil((context_north-south)/(context_north-context_south)*height))
    if x1 <= x0 or y1 <= y0:
        raise ValueError(f"OSM cache extent does not cover panel: {extent}")
    crop = Image.fromarray(image[y0:y1, x0:x1])
    crop = crop.resize(output_size, resample=Image.Resampling.BILINEAR)
    softened = Image.blend(crop, Image.new("RGB", output_size, "white"), 0.20)
    return np.asarray(softened)


def render(args: argparse.Namespace) -> None:
    tutorial_dir = Path(args.tutorial_dir).resolve()
    manifest_path = Path(args.extracted_areas).resolve()
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    areas = manifest["output_areas"]
    if not areas:
        raise ValueError(f"No extracted areas in {manifest_path}")
    paths = []
    for area in areas:
        path = (tutorial_dir / area["output_file"]).resolve()
        if not path.is_relative_to(tutorial_dir) or not path.is_file():
            raise FileNotFoundError(f"Missing or invalid extracted-area file: {area['output_file']}")
        paths.append(path)

    views = [focus_view(area["source_wgs84_bbox_west_south_east_north"]) for area in areas]
    osm_context = river.read_osm(OSM_CONTEXT_EXTENT, Path(args.tile_cache).expanduser())
    cmap = ListedColormap([
        to_rgba(CLASS_COLORS[code], CLASS_OPACITY[code]) for code in CLASS_CODES
    ])
    cmap.set_bad((0, 0, 0, 0))
    norm = BoundaryNorm([-0.5, 0.5, 1.5, 2.5, 3.5, 4.5, 5.5, 6.5, 255.5], cmap.N)

    count = len(areas)
    columns = 3
    rows = math.ceil(count / columns)
    figure, axes = plt.subplots(rows, columns, figsize=(14, rows * 3.35), squeeze=False)
    axes_flat = axes.ravel()
    for index, (area, path, view_extent) in enumerate(zip(areas, paths, views)):
        ax = axes_flat[index]
        data, raster_extent = load_display_raster(path)
        panel_width = max(
            400,
            round(1000 * (view_extent[2]-view_extent[0]) / (view_extent[3]-view_extent[1])),
        )
        panel_osm = crop_osm(osm_context, view_extent, (panel_width, 650))
        ax.imshow(
            panel_osm, extent=(view_extent[0], view_extent[2], view_extent[1], view_extent[3]),
            origin="upper", alpha=0.85, zorder=0,
        )
        masked = np.ma.masked_equal(data, 255)
        ax.imshow(
            masked, extent=raster_extent, origin="upper", interpolation="nearest",
            cmap=cmap, norm=norm, zorder=2,
        )
        west, south, east, north = map(
            float, area["source_wgs84_bbox_west_south_east_north"]
        )
        ax.set_xlim(view_extent[0], view_extent[2])
        ax.set_ylim(view_extent[1], view_extent[3])
        ax.set_aspect(1 / math.cos(math.radians((south + north) / 2)))
        ax.set_title(f"{area['id']} — {area['name']}", fontsize=10)
        ax.xaxis.set_major_locator(MaxNLocator(3))
        ax.yaxis.set_major_locator(MaxNLocator(3))
        ax.tick_params(labelsize=7)
        if index // columns == rows - 1:
            ax.set_xlabel("Longitude [°]", fontsize=8)
        if index % columns == 0:
            ax.set_ylabel("Latitude [°]", fontsize=8)

    for ax in axes_flat[count:]:
        ax.set_visible(False)
    legend = [
        Patch(facecolor=CLASS_COLORS[code], edgecolor="#444444", linewidth=0.3,
              label=f"{code}: {CLASS_NAMES[code]}")
        for code in CLASS_CODES if code != 255
    ]
    legend.append(Patch(facecolor="white", edgecolor="#777777", hatch="///",
                        label="255: NoData (transparent)"))
    figure.legend(handles=legend, loc="lower center", ncol=4, frameon=True,
                  fontsize=8, bbox_to_anchor=(0.5, 0.015))
    figure.suptitle(
        f"GFM native 20 m classification — {manifest['satellite']} · {manifest['date']}\n"
        f"{manifest['pass_id']} · {count} selected focus areas",
        fontsize=13,
    )
    figure.text(
        0.99, 0.005, river.OSM_ATTRIBUTION, ha="right", va="bottom", fontsize=7,
        color="#333333",
    )
    figure.text(
        0.01, 0.005,
        "Contains modified Copernicus Emergency Management Service information 2026",
        ha="left", va="bottom", fontsize=7, color="#333333",
    )
    figure.tight_layout(rect=(0.015, 0.075, 0.985, 0.94))
    output = Path(args.figure_output).resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(output, dpi=150)
    plt.close(figure)
    print(f"Wrote {output} ({output.stat().st_size:,} bytes)")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tutorial-dir", required=True)
    parser.add_argument("--extracted-areas", required=True)
    parser.add_argument("--figure-output", required=True)
    parser.add_argument("--tile-cache", required=True)
    render(parser.parse_args())


if __name__ == "__main__":
    main()

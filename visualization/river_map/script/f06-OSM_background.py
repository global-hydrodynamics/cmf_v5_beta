#!/usr/bin/env python3
"""Render p01-f06 OSM background and event-impact overlay panels."""
from __future__ import annotations

import argparse
import csv
from importlib.util import module_from_spec, spec_from_file_location
import math
from pathlib import Path
import sys
import time
from urllib.error import URLError
from urllib.request import Request, urlopen

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
from matplotlib.colors import ListedColormap
from matplotlib.lines import Line2D
from matplotlib.patches import Rectangle
import numpy as np
from PIL import Image
import rasterio
from rasterio.transform import from_bounds, from_origin
from rasterio.warp import reproject, Resampling

SCRIPT_DIR = Path(__file__).resolve().parent
RIVER_MAP_DIR = SCRIPT_DIR.parent
sys.path.insert(0, str(SCRIPT_DIR))
_F03_PATH = SCRIPT_DIR / "f03a-vector_river_map-upstream_area.py"
_spec = spec_from_file_location("f03a_vector_river_map", _F03_PATH)
_f03 = module_from_spec(_spec)
_spec.loader.exec_module(_f03)
from river_map_common import read_map_raster, validate_extent

OSM_URL = "https://tile.openstreetmap.org/{z}/{x}/{y}.png"
OSM_ATTRIBUTION = "© OpenStreetMap contributors · openstreetmap.org/copyright"
USER_AGENT = "CaMaFloodMapExplorerGallery/1.0 (https://github.com/global-hydrodynamics/cmf_v5_beta)"
DEFAULT_EXTENT = (3.0, 46.0, 12.0, 53.0)
DEFAULT_TARGET_BASIN = 74
PLOT_COLORS = {
    "rhine_tributaries": "#c62828",
    "comparison_rivers": "#6a51a3",
}


def arguments():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--panel", choices=("a", "b"), default="a")
    parser.add_argument("--map-dir", type=Path, required=True,
                        help="CaMa-Flood map root containing params.txt and netcdf/")
    parser.add_argument("--west", type=float, default=DEFAULT_EXTENT[0])
    parser.add_argument("--south", type=float, default=DEFAULT_EXTENT[1])
    parser.add_argument("--east", type=float, default=DEFAULT_EXTENT[2])
    parser.add_argument("--north", type=float, default=DEFAULT_EXTENT[3])
    parser.add_argument("--target-basin", type=int, default=DEFAULT_TARGET_BASIN)
    parser.add_argument("--zoomup-file", type=Path,
                        default=RIVER_MAP_DIR / "data/f06b_zoomup.csv")
    parser.add_argument("--plot-file", type=Path,
                        default=RIVER_MAP_DIR / "data/f06b_plot.csv")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--osm", dest="osm", action="store_true", default=True,
                       help="Add OSM Standard background (default)")
    group.add_argument("--no-osm", dest="osm", action="store_false",
                       help="Render without OSM tiles")
    parser.add_argument("--tile-cache", type=Path,
                        default=Path.home() / ".cache/cmf_flood_osm_tiles")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--dpi", type=int, default=180)
    return parser.parse_args()


def tile_xy(lon: float, lat: float, zoom: int) -> tuple[float, float]:
    n = 2**zoom
    lat = min(85.05112878, max(-85.05112878, lat))
    x = (lon + 180.0) / 360.0 * n
    y = (1.0 - math.asinh(math.tan(math.radians(lat))) / math.pi) / 2.0 * n
    return x, y


def read_osm(extent: tuple[float, float, float, float], cache: Path):
    west, south, east, north = extent
    width_px, height_px = 1800, 1400
    zoom = max(0, min(18, int(math.floor(math.log2(width_px * 360 / (256 * (east - west)))))))
    while True:
        x0, y0 = tile_xy(west, north, zoom)
        x1, y1 = tile_xy(east, south, zoom)
        c0, c1 = math.floor(x0), math.ceil(x1) - 1
        r0, r1 = max(0, math.floor(y0)), min(2**zoom - 1, math.ceil(y1) - 1)
        if (c1 - c0 + 1) * (r1 - r0 + 1) <= 32 or zoom == 0:
            break
        zoom -= 1

    tile_size = 256
    mosaic = Image.new("RGB", ((c1 - c0 + 1) * tile_size, (r1 - r0 + 1) * tile_size), "white")
    cache.mkdir(parents=True, exist_ok=True)
    for row in range(r0, r1 + 1):
        for col in range(c0, c1 + 1):
            x, y = col % (2**zoom), row
            path = cache / f"{zoom}_{x}_{y}.png"
            if not path.exists():
                request = Request(OSM_URL.format(z=zoom, x=x, y=y), headers={"User-Agent": USER_AGENT})
                with urlopen(request, timeout=20) as response:
                    path.write_bytes(response.read())
                time.sleep(0.2)
            with Image.open(path) as tile:
                mosaic.paste(tile.convert("RGB"), ((col - c0) * tile_size, (row - r0) * tile_size))

    world = 2 * math.pi * 6378137.0
    pixel = world / (2**zoom * tile_size)
    src_transform = from_origin((c0 / 2**zoom - .5) * world,
                                (.5 - r0 / 2**zoom) * world, pixel, pixel)
    dst = np.zeros((height_px, width_px, 3), dtype=np.uint8)
    dst_transform = from_bounds(west, south, east, north, width_px, height_px)
    source = np.asarray(mosaic)
    for band in range(3):
        reproject(source[:, :, band], dst[:, :, band], src_transform=src_transform,
                  src_crs="EPSG:3857", dst_transform=dst_transform,
                  dst_crs="EPSG:4326", resampling=Resampling.bilinear)
    return dst


def cell_edges(centers: np.ndarray) -> np.ndarray:
    """Return cell edges for regularly spaced raster center coordinates."""
    step = centers[1] - centers[0]
    edges = np.empty(centers.size + 1, dtype=float)
    edges[1:-1] = (centers[:-1] + centers[1:]) / 2.0
    edges[0] = centers[0] - step / 2.0
    edges[-1] = centers[-1] + step / 2.0
    return edges


def read_zoom_data(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as source:
        return list(csv.DictReader(source))


def main():
    args = arguments()
    map_dir = args.map_dir.expanduser().resolve()
    zoom_rows = read_zoom_data(args.zoomup_file)
    zoom_box = next(row for row in zoom_rows if row["region_id"] == "f06b_zoomup")
    if args.panel == "b":
        extent = tuple(float(zoom_box[key]) for key in ("west", "south", "east", "north"))
    else:
        extent = (args.west, args.south, args.east, args.north)
    west, south, east, north = extent
    if not (west < east and south < north):
        raise SystemExit("ERROR: bbox requires west < east and south < north")

    geometry = _f03.read_geometry(map_dir / "params.txt")
    validate_extent(west, east, south, north, geometry)
    netcdf = map_dir / "netcdf"
    (_, source_lon, source_lat, destination_lon, destination_lat,
     _, area_classes, _, _, _) = _f03.read_network(
        netcdf / "uparea.nc", netcdf / "nextxy.nc", netcdf / "lonlat.nc", map_dir / "params.txt"
    )

    basin_plot = None
    if args.panel == "a":
        basin_lon, basin_lat, basin_raw = read_map_raster(
            netcdf / "basin.nc", "basin", "1", geometry
        )
        basin = basin_raw.filled(np.nan)
        lon_indices = np.flatnonzero((basin_lon >= west) & (basin_lon <= east))
        lat_indices = np.flatnonzero((basin_lat >= south) & (basin_lat <= north))
        x_slice = slice(lon_indices[0], lon_indices[-1] + 1)
        y_slice = slice(lat_indices.min(), lat_indices.max() + 1)
        plot_lon, plot_lat = basin_lon[x_slice], basin_lat[y_slice]
        plot_basin = basin[y_slice, x_slice]
        target_cells = np.isfinite(plot_basin) & (plot_basin == args.target_basin)
        if not np.any(target_cells):
            raise SystemExit(f"ERROR: Basin ID {args.target_basin} is absent from the requested bbox")
        basin_plot = (plot_lon, plot_lat, plot_basin, target_cells)

    inside = (
        (source_lon >= west) & (source_lon <= east) &
        (source_lat >= south) & (source_lat <= north) &
        (destination_lon >= west) & (destination_lon <= east) &
        (destination_lat >= south) & (destination_lat <= north)
    )
    segments = np.stack((
        np.column_stack((source_lon[inside], source_lat[inside])),
        np.column_stack((destination_lon[inside], destination_lat[inside])),
    ), axis=1)
    selected_classes = area_classes[inside]

    fig, ax = plt.subplots(figsize=(11.4 if args.panel == "b" else 10.2, 7.8))
    ax.set_xlim(west, east)
    ax.set_ylim(south, north)
    ax.set_aspect(1.0 / math.cos(math.radians((south + north) / 2.0)))
    osm_loaded = False
    if args.osm:
        try:
            image = read_osm(extent, args.tile_cache.expanduser())
            image = np.asarray(Image.blend(
                Image.fromarray(image), Image.new("RGB", (image.shape[1], image.shape[0]), "white"), 0.18
            ))
            ax.imshow(image, extent=(west, east, south, north), origin="upper", alpha=0.5, zorder=0)
            osm_loaded = True
        except (OSError, URLError, TimeoutError, ValueError) as exc:
            print(f"WARNING: OSM tile unavailable; rendering overlays and river network without OSM: {exc}")

    if basin_plot is not None:
        plot_lon, plot_lat, plot_basin, target_cells = basin_plot
        outside_target = np.ma.masked_where(target_cells, np.ones(plot_basin.shape))
        ax.pcolormesh(
            cell_edges(plot_lon), cell_edges(plot_lat), outside_target,
            cmap=ListedColormap(["#858585"]), vmin=0, vmax=1,
            alpha=0.5, shading="flat", linewidth=0, rasterized=True, zorder=1,
        )
        ax.contour(plot_lon, plot_lat, target_cells.astype(np.uint8), levels=[0.5],
                   colors=["#d89000"], linewidths=0.65, zorder=1.5)
        zoom_x, zoom_y, zoom_w, zoom_h = (float(zoom_box[key]) for key in
                                          ("west", "south", "east", "north"))
        ax.add_patch(Rectangle(
            (zoom_x, zoom_y), zoom_w - zoom_x, zoom_h - zoom_y,
            fill=False, edgecolor="#c62828", linewidth=1.8,
            linestyle="--", zorder=3.5,
        ))
        ax.text(zoom_x + 0.06, zoom_y + 0.05, "f06b impact-area zoom",
                color="#8e0000", fontsize=8, weight="bold", zorder=4,
                bbox=dict(facecolor="white", alpha=0.8, edgecolor="none", pad=2))

    if args.panel == "b":
        for row in zoom_rows:
            if row["region_id"] == "f06b_zoomup":
                continue
            x0, y0, x1, y1 = (float(row[key]) for key in ("west", "south", "east", "north"))
            color = row["color"]
            ax.add_patch(Rectangle(
                (x0, y0), x1 - x0, y1 - y0,
                fill=False, edgecolor=color, linewidth=1.5,
                linestyle=row["linestyle"], zorder=2.5,
            ))
            ax.text(x0 + 0.04, y1 - 0.035, row["label"],
                    color=color, fontsize=7.5, weight="bold", va="top", zorder=4,
                    bbox=dict(facecolor="white", alpha=0.84, edgecolor="none", pad=1.8))

    for area_class, (color, width) in enumerate(zip(_f03.AREA_COLORS, _f03.AREA_WIDTHS)):
        selected = selected_classes == area_class
        if np.any(selected):
            ax.add_collection(LineCollection(
                segments[selected], colors=color, linewidths=width * 72 * 0.55,
                alpha=0.94, zorder=3 + area_class * 0.1, capstyle="round",
            ))

    if args.panel == "b":
        with args.plot_file.open(newline="", encoding="utf-8") as source:
            points = list(csv.DictReader(source))
        for group, color in PLOT_COLORS.items():
            selected = [point for point in points if point["plot_group"] == group]
            ax.scatter(
                [float(point["longitude"]) for point in selected],
                [float(point["latitude"]) for point in selected],
                s=30, marker="o", facecolor=color, edgecolor="white", linewidth=0.7,
                alpha=0.9, zorder=5, label=group.replace("_", " ").title(),
            )
            for point in selected:
                lon, lat = float(point["longitude"]), float(point["latitude"])
                dx, dy = float(point["label_dx"]), float(point["label_dy"])
                label = point["plot_label"]
                if point["coordinate_confidence"] == "low":
                    label += " (?)"
                ax.annotate(
                    label, (lon, lat), xytext=(lon + dx, lat + dy), textcoords="data",
                    fontsize=7, color="#222222", ha="left" if dx >= 0 else "right", va="center",
                    bbox=dict(facecolor="white", alpha=0.78, edgecolor="none", pad=1.2),
                    arrowprops=dict(arrowstyle="-", color=color, linewidth=0.55, alpha=0.8),
                    zorder=6,
                )
        region_handles = [
            Line2D([0], [0], color=row["color"], linewidth=1.5,
                   linestyle=row["linestyle"], label=row["short_label"])
            for row in zoom_rows if row["region_id"] != "f06b_zoomup"
        ]
        point_handles, _ = ax.get_legend_handles_labels()
        ax.legend(handles=point_handles + region_handles, loc="center left",
                  bbox_to_anchor=(1.01, 0.5), fontsize=8, framealpha=0.9, borderpad=0.6)
        ax.set_title(
            "Reported flood-impact localities and candidate observation domains\n"
            "Markers are approximate town centers; boxes are not flood boundaries",
            fontsize=10,
        )

    if osm_loaded:
        ax.text(.995, .012, OSM_ATTRIBUTION, transform=ax.transAxes,
                ha="right", va="bottom", fontsize=7, color="#333333",
                bbox=dict(facecolor="white", alpha=.82, edgecolor="none", pad=2), zorder=8)
    ax.set_xlabel("Longitude [°E]")
    ax.set_ylabel("Latitude [°N]")
    ax.set_xticks(np.arange(math.ceil(west), east + 0.01, 1.0 if args.panel == "b" else 2.0))
    ax.set_yticks(np.arange(math.ceil(south), north + 0.01, 0.5 if args.panel == "b" else 1.0))
    ax.tick_params(direction="out", length=4, labelsize=9)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    fig.subplots_adjust(left=0.11, right=0.78 if args.panel == "b" else 0.985,
                        bottom=0.11, top=0.88 if args.panel == "b" else 0.985)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(args.output, dpi=args.dpi, bbox_inches="tight", pad_inches=0.08, facecolor="white")
    plt.close(fig)
    print(f"Wrote {args.output}: panel f06{args.panel}, {int(inside.sum())} CaMa outlet links; bbox={list(extent)}")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Draw the wide OSM, Basin ID and CaMa-Flood network overview for f06a."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
from matplotlib.lines import Line2D
from matplotlib.patches import Rectangle
import numpy as np

import f06_common as common

SCRIPT_DIR = Path(__file__).resolve().parent
RIVER_MAP_DIR = SCRIPT_DIR.parent


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--map-dir", type=Path, required=True)
    parser.add_argument("--settings", type=Path, default=RIVER_MAP_DIR / "data/f06_settings.json")
    parser.add_argument("--zoomup-file", type=Path, default=RIVER_MAP_DIR / "data/f06b_zoomup.csv")
    parser.add_argument("--plot-file", type=Path)
    parser.add_argument("--station-file", type=Path)
    parser.add_argument("--tile-cache", type=Path, default=Path.home() / ".cache/cmf_flood_osm_tiles")
    parser.add_argument("--no-osm", action="store_true")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    settings = json.loads(args.settings.read_text(encoding="utf-8"))["panel_a"]
    extent = tuple(settings["extent"])
    rows = common.read_csv(args.zoomup_file)
    zoom = next(row for row in rows if row["region_id"] == settings["zoom_region_id"])
    geometry, netcdf, segments, classes = common.read_network(args.map_dir, extent)
    lon, lat, raw = common.read_map_raster(netcdf / "basin.nc", "basin", "1", geometry)
    basin = raw.filled(np.nan)
    x_idx = np.flatnonzero((lon >= extent[0]) & (lon <= extent[2]))
    y_idx = np.flatnonzero((lat >= extent[1]) & (lat <= extent[3]))
    x_slice = slice(x_idx[0], x_idx[-1] + 1)
    y_slice = slice(y_idx.min(), y_idx.max() + 1)
    plot_lon, plot_lat = lon[x_slice], lat[y_slice]
    plot_basin = basin[y_slice, x_slice]
    target = np.isfinite(plot_basin) & (plot_basin == int(settings["target_basin_id"]))
    if not np.any(target):
        raise SystemExit(f"ERROR: Basin ID {settings['target_basin_id']} is absent from the f06a extent")

    fig, ax = plt.subplots(figsize=tuple(settings["figure_size"]))
    if not args.no_osm:
        common.draw_osm(ax, extent, args.tile_cache, settings["osm_alpha"], settings["osm_white_mix"])
    outside = np.ma.masked_where(target, np.ones(plot_basin.shape))
    ax.pcolormesh(
        common.cell_edges(plot_lon), common.cell_edges(plot_lat), outside,
        cmap=ListedColormap([settings["mask_color"]]), vmin=0, vmax=1,
        alpha=settings["mask_alpha"], shading="flat", linewidth=0, rasterized=True, zorder=1,
    )
    ax.contour(plot_lon, plot_lat, target.astype(np.uint8), levels=[0.5],
               colors=[settings["basin_outline_color"]], linewidths=0.7, zorder=2)
    west, south, east, north = (float(zoom[key]) for key in ("west", "south", "east", "north"))
    ax.add_patch(Rectangle(
        (west, south), east - west, north - south, fill=False,
        edgecolor=zoom["color"], linewidth=1.8, linestyle=zoom["linestyle"], zorder=2.5,
    ))
    ax.text(west + 0.06, south + 0.05, settings["zoom_label"], color=zoom["color"],
            fontsize=8, weight="bold", zorder=4,
            bbox=dict(facecolor="white", alpha=0.86, edgecolor="none", pad=2))
    common.draw_network(ax, segments, classes)
    domain_handles = []
    if settings.get("basin_legend_label"):
        domain_handles.append(Line2D(
            [0], [0], color=settings["basin_outline_color"], linewidth=1.2,
            label=settings["basin_legend_label"],
        ))
    for box in settings.get("domain_boxes", []):
        box_west, box_south, box_east, box_north = (
            float(box[key]) for key in ("west", "south", "east", "north")
        )
        ax.add_patch(Rectangle(
            (box_west, box_south), box_east - box_west, box_north - box_south,
            fill=False, edgecolor=box["color"], linewidth=2.0,
            linestyle=box.get("linestyle", "--"), zorder=4.4,
        ))
        ax.text(
            box_west + 0.08, box_north - 0.08, box["label"],
            color=box["color"], fontsize=8, weight="bold", va="top", zorder=6,
            bbox=dict(facecolor="white", alpha=0.86, edgecolor="none", pad=2),
        )
        domain_handles.append(Line2D(
            [0], [0], color=box["color"], linewidth=2.0,
            linestyle=box.get("linestyle", "--"), label=box["legend_label"],
        ))
    common.format_axes(ax, extent, settings["x_tick_interval"], settings["y_tick_interval"])
    point_rows = []
    for point_file in (args.plot_file, args.station_file):
        if point_file is not None:
            point_rows.extend(common.read_csv(point_file))
    point_handles, point_counts = common.draw_point_groups(
        ax, point_rows, settings.get("point_groups", {}), show_labels=False
    )
    if settings.get("extent_note"):
        ax.text(
            0.02, 0.02, settings["extent_note"], transform=ax.transAxes,
            ha="left", va="bottom", fontsize=7.5,
            bbox=dict(facecolor="white", alpha=0.88, edgecolor="none", pad=2), zorder=7,
        )
    if point_handles or domain_handles:
        ax.legend(handles=domain_handles + point_handles, loc="lower left",
                  fontsize=7.5, framealpha=0.9, borderpad=0.6)
    ax.set_title(settings["title"], fontsize=12)
    ax.text(0.01, 0.99, settings["subtitle"], transform=ax.transAxes,
            ha="left", va="top", fontsize=8,
            bbox=dict(facecolor="white", alpha=0.86, edgecolor="none", pad=2), zorder=5)
    common.draw_attribution(ax)
    common.save_figure(fig, args.output, int(settings["dpi"]))
    print(
        f"Basin mask styling: alpha={settings['mask_alpha']:.2f}; "
        f"Basin ID {settings['target_basin_id']} retained; {segments.shape[0]} network links loaded"
    )


if __name__ == "__main__":
    main()

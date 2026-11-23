#!/usr/bin/env python3
"""Draw a local OSM river map with event impact localities and candidate AOIs."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Rectangle

import f06_common as common

SCRIPT_DIR = Path(__file__).resolve().parent
RIVER_MAP_DIR = SCRIPT_DIR.parent


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--map-dir", type=Path, required=True)
    parser.add_argument("--settings", type=Path, default=RIVER_MAP_DIR / "data/f06_settings.json")
    parser.add_argument("--settings-section", default="panel_b",
                        help="Figure-specific settings key in the JSON file (default: panel_b)")
    parser.add_argument("--zoomup-file", type=Path, default=RIVER_MAP_DIR / "data/f06b_zoomup.csv")
    parser.add_argument("--plot-file", type=Path, default=RIVER_MAP_DIR / "data/f06b_plot.csv")
    parser.add_argument("--station-file", type=Path)
    parser.add_argument("--tile-cache", type=Path, default=Path.home() / ".cache/cmf_flood_osm_tiles")
    parser.add_argument("--no-osm", action="store_true")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    settings = json.loads(args.settings.read_text(encoding="utf-8"))[args.settings_section]
    zoom_rows = common.read_csv(args.zoomup_file)
    zoom = next(row for row in zoom_rows if row["region_id"] == settings["zoom_region_id"])
    extent = tuple(float(zoom[key]) for key in ("west", "south", "east", "north"))
    _, _, segments, classes = common.read_network(args.map_dir, extent)
    points = common.read_csv(args.plot_file)
    if args.station_file is not None:
        points.extend(common.read_csv(args.station_file))

    fig, ax = plt.subplots(figsize=tuple(settings["figure_size"]))
    if not args.no_osm:
        common.draw_osm(ax, extent, args.tile_cache, settings["osm_alpha"], settings["osm_white_mix"])
    region_handles = []
    if settings.get("show_aoi_boxes", True):
        for row in zoom_rows:
            if row["region_id"] == settings["zoom_region_id"]:
                continue
            west, south, east, north = (float(row[key]) for key in ("west", "south", "east", "north"))
            ax.add_patch(Rectangle(
                (west, south), east - west, north - south, fill=False,
                edgecolor=row["color"], linewidth=1.5, linestyle=row["linestyle"], zorder=2,
            ))
            ax.text(west + 0.04, north - 0.035, row["label"], color=row["color"],
                    fontsize=7.5, weight="bold", va="top", zorder=4,
                    bbox=dict(facecolor="white", alpha=0.84, edgecolor="none", pad=1.8))
            region_handles.append(Line2D([0], [0], color=row["color"], linewidth=1.5,
                                         linestyle=row["linestyle"], label=row["short_label"]))

    common.draw_network(ax, segments, classes)
    point_styles = {
        group: {
            "color": color,
            "label": settings["plot_group_labels"][group],
            "marker": "o",
            "size": 30,
        }
        for group, color in settings["plot_group_colors"].items()
    }
    for group, style in settings.get("additional_point_groups", {}).items():
        point_styles[group] = style
    common.format_axes(ax, extent, settings["x_tick_interval"], settings["y_tick_interval"])
    point_handles, point_counts = common.draw_point_groups(
        ax, points, point_styles, group_field=settings.get("point_group_field", "plot_group")
    )
    ax.legend(handles=point_handles + region_handles, loc="center left",
              bbox_to_anchor=(1.01, 0.5), fontsize=8, framealpha=0.9, borderpad=0.6,
              title=settings.get("legend_title"))
    ax.set_title(settings["title"] + "\n" + settings["subtitle"], fontsize=10)
    common.draw_attribution(ax)
    common.save_figure(fig, args.output, int(settings["dpi"]))
    print(f"Plotted in-extent point counts {point_counts}; AOI boxes: {settings.get('show_aoi_boxes', True)}")


if __name__ == "__main__":
    main()

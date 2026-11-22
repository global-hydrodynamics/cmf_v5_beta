#!/usr/bin/env python3
"""Summarize date-separated GFM STAC results and draw pass-footprint pages."""
from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime
from pathlib import Path
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Polygon, Rectangle

SCRIPT_DIR = Path(__file__).resolve().parent
TUTORIAL_DIR = SCRIPT_DIR.parent
REPO_ROOT = TUTORIAL_DIR.parents[1]
sys.path.insert(0, str(SCRIPT_DIR))
sys.path.insert(0, str(REPO_ROOT / "visualization/river_map/script"))
from gfm_common import parse_source
import f06_common as river


def polygon_rings(geometry):
    if geometry["type"] == "Polygon":
        return geometry["coordinates"]
    if geometry["type"] == "MultiPolygon":
        return [ring for polygon in geometry["coordinates"] for ring in polygon]
    raise ValueError(f"Unsupported STAC footprint geometry: {geometry['type']}")


def clip_edge(points, inside, intersection):
    output = []
    if not points:
        return output
    previous = points[-1]
    previous_inside = inside(previous)
    for current in points:
        current_inside = inside(current)
        if current_inside:
            if not previous_inside:
                output.append(intersection(previous, current))
            output.append(current)
        elif previous_inside:
            output.append(intersection(previous, current))
        previous, previous_inside = current, current_inside
    return output


def clipped_area(ring, west, south, east, north):
    points = [(float(x), float(y)) for x, y, *_ in ring]
    edges = [
        (lambda p: p[0] >= west, lambda a, b: (west, a[1] + (b[1] - a[1]) * (west - a[0]) / (b[0] - a[0]))),
        (lambda p: p[0] <= east, lambda a, b: (east, a[1] + (b[1] - a[1]) * (east - a[0]) / (b[0] - a[0]))),
        (lambda p: p[1] >= south, lambda a, b: (a[0] + (b[0] - a[0]) * (south - a[1]) / (b[1] - a[1]), south)),
        (lambda p: p[1] <= north, lambda a, b: (a[0] + (b[0] - a[0]) * (north - a[1]) / (b[1] - a[1]), north)),
    ]
    for inside, intersection in edges:
        points = clip_edge(points, inside, intersection)
    if len(points) < 3:
        return 0.0
    return abs(sum(
        points[i][0] * points[(i + 1) % len(points)][1]
        - points[(i + 1) % len(points)][0] * points[i][1]
        for i in range(len(points))
    )) / 2.0


def footprint_overlaps(geometry, extent):
    west, south, east, north = extent
    return any(clipped_area(ring, west, south, east, north) > 1e-10
               for ring in polygon_rings(geometry))


def load_passes(catalogue_root, extent):
    groups = {}
    for catalogue in sorted(catalogue_root.glob("*/metadata/stac_items.json")):
        data = json.loads(catalogue.read_text(encoding="utf-8"))
        for item in data["features"]:
            source = parse_source(item)
            group = groups.setdefault(source["pass_id"], {
                "pass_id": source["pass_id"],
                "platform": source["platform"],
                "absolute_orbit": source["absolute_orbit"],
                "datatake": source["datatake"],
                "items": {},
            })
            group["items"][item["id"]] = item

    passes = []
    for group in groups.values():
        items = list(group["items"].values())
        starts = [datetime.fromisoformat(parse_source(item)["start_utc"]) for item in items]
        ends = [datetime.fromisoformat(parse_source(item)["end_utc"]) for item in items]
        overlapping = [item for item in items if footprint_overlaps(item["geometry"], extent)]
        group.update(
            start_utc=min(starts).isoformat().replace("+00:00", "Z"),
            end_utc=max(ends).isoformat().replace("+00:00", "Z"),
            item_count=len(items),
            aoi_overlap_items=len(overlapping),
            aoi_overlap="yes" if overlapping else "no",
            items=sorted(items, key=lambda item: (item["properties"]["datetime"], item["id"])),
        )
        passes.append(group)
    return sorted(passes, key=lambda item: (item["start_utc"], item["pass_id"]))


def read_orbit_lookup(path):
    if not path.exists():
        return {}
    with path.open(newline="", encoding="utf-8") as stream:
        return {row["pass_id"]: row for row in csv.DictReader(stream)}


def write_inventory(passes, path, orbit_metadata):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=[
            "pass_id", "satellite", "absolute_orbit", "relative_orbit",
            "orbit_direction", "datatake", "start_utc", "end_utc",
            "stac_item_count", "items_overlapping_candidate_aoi", "aoi_overlap",
            "item_ids", "review_status",
        ], lineterminator="\n")
        writer.writeheader()
        for group in passes:
            writer.writerow({
                "pass_id": group["pass_id"],
                "satellite": group["platform"],
                "absolute_orbit": group["absolute_orbit"],
                "relative_orbit": orbit_metadata.get(group["pass_id"], {}).get(
                    "relative_orbit", "not in GFM STAC metadata"
                ),
                "orbit_direction": orbit_metadata.get(group["pass_id"], {}).get(
                    "orbit_direction", "not in GFM STAC metadata"
                ),
                "datatake": group["datatake"],
                "start_utc": group["start_utc"],
                "end_utc": group["end_utc"],
                "stac_item_count": group["item_count"],
                "items_overlapping_candidate_aoi": group["aoi_overlap_items"],
                "aoi_overlap": group["aoi_overlap"],
                "item_ids": ";".join(item["id"] for item in group["items"]),
                "review_status": "candidate for researcher review",
            })


def draw_pages(passes, map_dir, view_extent, aoi_extent, tile_cache, output_dir, no_osm):
    _, _, segments, classes = river.read_network(map_dir, view_extent)
    output_dir.mkdir(parents=True, exist_ok=True)
    page_size = 6
    page_count = (len(passes) + page_size - 1) // page_size
    for page_index in range(page_count):
        page = passes[page_index * page_size:(page_index + 1) * page_size]
        fig, axes = plt.subplots(2, 3, figsize=(15, 10), squeeze=False)
        fig.suptitle(
            "GFM STAC footprints by acquisition pass\n"
            f"Candidate satellite analysis domain: {aoi_extent[0]}–{aoi_extent[2]}°E, "
            f"{aoi_extent[1]}–{aoi_extent[3]}°N · page {page_index + 1}/{page_count}",
            fontsize=14, y=0.985,
        )
        for axis_index, ax in enumerate(axes.flat):
            if axis_index >= len(page):
                ax.set_visible(False)
                continue
            group = page[axis_index]
            if not no_osm:
                river.draw_osm(ax, view_extent, tile_cache, alpha=0.78, white_mix=0.32)
            for item in group["items"]:
                for ring in polygon_rings(item["geometry"]):
                    ax.add_patch(Polygon(
                        [(float(x), float(y)) for x, y, *_ in ring],
                        closed=True, facecolor="#20a08b", edgecolor="#087568",
                        linewidth=0.65, alpha=0.24, zorder=1.5,
                    ))
            west, south, east, north = aoi_extent
            ax.add_patch(Rectangle(
                (west, south), east - west, north - south,
                fill=False, edgecolor="#dc7a12", linewidth=1.8,
                linestyle="--", zorder=2.4,
            ))
            river.draw_network(ax, segments, classes)
            river.format_axes(ax, view_extent, 1.0, 1.0)
            ax.tick_params(labelsize=7)
            start = datetime.fromisoformat(group["start_utc"].replace("Z", "+00:00"))
            end = datetime.fromisoformat(group["end_utc"].replace("Z", "+00:00"))
            ax.set_title(
                f"{start:%Y-%m-%d} · {group['platform']} · {group['pass_id']}\n"
                f"{start:%H:%M:%S}–{end:%H:%M:%S} UTC · {group['item_count']} Items · "
                f"AOI-intersecting Items: {group['aoi_overlap_items']}",
                fontsize=8.1, pad=5,
            )
            river.draw_attribution(ax)
        legend = [
            Line2D([0], [0], color="#2d6291", linewidth=1.4, label="CaMa-Flood river network"),
            Rectangle((0, 0), 1, 1, facecolor="#20a08b", edgecolor="#087568", alpha=0.24,
                      label="STAC product footprint (catalogue geometry)"),
            Line2D([0], [0], color="#dc7a12", linewidth=1.8, linestyle="--",
                   label="Candidate satellite analysis domain"),
        ]
        fig.legend(handles=legend, loc="lower center", ncol=3, frameon=True,
                   fontsize=9, bbox_to_anchor=(0.5, 0.018))
        fig.text(
            0.5, 0.055,
            "STAC footprints show catalogue product coverage, not valid flood-observation pixels.",
            ha="center", fontsize=9,
        )
        fig.subplots_adjust(left=0.07, right=0.98, top=0.90, bottom=0.12,
                            wspace=0.25, hspace=0.32)
        output = output_dir / f"f03a-gfm-pass-footprints-{page_index + 1:02d}.png"
        river.save_figure(fig, output, 180)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--domain-config", type=Path,
                        default=TUTORIAL_DIR / "metadata/domain_selection.json")
    parser.add_argument("--catalogue-root", type=Path,
                        default=TUTORIAL_DIR / "Atlantis/catalogue")
    parser.add_argument("--summary-dir", type=Path,
                        default=TUTORIAL_DIR / "Atlantis/summary")
    parser.add_argument("--inventory-output", type=Path,
                        default=TUTORIAL_DIR / "metadata/satellite_pass_inventory.csv")
    parser.add_argument("--orbit-metadata", type=Path,
                        default=TUTORIAL_DIR / "metadata/satellite_orbit_metadata.csv")
    parser.add_argument("--map-dir", type=Path, default=REPO_ROOT / "map/glb_15min")
    parser.add_argument("--tile-cache", type=Path,
                        default=Path.home() / ".cache/cmf_flood_osm_tiles")
    parser.add_argument("--figure-dir", type=Path, default=TUTORIAL_DIR / "figure")
    parser.add_argument("--no-osm", action="store_true")
    args = parser.parse_args()
    config = json.loads(args.domain_config.read_text(encoding="utf-8"))
    aoi_extent = tuple(config["satellite_analysis"]["domain"]["bbox_west_south_east_north"])
    view_margin = 0.5
    view_extent = (
        aoi_extent[0] - view_margin, aoi_extent[1] - view_margin,
        aoi_extent[2] + view_margin, aoi_extent[3] + view_margin,
    )
    passes = load_passes(args.catalogue_root, aoi_extent)
    if not passes:
        raise SystemExit("No STAC items found in the configured catalogue directories")
    args.summary_dir.mkdir(parents=True, exist_ok=True)
    write_inventory(passes, args.inventory_output, read_orbit_lookup(args.orbit_metadata))
    features = []
    for group in passes:
        for item in group["items"]:
            features.append({
                "type": "Feature", "geometry": item["geometry"],
                "properties": {
                    "pass_id": group["pass_id"], "platform": group["platform"],
                    "absolute_orbit": group["absolute_orbit"],
                    "datatake": group["datatake"], "item_id": item["id"],
                    "datetime": item["properties"]["datetime"],
                    "candidate_aoi_overlap": footprint_overlaps(item["geometry"], aoi_extent),
                },
            })
    (args.summary_dir / "gfm_pass_footprints.geojson").write_text(
        json.dumps({"type": "FeatureCollection", "features": features}, indent=2) + "\n",
        encoding="utf-8",
    )
    draw_pages(passes, args.map_dir, view_extent, aoi_extent, args.tile_cache,
               args.figure_dir, args.no_osm)
    print(f"Summarized {sum(p['item_count'] for p in passes)} STAC Items into {len(passes)} acquisition passes")


if __name__ == "__main__":
    main()

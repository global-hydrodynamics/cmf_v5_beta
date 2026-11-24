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
from matplotlib.patches import PathPatch, Rectangle
from matplotlib.path import Path as MatplotlibPath

SCRIPT_DIR = Path(__file__).resolve().parent
TUTORIAL_DIR = SCRIPT_DIR.parent
REPO_ROOT = TUTORIAL_DIR.parents[1]
sys.path.insert(0, str(SCRIPT_DIR))
sys.path.insert(0, str(REPO_ROOT / "visualization/river_map/script"))
from event_gfm_common import parse_source
import f06_common as river


def polygon_rings(geometry):
    if geometry["type"] == "Polygon":
        return geometry["coordinates"]
    if geometry["type"] == "MultiPolygon":
        return [ring for polygon in geometry["coordinates"] for ring in polygon]
    raise ValueError(f"Unsupported STAC footprint geometry: {geometry['type']}")


def source_product_id(item):
    """Return the Sentinel-1 product ID linked by the GFM STAC Item."""
    href = next((link.get("href") for link in item.get("links", [])
                 if link.get("rel") == "derived_from"), None)
    if not href:
        raise ValueError(f"GFM Item has no derived_from source product: {item['id']}")
    return href.rsplit("/", 1)[-1]


def compound_path(geometries):
    """Build one filled Matplotlib path so overlaps receive alpha only once."""
    vertices = []
    codes = []
    for geometry in geometries:
        polygons = (geometry["coordinates"] if geometry["type"] == "MultiPolygon"
                    else [geometry["coordinates"]])
        for polygon in polygons:
            # Sentinel-1 acquisition GeoFootprints in this survey have no holes.
            ring = polygon[0]
            points = [(float(x), float(y)) for x, y, *_ in ring]
            if len(points) < 4:
                continue
            vertices.extend(points)
            codes.extend([MatplotlibPath.MOVETO]
                         + [MatplotlibPath.LINETO] * (len(points) - 2)
                         + [MatplotlibPath.CLOSEPOLY])
    if not vertices:
        raise ValueError("No polygon coordinates found for acquisition pass")
    return MatplotlibPath(vertices, codes)


def load_acquisition_footprints(path):
    data = json.loads(path.read_text(encoding="utf-8"))
    return {
        feature["properties"]["source_product_id"]: feature["geometry"]
        for feature in data["features"]
    }


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


def load_passes(catalogue_root, extent, start_date, end_date):
    groups = {}
    for catalogue in sorted(catalogue_root.glob("*/metadata/stac_items.json")):
        catalogue_date = catalogue.parent.parent.name
        if not start_date <= catalogue_date <= end_date:
            continue
        data = json.loads(catalogue.read_text(encoding="utf-8"))
        for item in data["features"]:
            source = parse_source(item)
            group = groups.setdefault(source["pass_id"], {
                "pass_id": source["pass_id"],
                "platform": source["platform"],
                "absolute_orbit": source["absolute_orbit"],
                "datatake": source["datatake"],
                "items": {},
                "source_product_ids": set(),
                "equi7_tiles": set(),
            })
            group["items"][item["id"]] = item
            group["source_product_ids"].add(source_product_id(item))
            tile = item.get("properties", {}).get("Equi7Tile")
            if tile:
                group["equi7_tiles"].add(tile)

    passes = []
    for group in groups.values():
        items = list(group["items"].values())
        starts = [datetime.fromisoformat(parse_source(item)["start_utc"]) for item in items]
        ends = [datetime.fromisoformat(parse_source(item)["end_utc"]) for item in items]
        overlapping = [item for item in items if footprint_overlaps(item["geometry"], extent)]
        tile_geometries = {json.dumps(item["geometry"], sort_keys=True) for item in items}
        group.update(
            start_utc=min(starts).isoformat().replace("+00:00", "Z"),
            end_utc=max(ends).isoformat().replace("+00:00", "Z"),
            item_count=len(items),
            source_product_ids=sorted(group["source_product_ids"]),
            source_product_count=len(group["source_product_ids"]),
            equi7_tiles=sorted(group["equi7_tiles"]),
            equi7_tile_count=len(group["equi7_tiles"]),
            distinct_stac_geometries=len(tile_geometries),
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


def source_metadata(catalogue_root, passes):
    """Collect source-product geometry and orbit attributes cached by s01."""
    source_ids = {source_id for group in passes for source_id in group["source_product_ids"]}
    products_by_source = {source_id: [] for source_id in source_ids}
    response_files = sorted(catalogue_root.glob("*/metadata/orbit_*.json"))
    response_files += sorted(catalogue_root.glob("source_products_by_date/*.json"))
    for path in response_files:
        response = json.loads(path.read_text(encoding="utf-8"))
        products = response.get("products", response.get("value", []))
        for product in products:
            name = product.get("Name", "")
            for source_id in source_ids:
                if name.startswith(source_id):
                    products_by_source[source_id].append(product)

    footprints = {}
    orbit_metadata = {}
    features = []
    for group in passes:
        pass_products = []
        for source_id in group["source_product_ids"]:
            candidates = products_by_source[source_id]
            if not candidates:
                raise ValueError(f"No Copernicus OData metadata cached for {source_id}; rerun s03a")
            product = sorted(candidates, key=lambda item: "_COG" in item["Name"])[0]
            geometry = product.get("GeoFootprint")
            if not geometry:
                raise ValueError(f"No GeoFootprint in Copernicus metadata for {source_id}")
            attributes = {item["Name"]: item["Value"] for item in product.get("Attributes", [])}
            footprints[source_id] = geometry
            pass_products.append((source_id, product, attributes))
            content_date = product.get("ContentDate", {})
            features.append({
                "type": "Feature",
                "id": source_id,
                "geometry": geometry,
                "properties": {
                    "source_product_id": source_id,
                    "catalogue_product_name": product["Name"],
                    "acquisition_start_utc": content_date.get("Start", ""),
                    "acquisition_end_utc": content_date.get("End", ""),
                    "satellite": group["platform"],
                    "absolute_orbit": group["absolute_orbit"],
                    "relative_orbit": attributes.get("relativeOrbitNumber"),
                    "orbit_direction": attributes.get("orbitDirection"),
                    "geometry_source": "Copernicus Data Space OData Products.GeoFootprint (SRID 4326)",
                    "source_item_href": next(
                        link["href"]
                        for item in group["items"]
                        for link in item.get("links", [])
                        if link.get("rel") == "derived_from"
                        and link["href"].rstrip("/").rsplit("/", 1)[-1] == source_id
                    ),
                },
            })
        relative = {str(attributes.get("relativeOrbitNumber")) for _, _, attributes in pass_products}
        directions = {str(attributes.get("orbitDirection")) for _, _, attributes in pass_products}
        if len(relative) != 1 or len(directions) != 1:
            raise ValueError(f"Conflicting or missing Copernicus orbit attributes for {group['pass_id']}")
        orbit_metadata[group["pass_id"]] = {
            "relative_orbit": next(iter(relative)),
            "orbit_direction": next(iter(directions)),
        }
    return orbit_metadata, footprints, features


def write_source_metadata(orbit_metadata, footprints_features, orbit_path, footprint_path):
    orbit_path.parent.mkdir(parents=True, exist_ok=True)
    with orbit_path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(
            stream, fieldnames=["pass_id", "relative_orbit", "orbit_direction", "source"],
            lineterminator="\n",
        )
        writer.writeheader()
        for pass_id, values in sorted(orbit_metadata.items()):
            writer.writerow({
                "pass_id": pass_id,
                **values,
                "source": "Copernicus Data Space OData source product Attributes",
            })
    footprint_path.write_text(
        json.dumps({"type": "FeatureCollection", "features": footprints_features}, indent=2) + "\n",
        encoding="utf-8",
    )


def write_inventory(passes, path, orbit_metadata, acquisition_footprints, extent):
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "pass_id", "satellite", "absolute_orbit", "relative_orbit",
        "orbit_direction", "datatake", "start_utc", "end_utc",
        "stac_item_count", "equi7_tile_count", "distinct_stac_tile_geometries",
        "source_product_count", "items_overlapping_candidate_aoi",
        "source_products_overlapping_candidate_aoi", "stac_item_aoi_overlap",
        "source_footprint_aoi_overlap",
        "item_ids", "equi7_tile_ids", "source_product_ids", "footprint_geometry_source",
        "review_status",
    ]
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        for group in passes:
            orbit = orbit_metadata.get(group["pass_id"], {})
            source_ids = group["source_product_ids"]
            missing = [source_id for source_id in source_ids if source_id not in acquisition_footprints]
            if missing:
                raise ValueError(f"Acquisition footprint metadata missing for {group['pass_id']}: {missing}")
            source_overlap_count = sum(
                footprint_overlaps(acquisition_footprints[source_id], extent)
                for source_id in source_ids
            )
            writer.writerow({
                "pass_id": group["pass_id"],
                "satellite": group["platform"],
                "absolute_orbit": group["absolute_orbit"],
                "relative_orbit": orbit.get("relative_orbit", "not in Copernicus metadata"),
                "orbit_direction": orbit.get("orbit_direction", "not in Copernicus metadata"),
                "datatake": group["datatake"],
                "start_utc": group["start_utc"],
                "end_utc": group["end_utc"],
                "stac_item_count": group["item_count"],
                "equi7_tile_count": group["equi7_tile_count"],
                "distinct_stac_tile_geometries": group["distinct_stac_geometries"],
                "source_product_count": group["source_product_count"],
                "items_overlapping_candidate_aoi": group["aoi_overlap_items"],
                "source_products_overlapping_candidate_aoi": source_overlap_count,
                "stac_item_aoi_overlap": group["aoi_overlap"],
                "source_footprint_aoi_overlap": "yes" if source_overlap_count else "no",
                "item_ids": ";".join(item["id"] for item in group["items"]),
                "equi7_tile_ids": ";".join(group["equi7_tiles"]),
                "source_product_ids": ";".join(source_ids),
                "footprint_geometry_source": "Copernicus Data Space OData GeoFootprint (source GRD SAFE)",
                "review_status": "candidate for researcher review",
            })


def draw_pages(passes, acquisition_footprints, orbit_metadata, map_dir, view_extent,
               aoi_extent, tile_cache, output_dir, no_osm, fig_width=15, fig_height=10, dpi=180, period_title=None):
    _, _, segments, classes = river.read_network(map_dir, view_extent)
    output_dir.mkdir(parents=True, exist_ok=True)
    page_size = 6
    page_count = (len(passes) + page_size - 1) // page_size
    expected_outputs = {
        f"f03a-gfm-pass-footprints-{page_index + 1:02d}.png"
        for page_index in range(page_count)
    }
    for page_index in range(page_count):
        page = passes[page_index * page_size:(page_index + 1) * page_size]
        fig, axes = plt.subplots(2, 3, figsize=(fig_width, fig_height), squeeze=False)
        fig.suptitle(
            (period_title or "Original Sentinel-1 acquisition footprints by pass · 14–16 July 2021\nCentered on 15 July disaster date · candidate domain: ")
            + f"{aoi_extent[0]}–{aoi_extent[2]}°E, {aoi_extent[1]}–{aoi_extent[3]}°N · "
            f"page {page_index + 1}/{page_count}",
            fontsize=14, y=0.985,
        )
        for axis_index, ax in enumerate(axes.flat):
            if axis_index >= len(page):
                ax.set_visible(False)
                continue
            group = page[axis_index]
            if not no_osm:
                river.draw_osm(ax, view_extent, tile_cache, alpha=0.78, white_mix=0.32)
            geometries = [acquisition_footprints[source_id]
                          for source_id in group["source_product_ids"]]
            # One compound fill per pass prevents overlaps between adjacent source slices
            # from appearing darker or implying a second observation.
            ax.add_patch(PathPatch(
                compound_path(geometries), facecolor="#20a08b", edgecolor="none",
                alpha=0.34, zorder=1.5,
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
            orbit = orbit_metadata.get(group["pass_id"], {})
            direction = orbit.get("orbit_direction", "Unknown").upper()
            direction = {"ASCENDING": "ASC", "DESCENDING": "DESC"}.get(direction, direction)
            ax.set_title(
                f"{start:%Y-%m-%d} · {group['platform']} · {direction}\n"
                f"{group['pass_id']}\n"
                f"{start:%H:%M:%S}–{end:%H:%M:%S} UTC · {group['item_count']} STAC / "
                f"{group['source_product_count']} source / {group['equi7_tile_count']} tiles",
                fontsize=7.0, pad=4,
            )
            river.draw_attribution(ax)
        legend = [
            Line2D([0], [0], color="#2d6291", linewidth=1.4, label="CaMa-Flood river network"),
            Rectangle((0, 0), 1, 1, facecolor="#20a08b", edgecolor="none", alpha=0.34,
                      label="Sentinel-1 source GRD acquisition footprint"),
            Line2D([0], [0], color="#dc7a12", linewidth=1.8, linestyle="--",
                   label="Candidate satellite analysis domain"),
        ]
        fig.legend(handles=legend, loc="lower center", ncol=3, frameon=True,
                   fontsize=9, bbox_to_anchor=(0.5, 0.018))
        fig.text(
            0.5, 0.055,
            "Copernicus Data Space product GeoFootprints; one uniform fill per pass, not GFM valid flood pixels.",
            ha="center", fontsize=9,
        )
        fig.subplots_adjust(left=0.07, right=0.98, top=0.90, bottom=0.12,
                            wspace=0.25, hspace=0.32)
        output = output_dir / f"f03a-gfm-pass-footprints-{page_index + 1:02d}.png"
        river.save_figure(fig, output, dpi)
    for stale in output_dir.glob("f03a-gfm-pass-footprints-*.png"):
        if stale.name not in expected_outputs:
            stale.unlink()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=["metadata", "figure"], required=True,
                        help="metadata: summarize cached STAC/OData; figure: render existing metadata only")
    parser.add_argument("--domain-config", type=Path,
                        default=TUTORIAL_DIR / "metadata/02_domain_selection.json")
    parser.add_argument("--catalogue-root", type=Path,
                        default=TUTORIAL_DIR / "Atlantis/catalogue")
    parser.add_argument("--summary-dir", type=Path,
                        default=TUTORIAL_DIR / "Atlantis/summary")
    parser.add_argument("--inventory-output", type=Path,
                        default=TUTORIAL_DIR / "metadata/03a_satellite_pass_inventory.csv")
    parser.add_argument("--orbit-metadata", type=Path,
                        default=TUTORIAL_DIR / "metadata/03a_satellite_orbit_metadata.csv")
    parser.add_argument("--acquisition-footprints", type=Path,
                        default=TUTORIAL_DIR / "metadata/03a_sentinel1_acquisition_footprints.geojson")
    parser.add_argument("--map-dir", type=Path, default=REPO_ROOT / "map/glb_15min")
    parser.add_argument("--tile-cache", type=Path,
                        default=Path.home() / ".cache/cmf_flood_osm_tiles")
    parser.add_argument("--figure-dir", type=Path, default=TUTORIAL_DIR / "figure")
    parser.add_argument("--no-osm", action="store_true")
    parser.add_argument("--fig-width", type=float, default=15)
    parser.add_argument("--fig-height", type=float, default=10)
    parser.add_argument("--dpi", type=int, default=180)
    args = parser.parse_args()
    config = json.loads(args.domain_config.read_text(encoding="utf-8"))
    aoi_extent = tuple(config["satellite_analysis"]["domain"]["bbox_west_south_east_north"])
    view_margin = 0.5
    view_extent = (
        aoi_extent[0] - view_margin, aoi_extent[1] - view_margin,
        aoi_extent[2] + view_margin, aoi_extent[3] + view_margin,
    )
    search_period = config["satellite_analysis"]["search_period"]
    passes = load_passes(
        args.catalogue_root, aoi_extent,
        search_period["start_date"], search_period["end_date"],
    )
    if not passes:
        raise SystemExit("No cached STAC items in the configured date range; run s03a-satellite_availability.sh first")
    if args.mode == "metadata":
        orbit_metadata, acquisition_footprints, source_features = source_metadata(args.catalogue_root, passes)
        write_source_metadata(orbit_metadata, source_features,
                              args.orbit_metadata, args.acquisition_footprints)
    else:
        if not args.orbit_metadata.is_file() or not args.acquisition_footprints.is_file():
            raise SystemExit("Step 3a metadata is missing; run s03a-satellite_availability.sh first")
        acquisition_footprints = load_acquisition_footprints(args.acquisition_footprints)
        orbit_metadata = read_orbit_lookup(args.orbit_metadata)
        missing_passes = sorted({group["pass_id"] for group in passes} - orbit_metadata.keys())
        if missing_passes:
            raise SystemExit(
                "Step 3a orbit metadata is missing for " + ", ".join(missing_passes)
                + "; run s03a-satellite_availability.sh first"
            )
    missing = sorted({source_id for group in passes for source_id in group["source_product_ids"]}
                     - acquisition_footprints.keys())
    if missing:
        raise SystemExit(
            "No Copernicus acquisition GeoFootprint metadata for source product(s): "
            + ", ".join(missing)
            + f"\nUpdate {args.acquisition_footprints} from Copernicus Data Space OData metadata; "
              "GFM tile geometry is not used as a substitute."
        )
    if args.mode == "metadata":
        args.summary_dir.mkdir(parents=True, exist_ok=True)
        write_inventory(passes, args.inventory_output, orbit_metadata,
                        acquisition_footprints, aoi_extent)
        features = []
        for group in passes:
            for item in group["items"]:
                features.append({
                    "type": "Feature", "geometry": item["geometry"],
                    "properties": {
                        "pass_id": group["pass_id"], "platform": group["platform"],
                        "absolute_orbit": group["absolute_orbit"],
                        "datatake": group["datatake"], "item_id": item["id"],
                        "source_product_id": source_product_id(item),
                        "equi7_tile": item.get("properties", {}).get("Equi7Tile", ""),
                        "datetime": item["properties"]["datetime"],
                        "candidate_aoi_overlap": footprint_overlaps(item["geometry"], aoi_extent),
                        "geometry_meaning": "GFM Equi7 tile product coverage, not source acquisition footprint",
                    },
                })
        (args.summary_dir / "gfm_pass_footprints.geojson").write_text(
            json.dumps({"type": "FeatureCollection", "features": features}, indent=2) + "\n",
            encoding="utf-8",
        )
    else:
        draw_pages(passes, acquisition_footprints, orbit_metadata, args.map_dir, view_extent,
                   aoi_extent, args.tile_cache, args.figure_dir, args.no_osm, args.fig_width, args.fig_height, args.dpi,
                   None if (search_period["start_date"], search_period["end_date"]) == ("2021-07-14", "2021-07-16") else
                   f"Original Sentinel-1 acquisition footprints by pass · {search_period['start_date']}–{search_period['end_date']}\nCandidate domain: ")
    source_count = sum(group["source_product_count"] for group in passes)
    print(f"Summarized {sum(p['item_count'] for p in passes)} STAC Items into "
          f"{len(passes)} acquisition passes and {source_count} source product slices")



if __name__ == "__main__":
    main()

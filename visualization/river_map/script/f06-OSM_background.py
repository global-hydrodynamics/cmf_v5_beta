#!/usr/bin/env python3
"""Render p01-f06 OSM_background: CaMa outlet links over OSM Standard."""
from __future__ import annotations

import argparse
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
import numpy as np
from PIL import Image
import rasterio
from rasterio.transform import from_bounds, from_origin
from rasterio.warp import reproject, Resampling

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))
_F03_PATH = SCRIPT_DIR / "f03a-vector_river_map-upstream_area.py"
_spec = spec_from_file_location("f03a_vector_river_map", _F03_PATH)
_f03 = module_from_spec(_spec)
_spec.loader.exec_module(_f03)
from river_map_common import validate_extent

OSM_URL = "https://tile.openstreetmap.org/{z}/{x}/{y}.png"
OSM_ATTRIBUTION = "© OpenStreetMap contributors · openstreetmap.org/copyright"
USER_AGENT = "CaMaFloodMapExplorerGallery/1.0 (https://github.com/global-hydrodynamics/cmf_v5_beta)"
DEFAULT_EXTENT = (3.0, 46.0, 12.0, 53.0)


def arguments():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--map-dir", type=Path, required=True,
                        help="CaMa-Flood map root containing params.txt and netcdf/")
    parser.add_argument("--west", type=float, default=DEFAULT_EXTENT[0])
    parser.add_argument("--south", type=float, default=DEFAULT_EXTENT[1])
    parser.add_argument("--east", type=float, default=DEFAULT_EXTENT[2])
    parser.add_argument("--north", type=float, default=DEFAULT_EXTENT[3])
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--osm", dest="osm", action="store_true", default=True,
                       help="Add OSM Standard background (default)")
    group.add_argument("--no-osm", dest="osm", action="store_false",
                       help="Render the river network alone")
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


def main():
    args = arguments()
    map_dir = args.map_dir.expanduser().resolve()
    extent = (args.west, args.south, args.east, args.north)
    if not (args.west < args.east and args.south < args.north):
        raise SystemExit("ERROR: bbox requires west < east and south < north")
    geometry = _f03.read_geometry(map_dir / "params.txt")
    validate_extent(args.west, args.east, args.south, args.north, geometry)
    netcdf = map_dir / "netcdf"
    (_, source_lon, source_lat, destination_lon, destination_lat,
     _, area_classes, _, _, _) = _f03.read_network(
        netcdf / "uparea.nc", netcdf / "nextxy.nc", netcdf / "lonlat.nc", map_dir / "params.txt"
    )

    inside = (
        (source_lon >= args.west) & (source_lon <= args.east) &
        (source_lat >= args.south) & (source_lat <= args.north) &
        (destination_lon >= args.west) & (destination_lon <= args.east) &
        (destination_lat >= args.south) & (destination_lat <= args.north)
    )
    segments = np.stack((
        np.column_stack((source_lon[inside], source_lat[inside])),
        np.column_stack((destination_lon[inside], destination_lat[inside])),
    ), axis=1)
    selected_classes = area_classes[inside]

    fig, ax = plt.subplots(figsize=(10.2, 7.8))
    ax.set_xlim(args.west, args.east)
    ax.set_ylim(args.south, args.north)
    ax.set_aspect(1.0 / math.cos(math.radians((args.south + args.north) / 2.0)))
    osm_loaded = False
    if args.osm:
        try:
            image = read_osm(extent, args.tile_cache.expanduser())
            ax.imshow(image, extent=(args.west, args.east, args.south, args.north), origin="upper", zorder=0)
            osm_loaded = True
        except (OSError, URLError, TimeoutError, ValueError) as exc:
            print(f"WARNING: OSM tile unavailable; rendering the river network only: {exc}")

    for area_class, (color, width) in enumerate(zip(_f03.AREA_COLORS, _f03.AREA_WIDTHS)):
        selected = selected_classes == area_class
        if np.any(selected):
            ax.add_collection(LineCollection(
                segments[selected], colors=color, linewidths=width * 72 * 0.55,
                alpha=0.94, zorder=2 + area_class * 0.1, capstyle="round",
            ))
    if osm_loaded:
        ax.text(.995, .012, OSM_ATTRIBUTION, transform=ax.transAxes,
                ha="right", va="bottom", fontsize=7, color="#333333",
                bbox=dict(facecolor="white", alpha=.82, edgecolor="none", pad=2), zorder=5)
    ax.set_axis_off()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(args.output, dpi=args.dpi, bbox_inches="tight", pad_inches=0, facecolor="white")
    plt.close(fig)
    print(f"Wrote {args.output}: {int(inside.sum())} CaMa outlet links; bbox={list(extent)}")


if __name__ == "__main__":
    main()

"""Shared OSM and CaMa-Flood drawing helpers for River Map f06 panels."""
from __future__ import annotations

from importlib.util import module_from_spec, spec_from_file_location
import math
from pathlib import Path
import sys
import time
from urllib.error import URLError
from urllib.request import Request, urlopen

import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
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


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as source:
        import csv
        return list(csv.DictReader(source))


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


def draw_osm(ax, extent, cache: Path, alpha: float, white_mix: float) -> bool:
    """Draw softened OSM tiles; return False and continue with vectors if unavailable."""
    try:
        image = read_osm(extent, cache.expanduser())
        image = np.asarray(Image.blend(
            Image.fromarray(image), Image.new("RGB", (image.shape[1], image.shape[0]), "white"), white_mix
        ))
    except (OSError, URLError, TimeoutError, ValueError) as exc:
        print(f"WARNING: OSM tiles unavailable; continuing with CaMa layers: {exc}")
        return False
    west, south, east, north = extent
    ax.imshow(image, extent=(west, east, south, north), origin="upper", alpha=alpha, zorder=0)
    print(f"OSM styling: alpha={alpha:.2f}, white blend={white_mix:.2f}")
    return True


def read_network(map_dir: Path, extent):
    geometry = _f03.read_geometry(map_dir / "params.txt")
    validate_extent(extent[0], extent[2], extent[1], extent[3], geometry)
    netcdf = map_dir / "netcdf"
    (_, source_lon, source_lat, destination_lon, destination_lat,
     _, area_classes, _, _, _) = _f03.read_network(
        netcdf / "uparea.nc", netcdf / "nextxy.nc", netcdf / "lonlat.nc", map_dir / "params.txt"
    )
    west, south, east, north = extent
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
    return geometry, netcdf, segments, area_classes[inside]


def draw_network(ax, segments, classes):
    for area_class, (color, width) in enumerate(zip(_f03.AREA_COLORS, _f03.AREA_WIDTHS)):
        selected = classes == area_class
        if np.any(selected):
            ax.add_collection(LineCollection(
                segments[selected], colors=color, linewidths=width * 72 * 0.55,
                alpha=0.96, zorder=3 + area_class * 0.1, capstyle="round",
            ))


def draw_attribution(ax):
    ax.text(.995, .012, OSM_ATTRIBUTION, transform=ax.transAxes,
            ha="right", va="bottom", fontsize=7, color="#333333",
            bbox=dict(facecolor="white", alpha=.82, edgecolor="none", pad=2), zorder=10)


def format_axes(ax, extent, x_interval: float, y_interval: float):
    from matplotlib.ticker import MultipleLocator
    west, south, east, north = extent
    ax.set_xlim(west, east)
    ax.set_ylim(south, north)
    ax.set_aspect(1.0 / math.cos(math.radians((south + north) / 2.0)))
    ax.xaxis.set_major_locator(MultipleLocator(x_interval))
    ax.yaxis.set_major_locator(MultipleLocator(y_interval))
    ax.set_xlabel("Longitude [°E]")
    ax.set_ylabel("Latitude [°N]")
    ax.tick_params(direction="out", length=4, labelsize=9)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)


def cell_edges(centers: np.ndarray) -> np.ndarray:
    step = centers[1] - centers[0]
    edges = np.empty(centers.size + 1, dtype=float)
    edges[1:-1] = (centers[:-1] + centers[1:]) / 2.0
    edges[0] = centers[0] - step / 2.0
    edges[-1] = centers[-1] + step / 2.0
    return edges


def save_figure(fig, output: Path, dpi: int):
    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output, dpi=dpi, bbox_inches="tight", pad_inches=0.08, facecolor="white")
    plt.close(fig)
    print(f"Wrote {output}")

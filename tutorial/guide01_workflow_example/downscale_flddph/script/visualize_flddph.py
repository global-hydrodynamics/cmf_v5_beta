#!/usr/bin/env python3
"""Draw native-grid and high-resolution flood-depth panels without recalculation."""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import Normalize
from netCDF4 import Dataset
import numpy as np

import downscale_flddph as depth

FILL_VALUE = np.float32(-9999.0)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True, help="2D low-resolution flddph NetCDF")
    parser.add_argument("--downscaled", type=Path, required=True, help="2D high-resolution flddph NetCDF")
    parser.add_argument("--map-dir", type=Path, required=True)
    parser.add_argument("--resolution", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--west", type=float, required=True)
    parser.add_argument("--east", type=float, required=True)
    parser.add_argument("--south", type=float, required=True)
    parser.add_argument("--north", type=float, required=True)
    parser.add_argument("--depth-min", type=float, default=0.0)
    parser.add_argument("--depth-max", type=float, default=20.0)
    parser.add_argument("--figure-width", type=float, default=12.0)
    parser.add_argument("--figure-height", type=float, default=5.8)
    parser.add_argument("--dpi", type=int, default=180)
    return parser.parse_args()


def read_flddph(path: Path) -> tuple[np.ma.MaskedArray, np.ndarray, np.ndarray, str]:
    with Dataset(path) as source:
        for name in ("flddph", "lat", "lon"):
            if name not in source.variables:
                raise ValueError(f"{path}: missing variable {name!r}")
        variable = source.variables["flddph"]
        if variable.dimensions == ("lat", "lon"):
            values = np.ma.asarray(variable[:], dtype=np.float32)
        elif variable.dimensions == ("time", "lat", "lon") and variable.shape[0] == 1:
            values = np.ma.asarray(variable[0], dtype=np.float32)
        else:
            raise ValueError(f"{path}: expected 2D flddph or one time record")
        if getattr(variable, "units", "") != "m":
            raise ValueError(f"{path}: flddph units must be 'm'")
        lat = np.asarray(source.variables["lat"][:], dtype=np.float64)
        lon = np.asarray(source.variables["lon"][:], dtype=np.float64)
        temporal = getattr(source, "selected_cf_time", getattr(source, "temporal_selection", ""))
    if values.shape != (lat.size, lon.size):
        raise ValueError(f"{path}: coordinate lengths do not match flddph grid")
    values = np.ma.masked_where(np.ma.getmaskarray(values) | ~np.isfinite(np.ma.filled(values, np.nan)) | (np.ma.filled(values, FILL_VALUE) == FILL_VALUE), values)
    return values, lat, lon, str(temporal)


def read_map_geometry(map_dir: Path) -> tuple[int, int, float, float, float, float, float]:
    """Read authoritative model-grid geometry from the current map metadata."""
    return depth.read_map_geometry(map_dir)


def read_map_layer(map_dir: Path, resolution: str, layer: str, lon: np.ndarray,
                   lat: np.ndarray) -> np.ndarray:
    """Merge a listed NetCDF tile layer onto north-first output cell centers."""
    high_dir = map_dir / resolution
    location_path = high_dir / "location.csv"
    tiles = depth.read_locations(location_path)
    if layer == "catmxy":
        output = np.full((2, lat.size, lon.size), -9999, dtype=np.int16)
    else:
        output = np.full((lat.size, lon.size), FILL_VALUE, dtype=np.float32)
    pixel = float(tiles[0]["resolution"])
    for tile in tiles:
        west, east = float(tile["west"]), float(tile["east"])
        south, north = float(tile["south"]), float(tile["north"])
        if east <= lon[0] or west >= lon[-1] or north <= lat[-1] or south >= lat[0]:
            continue
        area = str(tile["area"])
        path = high_dir / f"{area}.{layer}.nc"
        layer_data = depth.read_netcdf_tile(path, tile, layer)
        data = (np.stack((layer_data["catmxx"], layer_data["catmyy"]))
                if layer == "catmxy" else layer_data[layer])
        tile_lon = west + (np.arange(int(tile["nx"])) + 0.5) * pixel
        tile_lat = north - (np.arange(int(tile["ny"])) + 0.5) * pixel
        columns = np.rint((tile_lon - lon[0]) / pixel).astype(int)
        rows = np.rint((lat[0] - tile_lat) / pixel).astype(int)
        valid_x = ((columns >= 0) & (columns < lon.size)
                   & np.isclose(lon[0] + columns * pixel, tile_lon, rtol=0, atol=1e-5))
        valid_y = ((rows >= 0) & (rows < lat.size)
                   & np.isclose(lat[0] - rows * pixel, tile_lat, rtol=0, atol=1e-5))
        source_x, target_x = np.flatnonzero(valid_x), columns[valid_x]
        source_y, target_y = np.flatnonzero(valid_y), rows[valid_y]
        if source_x.size and source_y.size:
            if layer == "catmxy":
                output[:, target_y[:, None], target_x] = data[:, source_y[:, None], source_x]
            else:
                output[np.ix_(target_y, target_x)] = data[np.ix_(source_y, source_x)]
    return output


def main() -> None:
    args = parse_args()
    if args.west >= args.east or args.south >= args.north or args.depth_min >= args.depth_max:
        raise ValueError("Invalid geographic extent or depth scale")
    low, low_lat, low_lon, low_time = read_flddph(args.input)
    high, high_lat, high_lon, high_time = read_flddph(args.downscaled)
    map_dir = args.map_dir.resolve()
    nx, ny, grid_size, map_west, map_east, map_south, map_north = read_map_geometry(map_dir)
    expected_lon = map_west + (np.arange(nx) + 0.5) * grid_size
    expected_lat = map_north - (np.arange(ny) + 0.5) * grid_size
    if low.shape != (ny, nx) or not np.allclose(low_lon, expected_lon, rtol=0, atol=1e-5) or not np.allclose(low_lat, expected_lat, rtol=0, atol=1e-5):
        raise ValueError("Low-resolution NetCDF does not match the map params grid")
    if high_lon.size < 2 or high_lat.size < 2:
        raise ValueError("Downscaled NetCDF must have at least two coordinates per axis")
    pixel_x, pixel_y = float(np.median(np.diff(high_lon))), float(-np.median(np.diff(high_lat)))
    if pixel_x <= 0 or pixel_y <= 0 or not np.isclose(pixel_x, pixel_y, rtol=0, atol=1e-10):
        raise ValueError("Downscaled NetCDF coordinates must be regular, north-first, square pixels")
    background_raw = read_map_layer(map_dir, args.resolution, "flddif", high_lon, high_lat)
    background = np.ma.masked_where(
        ~np.isfinite(background_raw) | (background_raw == FILL_VALUE), background_raw,
    )
    elevation_raw = read_map_layer(map_dir, args.resolution, "elevtn", high_lon, high_lat)
    elevation_valid = np.isfinite(elevation_raw) & (elevation_raw != FILL_VALUE)
    catchment = read_map_layer(map_dir, args.resolution, "catmxy", high_lon, high_lat)
    catmxy_defined = (catchment[0] > 0) & (catchment[1] > 0)
    high_valid = ~np.ma.getmaskarray(high)
    if np.any(high_valid & ~catmxy_defined):
        raise ValueError("Downscaled flood-depth values occur where catmxy is undefined")

    valid_background = background.compressed()
    if not valid_background.size:
        raise ValueError("No flddif background cells overlap the downscaled extent")
    gray_low, gray_high = np.percentile(valid_background, [2, 98])
    if gray_high <= gray_low:
        gray_high = gray_low + 1.0
    normalized = np.clip((background - gray_low) / (gray_high - gray_low), 0, 1)
    intensity = 0.16 + 0.42 * np.ma.sqrt(normalized)
    land_fill = np.ma.getmaskarray(background) & elevation_valid
    display = np.asarray(intensity.filled(1.0))
    display[land_fill] = 0.5
    # Cells without valid high-resolution elevation are outside mapped land
    # (including the sea); keep them white even if flddif has a value there.
    display_mask = (np.ma.getmaskarray(intensity) & ~land_fill) | ~elevation_valid
    grayscale = np.ma.array(display, mask=display_mask)
    display_high = np.ma.masked_where(np.ma.getmaskarray(high) | (high <= 0.0) | ~catmxy_defined, high)
    cmap = plt.get_cmap("YlGnBu").copy()
    cmap.set_bad((1, 1, 1, 0))
    gray_cmap = plt.get_cmap("gray").copy()
    gray_cmap.set_bad((1, 1, 1, 0))

    fig, axes = plt.subplots(1, 2, figsize=(args.figure_width, args.figure_height), constrained_layout=True)
    aspect = 1.0 / np.cos(np.deg2rad((args.south + args.north) / 2.0))
    low_image = axes[0].imshow(low, extent=(map_west, map_east, map_south, map_north), origin="upper",
                               cmap=cmap, norm=Normalize(args.depth_min, args.depth_max), interpolation="nearest", aspect=aspect)
    axes[0].set_title("Native model grid")
    axes[1].set_facecolor("white")
    axes[1].imshow(grayscale, extent=(high_lon[0] - pixel_x / 2, high_lon[-1] + pixel_x / 2,
                                      high_lat[-1] - pixel_y / 2, high_lat[0] + pixel_y / 2),
                   origin="upper", cmap=gray_cmap, vmin=0, vmax=1,
                   interpolation="nearest", aspect=aspect, zorder=0)
    axes[1].imshow(display_high, extent=(high_lon[0] - pixel_x / 2, high_lon[-1] + pixel_x / 2,
                                        high_lat[-1] - pixel_y / 2, high_lat[0] + pixel_y / 2),
                   origin="upper", cmap=cmap, norm=Normalize(args.depth_min, args.depth_max),
                   interpolation="nearest", aspect=aspect, zorder=2)
    axes[1].set_title(f"Downscaled {args.resolution}")
    for ax in axes:
        ax.set_xlim(args.west, args.east)
        ax.set_ylim(args.south, args.north)
        ax.set_xlabel("Longitude [degrees east]")
        ax.set_ylabel("Latitude [degrees north]")
        ax.grid(False)
    title = "CaMa-Flood flood depth"
    times = low_time or high_time
    if times:
        title += f"\n{times}"
    fig.suptitle(title)
    colorbar = fig.colorbar(low_image, ax=axes, shrink=0.82, pad=0.025, extend="max")
    colorbar.set_label("Flood depth [m]")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(args.output, dpi=args.dpi, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved {args.output}: low={low.shape}; high={high.shape}; extent={args.west},{args.east},{args.south},{args.north}")


if __name__ == "__main__":
    main()

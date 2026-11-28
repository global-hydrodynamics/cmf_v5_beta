#!/usr/bin/env python3
"""Plot native-grid and high-resolution CaMa-Flood flood-duration products."""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import BoundaryNorm
from matplotlib.patches import Patch
from netCDF4 import Dataset
import numpy as np

FILL_VALUE = np.float32(-9999.0)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--table", type=Path, required=True)
    parser.add_argument("--downscaled", type=Path, required=True)
    parser.add_argument("--map-dir", type=Path, required=True)
    parser.add_argument("--resolution", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--west", type=float, required=True)
    parser.add_argument("--east", type=float, required=True)
    parser.add_argument("--south", type=float, required=True)
    parser.add_argument("--north", type=float, required=True)
    parser.add_argument("--native-threshold", type=float, default=0.01)
    parser.add_argument("--max-days", type=int, default=365)
    parser.add_argument("--figure-width", type=float, default=12.0)
    parser.add_argument("--figure-height", type=float, default=5.8)
    parser.add_argument("--dpi", type=int, default=180)
    return parser.parse_args()


def load_product(path: Path, variable_name: str, required: tuple[str, ...]):
    with Dataset(path) as source:
        for name in (*required, "lat", "lon"):
            if name not in source.variables:
                raise ValueError(f"{path}: missing variable {name!r}")
        values = np.ma.asarray(source.variables[variable_name][:])
        lat = np.asarray(source.variables["lat"][:], dtype=np.float64)
        lon = np.asarray(source.variables["lon"][:], dtype=np.float64)
        attrs = {name: source.getncattr(name) for name in source.ncattrs()}
    if values.shape != (lat.size, lon.size):
        raise ValueError(f"{path}: {variable_name} shape does not match coordinates")
    return values, lat, lon, attrs


def read_map_geometry(path: Path):
    from visualize_flddph import read_map_geometry as read_depth_map_geometry
    return read_depth_map_geometry(path)


def read_map_layer(map_dir: Path, resolution: str, layer: str, lon: np.ndarray,
                   lat: np.ndarray, dtype: str = "<f4", records: int = 1) -> np.ndarray:
    """Reuse the depth visualizer's validated tile-to-grid placement routine."""
    from visualize_flddph import read_map_layer as read_depth_map_layer
    return read_depth_map_layer(map_dir, resolution, layer, lon, lat, dtype=dtype, records=records)


def main() -> None:
    args = parse_args()
    if not (args.west < args.east and args.south < args.north and args.max_days > 0):
        raise ValueError("Invalid geographic extent or maximum duration")
    with Dataset(args.table) as source:
        for name in ("flood_days", "depth_threshold", "lat", "lon"):
            if name not in source.variables:
                raise ValueError(f"{args.table}: missing variable {name!r}")
        threshold_values = np.asarray(source.variables["depth_threshold"][:], dtype=np.float32)
        table = np.ma.asarray(source.variables["flood_days"][:], dtype=np.float32)
        low_lat = np.asarray(source.variables["lat"][:], dtype=np.float64)
        low_lon = np.asarray(source.variables["lon"][:], dtype=np.float64)
        table_attrs = {name: source.getncattr(name) for name in source.ncattrs()}
    index_matches = np.flatnonzero(np.isclose(threshold_values, args.native_threshold, rtol=0, atol=1e-6))
    if index_matches.size != 1:
        raise ValueError(f"Native threshold {args.native_threshold} m is not present in {args.table}")
    native = np.ma.asarray(table[index_matches[0]], dtype=np.float32)
    high, high_lat, high_lon, high_attrs = load_product(
        args.downscaled, "flood_duration", ("flood_duration", "permanent_water")
    )
    permanent, _, _, _ = load_product(args.downscaled, "permanent_water", ("permanent_water",))
    if native.shape != (low_lat.size, low_lon.size) or high.shape != (high_lat.size, high_lon.size):
        raise ValueError("Duration values do not match their coordinate dimensions")
    if not np.isclose(float(table_attrs["record_count"]), args.max_days):
        raise ValueError("Configured maximum days do not match duration table record_count")
    if high_attrs.get("source_period_start_inclusive") != table_attrs.get("period_start_inclusive"):
        raise ValueError("High-resolution output was generated from a different duration-table period")
    map_dir = args.map_dir.resolve()
    nx, ny, grid, map_west, map_east, map_south, map_north = read_map_geometry(map_dir)
    expected_lon = map_west + (np.arange(nx) + 0.5) * grid
    expected_lat = map_north - (np.arange(ny) + 0.5) * grid
    if native.shape != (ny, nx) or not np.allclose(low_lon, expected_lon, atol=1e-5, rtol=0) or not np.allclose(low_lat, expected_lat, atol=1e-5, rtol=0):
        raise ValueError("Duration table coordinates do not match the CaMa-Flood map")
    high_pixel_x = float(np.median(np.diff(high_lon)))
    high_pixel_y = float(-np.median(np.diff(high_lat)))
    if high_pixel_x <= 0 or not np.isclose(high_pixel_x, high_pixel_y, rtol=0, atol=1e-10):
        raise ValueError("High-resolution coordinates must be regular square pixels")

    flddif = read_map_layer(map_dir, args.resolution, "flddif", high_lon, high_lat)
    elevtn = read_map_layer(map_dir, args.resolution, "elevtn", high_lon, high_lat)
    elevation_valid = np.isfinite(elevtn) & (elevtn != FILL_VALUE)
    background = np.ma.masked_where(~np.isfinite(flddif) | (flddif == FILL_VALUE), flddif)
    valid_bg = background.compressed()
    if not valid_bg.size:
        raise ValueError("No valid high-resolution flddif background overlaps this extent")
    low_bg, high_bg = np.percentile(valid_bg, [2, 98])
    if high_bg <= low_bg:
        high_bg = low_bg + 1.0
    normalized = np.clip((background - low_bg) / (high_bg - low_bg), 0, 1)
    intensity = 0.16 + 0.42 * np.ma.sqrt(normalized)
    land_fill = np.ma.getmaskarray(background) & elevation_valid
    display = np.asarray(intensity.filled(1.0))
    display[land_fill] = 0.5
    grayscale = np.ma.array(display, mask=(np.ma.getmaskarray(intensity) & ~land_fill) | ~elevation_valid)
    high_duration = np.ma.masked_where(np.ma.getmaskarray(high) | (high < 0), high)
    high_permanent = np.ma.filled(permanent, 255).astype(np.uint8) == 1
    high_permanent = np.ma.masked_where(np.ma.getmaskarray(high) | ~high_permanent, high_permanent)

    cmap = plt.get_cmap("YlOrRd").copy()
    cmap.set_bad((1, 1, 1, 0))
    gray_cmap = plt.get_cmap("gray").copy()
    gray_cmap.set_bad((1, 1, 1, 0))
    boundaries = np.array([0, 1, 3, 7, 14, 30, 60, 90, 120, 180, 240, 300, args.max_days + 1])
    norm = BoundaryNorm(boundaries, cmap.N, clip=True)
    native_display = np.ma.masked_where(np.ma.getmaskarray(native) | (native < 0), native)

    fig, axes = plt.subplots(1, 2, figsize=(args.figure_width, args.figure_height), constrained_layout=True)
    aspect = 1.0 / np.cos(np.deg2rad((args.south + args.north) / 2.0))
    image = axes[0].imshow(native_display, extent=(map_west, map_east, map_south, map_north),
                           origin="upper", cmap=cmap, norm=norm, interpolation="nearest", aspect=aspect)
    axes[0].set_title(f"Native model grid: days > {args.native_threshold:g} m")
    axes[1].set_facecolor("white")
    high_extent = (high_lon[0] - high_pixel_x / 2, high_lon[-1] + high_pixel_x / 2,
                   high_lat[-1] - high_pixel_y / 2, high_lat[0] + high_pixel_y / 2)
    axes[1].imshow(grayscale, extent=high_extent, origin="upper", cmap=gray_cmap,
                   vmin=0, vmax=1, interpolation="nearest", aspect=aspect, zorder=0)
    duration_image = axes[1].imshow(high_duration, extent=high_extent, origin="upper",
                                    cmap=cmap, norm=norm, interpolation="nearest", aspect=aspect, zorder=2)
    axes[1].imshow(high_permanent, extent=high_extent, origin="upper",
                   cmap=plt.matplotlib.colors.ListedColormap(["#218c8d"]), vmin=0, vmax=1,
                   interpolation="nearest", aspect=aspect, zorder=3, alpha=0.88)
    axes[1].set_title(f"Downscaled {args.resolution}: local flddif lookup")
    for ax in axes:
        ax.set_xlim(args.west, args.east)
        ax.set_ylim(args.south, args.north)
        ax.set_xlabel("Longitude [degrees east]")
        ax.set_ylabel("Latitude [degrees north]")
        ax.grid(False)
    fig.suptitle(
        f"CaMa-Flood flood duration: {table_attrs.get('period_start_inclusive')} to "
        f"{table_attrs.get('period_end_inclusive')}\n"
        "Native panel uses the 0.01 m minimum threshold; high-resolution panel uses the flddif lookup."
    )
    colorbar = fig.colorbar(image, ax=axes, shrink=0.82, pad=0.025, extend="max")
    colorbar.set_label("Flood duration [days]")
    colorbar.set_ticks([0, 1, 3, 7, 14, 30, 60, 90, 120, 180, 240, 300, args.max_days])
    axes[1].legend(handles=[Patch(facecolor="#218c8d", label="Permanent water (separate mask)")],
                   loc="lower right", framealpha=0.9)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(args.output, dpi=args.dpi, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved {args.output}: native={native.shape}; high={high.shape}; extent={args.west},{args.east},{args.south},{args.north}")


if __name__ == "__main__":
    main()

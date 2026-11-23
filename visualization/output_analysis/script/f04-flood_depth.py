#!/usr/bin/env python3
"""Prepare and plot a one-day native-grid and 1-minute flddph comparison."""

from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import Normalize
from netCDF4 import Dataset, num2date
import numpy as np
from PIL import Image, PngImagePlugin

ROOT = Path(__file__).resolve().parents[3]
RIVER_SCRIPT = ROOT / "visualization" / "river_map" / "script"
sys.path.insert(0, str(RIVER_SCRIPT))
sys.path.insert(0, str(RIVER_SCRIPT.parent.parent / "cmf_colormap" / "src"))
from f05_river_background import (  # noqa: E402
    crop_high_resolution,
    grayscale_background,
    read_float_raster,
    read_high_resolution_grid,
)
from river_map_common import read_geometry, read_map_raster  # noqa: E402

FILL_VALUE = np.float32(1.0e20)
MAP_RECT_INCHES = (1.134, 1.26, 5.519, 6.21)
COLORBAR_RECT_INCHES = (7.182, 1.26, 0.27, 6.21)
TITLES = {
    "a": "p02-f04a Flood Depth: Raster\nNative 15-minute grid",
    "b": "p02-f04b Flood Depth: Downscale 1min\nGuide01 tributary downscaling method",
}


def add_common_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--date", required=True)
    parser.add_argument("--params", type=Path, required=True)
    parser.add_argument("--west", type=float, required=True)
    parser.add_argument("--east", type=float, required=True)
    parser.add_argument("--south", type=float, required=True)
    parser.add_argument("--north", type=float, required=True)
    parser.add_argument("--depth-min", type=float, required=True)
    parser.add_argument("--depth-max", type=float, required=True)
    parser.add_argument("--depth-ticks", required=True)
    parser.add_argument("--cmap", required=True)
    parser.add_argument("--title-size", type=float, required=True)
    parser.add_argument("--axis-label-size", type=float, required=True)
    parser.add_argument("--tick-label-size", type=float, required=True)
    parser.add_argument("--colorbar-label-size", type=float, required=True)
    parser.add_argument("--figure-width", type=float, required=True)
    parser.add_argument("--figure-height", type=float, required=True)
    parser.add_argument("--dpi", type=int, required=True)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    plot = commands.add_parser("plot", help="save the downscaled NetCDF sample and draw f04")
    add_common_arguments(plot)
    for option in ("source", "downscaled-netcdf", "flddif", "elevtn",
                   "location", "panel-a", "panel-b"):
        plot.add_argument(f"--{option}", type=Path, required=True)
    return parser.parse_args()


def read_snapshot(path: Path, date_text: str):
    requested = datetime.strptime(date_text, "%Y-%m-%d")
    with Dataset(path) as source:
        for name in ("time", "lat", "lon", "flddph"):
            if name not in source.variables:
                raise ValueError(f"{path}: missing variable {name!r}")
        variable = source.variables["flddph"]
        if variable.dimensions != ("time", "lat", "lon") or variable.shape[0] != 1:
            raise ValueError(f"{path}: flddph must be a one-record (time, lat, lon) array")
        if getattr(variable, "units", "") != "m":
            raise ValueError(f"{path}: flddph units must be 'm'")
        time_variable = source.variables["time"]
        selected = num2date(
            time_variable[:], time_variable.units,
            calendar=getattr(time_variable, "calendar", "standard"),
            only_use_cftime_datetimes=False,
        )[0]
        if selected.strftime("%Y-%m-%d") != date_text:
            raise ValueError(f"{path}: CF timestamp {selected} does not match {date_text}")
        values = np.ma.asarray(variable[0], dtype=np.float32)
        lon = np.asarray(source.variables["lon"][:], dtype=np.float64)
        lat = np.asarray(source.variables["lat"][:], dtype=np.float64)
    return values, lon, lat, selected


def read_downscaled_snapshot(path: Path, extent: tuple[float, float, float, float]):
    west, east, south, north = extent
    with Dataset(path) as source:
        for name in ("lat", "lon", "flddph"):
            if name not in source.variables:
                raise ValueError(f"{path}: missing variable {name!r}")
        variable = source.variables["flddph"]
        if variable.dimensions == ("lat", "lon"):
            values = np.ma.asarray(variable[:], dtype=np.float32)
        elif variable.dimensions == ("time", "lat", "lon") and variable.shape[0] == 1:
            values = np.ma.asarray(variable[0], dtype=np.float32)
        else:
            raise ValueError(f"{path}: flddph must be (lat,lon) or one-record (time,lat,lon)")
        if getattr(variable, "units", "") != "m":
            raise ValueError(f"{path}: flddph units must be 'm'")
        lon = np.asarray(source.variables["lon"][:], dtype=np.float64)
        lat = np.asarray(source.variables["lat"][:], dtype=np.float64)
    expected = (int(round((north - south) * 60)), int(round((east - west) * 60)))
    expected_lon = west + (np.arange(expected[1]) + 0.5) / 60.0
    expected_lat = north - (np.arange(expected[0]) + 0.5) / 60.0
    if values.shape != expected or not np.allclose(lon, expected_lon, rtol=0, atol=1.0e-5) or not np.allclose(lat, expected_lat, rtol=0, atol=1.0e-5):
        raise ValueError(f"{path}: downscaled grid does not match requested extent and 1-minute cell centers")
    values = np.ma.masked_where(~np.isfinite(values) | (values == -9999.0) | (values == FILL_VALUE), values)
    return values


def parse_ticks(text: str) -> np.ndarray:
    try:
        ticks = np.asarray([float(item.strip()) for item in text.split(",")])
    except ValueError as exc:
        raise ValueError("DEPTH_TICKS must be comma-separated numbers") from exc
    if ticks.size < 2 or not np.all(np.isfinite(ticks)) or np.any(np.diff(ticks) <= 0):
        raise ValueError("DEPTH_TICKS must be finite and strictly ascending")
    return ticks


def figure_rect(rect, width: float, height: float):
    left, bottom, rect_width, rect_height = rect
    return left / width, bottom / height, rect_width / width, rect_height / height


def embed_layout(fig, ax, cax, output: Path, dpi: int, extent) -> None:
    fig.canvas.draw()
    width_px, height_px = (round(value * dpi) for value in fig.get_size_inches())
    scale = dpi / fig.dpi

    def bounds(axes):
        x, y, width, height = axes.get_window_extent(fig.canvas.get_renderer()).bounds
        return [round(x * scale, 5), round(height_px - (y + height) * scale, 5),
                round(width * scale, 5), round(height * scale, 5)]

    metadata = PngImagePlugin.PngInfo()
    metadata.add_text("cama_map_layout", json.dumps({
        "bounds_px": bounds(ax), "extent": list(extent),
        "colorbar_bounds_px": bounds(cax), "colorbar_visible": True,
    }))
    temporary = output.with_name(f".{output.name}.tmp.png")
    with Image.open(output) as image:
        image.save(temporary, format="PNG", pnginfo=metadata, dpi=(dpi, dpi))
    temporary.replace(output)


def draw_panel(args: argparse.Namespace, panel: str, coarse, highres, highres_extent,
               grayscale, gray_cmap, output: Path, ticks: np.ndarray,
               geometry, out_of_range: tuple[int, int]) -> None:
    width, height = args.figure_width, args.figure_height
    if width <= 0 or height <= 0 or args.dpi < 1:
        raise ValueError("figure dimensions and DPI must be positive")
    fig = plt.figure(figsize=(width, height))
    ax = fig.add_axes(figure_rect(MAP_RECT_INCHES, width, height))
    cax = fig.add_axes(figure_rect(COLORBAR_RECT_INCHES, width, height))
    extent = (args.west, args.east, args.south, args.north)
    midlat = (args.south + args.north) / 2.0
    ax.set_xlim(args.west, args.east)
    ax.set_ylim(args.south, args.north)
    ax.set_aspect(1.0 / np.cos(np.deg2rad(midlat)))
    ax.set_xlabel("Longitude", fontsize=args.axis_label_size)
    ax.set_ylabel("Latitude", fontsize=args.axis_label_size)
    ax.tick_params(axis="both", labelsize=args.tick_label_size)
    ax.set_title(f"{TITLES[panel]}\n{args.date}", fontsize=args.title_size, pad=10)
    ax.grid(False)

    raster_extent = geometry[3:]
    if panel == "b":
        ax.imshow(grayscale, origin="upper", extent=highres_extent,
                  cmap=gray_cmap, vmin=0, vmax=1, interpolation="nearest",
                  aspect=ax.get_aspect(), zorder=0)
        data = highres
        raster_extent = highres_extent
    else:
        data = coarse
    cmap = plt.get_cmap(args.cmap).copy()
    cmap.set_bad((1.0, 1.0, 1.0, 0.0) if panel == "b" else "white")
    cmap.set_under("#ffffcc")
    cmap.set_over("#081d58")
    image = ax.imshow(
        data, origin="upper", extent=raster_extent, cmap=cmap,
        norm=Normalize(args.depth_min, args.depth_max, clip=False),
        interpolation="nearest", aspect=ax.get_aspect(), zorder=2,
    )
    # Equal geographic scaling can shrink the active map rectangle inside its
    # allocated box. Match the colorbar to the rendered axes, not that box.
    fig.canvas.draw()
    map_position = ax.get_position()
    colorbar_x = COLORBAR_RECT_INCHES[0] / width
    colorbar_width = COLORBAR_RECT_INCHES[2] / width
    cax.set_position((colorbar_x, map_position.y0,
                      colorbar_width, map_position.height))
    colorbar = fig.colorbar(image, cax=cax, ticks=ticks, extend="both" if any(out_of_range) else "neither")
    colorbar.set_label("Floodplain depth, flddph [m]", fontsize=args.colorbar_label_size)
    colorbar.ax.tick_params(labelsize=args.tick_label_size)
    ax._river_map_extent = extent
    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output, dpi=args.dpi, format="png")
    embed_layout(fig, ax, cax, output, args.dpi, extent)
    plt.close(fig)


def plot(args: argparse.Namespace) -> None:
    if not (args.west < args.east and args.south < args.north):
        raise ValueError("map extent must be ordered")
    if not (args.depth_min < args.depth_max):
        raise ValueError("depth range must be ascending")
    ticks = parse_ticks(args.depth_ticks)
    if ticks[0] < args.depth_min or ticks[-1] > args.depth_max:
        raise ValueError("DEPTH_TICKS must lie within DEPTH_MIN and DEPTH_MAX")
    geometry = read_geometry(args.params)
    coarse, lon, lat, timestamp = read_snapshot(args.source, args.date)
    expected_coarse = (geometry[1], geometry[0])
    if coarse.shape != expected_coarse:
        raise ValueError(f"coarse flddph shape {coarse.shape} != expected {expected_coarse}")
    # The requested map extent is a subset of the native Mekong map extent.
    nx1, ny1, _, west1, east1, south1, north1 = read_high_resolution_grid(args.location, geometry)
    grid = (nx1, ny1, 1 / 60, west1, east1, south1, north1)
    flddif = read_float_raster(args.flddif, nx1, ny1)
    elevtn = read_float_raster(args.elevtn, nx1, ny1)
    fill_mask = np.ma.getmaskarray(flddif) & ~np.ma.getmaskarray(elevtn)
    gray_full, gray_cmap, gray_low, gray_high = grayscale_background(
        flddif, fill_mask=fill_mask, fill_value=0.5, palette="gray",
    )
    gray_crop, highres_extent = crop_high_resolution(gray_full, grid, (args.west, args.east, args.south, args.north))

    extent = (args.west, args.east, args.south, args.north)
    highres = read_downscaled_snapshot(args.downscaled_netcdf, extent)
    high_valid = highres.compressed()
    if np.any(high_valid < 0):
        raise ValueError("Downscaled flddph contains negative valid values")
    expected = highres.shape
    # Zero depth denotes dry pixels; keep the flddif context visible beneath them.
    highres.mask = np.ma.getmaskarray(highres) | (highres.filled(0) <= 0)
    low_values = coarse.compressed()
    both = np.concatenate((low_values, high_valid))
    below = int(np.count_nonzero(both < args.depth_min))
    above = int(np.count_nonzero(both > args.depth_max))
    if both.size == 0:
        raise ValueError("No valid flood-depth values to plot")
    print(f"flddph {args.date} CF timestamp={timestamp}; coarse valid={low_values.size}, min={low_values.min():.6g} m, max={low_values.max():.6g} m")
    print(f"Downscaled valid={high_valid.size}, min={high_valid.min():.6g} m, max={high_valid.max():.6g} m, shape={expected}; flddif gray stretch p2-p98={gray_low:.6g}..{gray_high:.6g} m")
    print(f"Shared scale [{args.depth_min:g}, {args.depth_max:g}] m: below={below}, above={above}; out-of-range values are not clipped")
    ticks = parse_ticks(args.depth_ticks)
    draw_panel(args, "a", coarse, highres, highres_extent, gray_crop, gray_cmap,
               args.panel_a, ticks, geometry, (below, above))
    draw_panel(args, "b", coarse, highres, highres_extent, gray_crop, gray_cmap,
               args.panel_b, ticks, geometry, (below, above))


def main() -> None:
    args = parse_args()
    plot(args)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Map a CaMa-Flood depth-duration table onto a higher-resolution map."""

from __future__ import annotations

import argparse
from pathlib import Path

from netCDF4 import Dataset
import numpy as np

FILL_VALUE = np.float32(-9999.0)
MASK_FILL = np.uint8(255)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--table", type=Path, required=True)
    parser.add_argument("--map-dir", type=Path, required=True)
    parser.add_argument("--map-format", choices=("auto", "netcdf", "binary"), default="auto")
    parser.add_argument("--resolution", required=True)
    parser.add_argument("--west", type=float, required=True)
    parser.add_argument("--east", type=float, required=True)
    parser.add_argument("--south", type=float, required=True)
    parser.add_argument("--north", type=float, required=True)
    parser.add_argument("--depth-interval", type=float, required=True)
    parser.add_argument("--permanent-water", type=int, choices=(0, 1), default=1)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def read_duration_table(path: Path):
    with Dataset(path) as source:
        for name in ("flood_days", "depth_threshold", "lat", "lon"):
            if name not in source.variables:
                raise ValueError(f"{path}: missing variable {name!r}")
        days = np.ma.asarray(source.variables["flood_days"][:], dtype=np.float32)
        thresholds = np.asarray(source.variables["depth_threshold"][:], dtype=np.float32)
        lat = np.asarray(source.variables["lat"][:], dtype=np.float64)
        lon = np.asarray(source.variables["lon"][:], dtype=np.float64)
        if source.variables["flood_days"].dimensions != ("threshold", "lat", "lon"):
            raise ValueError(f"{path}: flood_days dimensions must be (threshold,lat,lon)")
        attrs = {name: source.getncattr(name) for name in source.ncattrs()}
    if days.shape != (thresholds.size, lat.size, lon.size):
        raise ValueError(f"{path}: inconsistent threshold and grid dimensions")
    return days, thresholds, lat, lon, attrs


def main() -> None:
    args = parse_args()
    if not args.table.is_file():
        raise FileNotFoundError(args.table)
    if not (args.west < args.east and args.south < args.north and args.depth_interval > 0):
        raise ValueError("Invalid extent or depth interval")
    import downscale_flddph as depth

    table, thresholds, low_lat, low_lon, table_attrs = read_duration_table(args.table)
    nx, ny, coarse, map_west, map_east, map_south, map_north = depth.read_map_geometry(args.map_dir / "params.txt")
    if table.shape[1:] != (ny, nx):
        raise ValueError(f"{args.table}: table grid {table.shape[1:]} does not match map {(ny, nx)}")
    exp_lon = map_west + (np.arange(nx) + 0.5) * coarse
    exp_lat = map_north - (np.arange(ny) + 0.5) * coarse
    if not np.allclose(low_lon, exp_lon, rtol=0, atol=1e-5) or not np.allclose(low_lat, exp_lat, rtol=0, atol=1e-5):
        raise ValueError(f"{args.table}: coordinates do not match map params.txt")
    if not np.isclose(float(table_attrs.get("depth_interval_m", np.nan)), args.depth_interval, rtol=0, atol=1e-7):
        raise ValueError("Configured depth interval does not match the duration table")
    expected_nlev = int(float(table_attrs["max_depth_m"]) / args.depth_interval) + 1
    if thresholds.size != expected_nlev:
        raise ValueError(f"Duration table has {thresholds.size} levels; expected {expected_nlev}")

    pixel = 1.0 / 60.0 if args.resolution == "1min" else None
    if pixel is None:
        raise ValueError("This package currently supports the existing 1min high-resolution grid")
    width_float, height_float = (args.east - args.west) / pixel, (args.north - args.south) / pixel
    width, height = int(round(width_float)), int(round(height_float))
    if not np.isclose(width_float, width, rtol=0, atol=1e-7) or not np.isclose(height_float, height, rtol=0, atol=1e-7):
        raise ValueError("Requested extent must align to the selected high-resolution pixel size")
    lon_out = args.west + (np.arange(width, dtype=np.float64) + 0.5) * pixel
    lat_out = args.north - (np.arange(height, dtype=np.float64) + 0.5) * pixel
    shape = (height, width)
    flood_duration = np.full(shape, -9999, dtype=np.int16)
    permanent_water = np.full(shape, MASK_FILL, dtype=np.uint8)
    high_dir = args.map_dir / args.resolution
    tiles = depth.read_locations(high_dir / "location.txt")
    selected_layers: dict[str, str] = {}
    selected_sources: dict[str, str] = {}

    for tile in tiles:
        tw, te = float(tile["west"]), float(tile["east"])
        ts, tn = float(tile["south"]), float(tile["north"])
        if te < args.west or tw > args.east or tn < args.south or ts > args.north:
            continue
        area = str(tile["area"])
        data_by_layer = {}
        for layer in ("catmxy", "flddif", "rivwth"):
            file_format, path, source_layer = depth.resolve_hires_layer(high_dir, area, layer, args.map_format)
            data = depth.read_netcdf_tile(path, tile, source_layer) if file_format == "netcdf" else depth.read_binary_hires_tile(path, tile, source_layer)
            data_by_layer[layer] = data
            selected_layers[f"{area}.{source_layer}"] = file_format
            selected_sources[f"{area}.{source_layer}"] = str(path)
        cat_x = data_by_layer["catmxy"]["catmxx"].astype(np.int64)
        cat_y = data_by_layer["catmxy"]["catmyy"].astype(np.int64)
        relative_height = data_by_layer["flddif"]["flddif"]
        river_width = data_by_layer["rivwth"]["rivwth"]
        tile_ny, tile_nx = cat_x.shape
        tile_lon = float(tile["west"]) + (np.arange(tile_nx) + 0.5) * pixel
        tile_lat = float(tile["north"]) - (np.arange(tile_ny) + 0.5) * pixel
        source_x = np.flatnonzero((tile_lon > args.west) & (tile_lon < args.east))
        source_y = np.flatnonzero((tile_lat > args.south) & (tile_lat < args.north))
        if not source_x.size or not source_y.size:
            continue
        target_x = np.floor((tile_lon[source_x] - args.west) / pixel).astype(int)
        target_y = np.floor((args.north - tile_lat[source_y]) / pixel).astype(int)
        sx, sy = np.meshgrid(source_x, source_y)
        tx, ty = np.meshgrid(target_x, target_y)
        cx, cy = cat_x[sy, sx], cat_y[sy, sx]
        assigned = (cx > 0) & (cy > 0)
        if not np.any(assigned):
            continue
        if np.any((cx[assigned] > nx) | (cy[assigned] > ny)):
            raise ValueError(f"{area}: catmxy points outside the coarse map grid")
        diff = relative_height[sy, sx].astype(np.float32)
        coarse_i, coarse_j = cx[assigned] - 1, cy[assigned] - 1
        diff_assigned = diff[assigned]
        values = np.zeros(diff_assigned.shape, dtype=np.int16)
        nonnegative = diff_assigned >= np.float32(0.0)
        # Match Fortran INT(diff / INTDPH) + 1, then convert to zero-based indexing.
        record = np.floor(diff_assigned[nonnegative] / np.float32(args.depth_interval)).astype(np.int64)
        record = np.minimum(record, thresholds.size - 1)
        selected_table = table.filled(FILL_VALUE)[record, coarse_j[nonnegative], coarse_i[nonnegative]]
        if np.any(selected_table == FILL_VALUE):
            raise ValueError(f"{area}: assigned catmxy references missing duration-table values")
        values[nonnegative] = selected_table.astype(np.int16)
        # The legacy routine tests rivwth != -9999 and != 0; store that mask separately.
        rw = river_width[sy, sx][assigned]
        permanent = (rw != FILL_VALUE) & (rw != 0.0) if args.permanent_water else np.zeros(rw.shape, dtype=bool)
        flood_duration[ty[assigned], tx[assigned]] = values
        permanent_water[ty[assigned], tx[assigned]] = permanent.astype(np.uint8)

    valid = flood_duration != -9999
    if not np.any(valid):
        raise ValueError("No mapped high-resolution cells overlap the requested extent")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with Dataset(args.output, "w", format="NETCDF4") as output:
        output.createDimension("lat", height)
        output.createDimension("lon", width)
        lat_var = output.createVariable("lat", "f8", ("lat",))
        lon_var = output.createVariable("lon", "f8", ("lon",))
        lat_var[:], lon_var[:] = lat_out, lon_out
        lat_var.units, lon_var.units = "degrees_north", "degrees_east"
        days = output.createVariable("flood_duration", "i2", ("lat", "lon"), fill_value=np.int16(-9999), zlib=True, complevel=4)
        days[:, :] = np.ma.masked_where(~valid, flood_duration)
        days.units = "days"
        days.long_name = "number of daily flood-depth records above selected threshold"
        water = output.createVariable("permanent_water", "u1", ("lat", "lon"), fill_value=MASK_FILL, zlib=True, complevel=4)
        water[:, :] = np.ma.masked_where(~valid, permanent_water)
        water.flag_values = np.array([0, 1], dtype=np.uint8)
        water.flag_meanings = "not_permanent_water permanent_water"
        water.long_name = "permanent-water mask from rivwth; not duration days"
        output.source_duration_table = str(args.table)
        output.source_period_start_inclusive = str(table_attrs["period_start_inclusive"])
        output.source_period_end_inclusive = str(table_attrs["period_end_inclusive"])
        output.record_count = np.int32(table_attrs["record_count"])
        output.depth_interval_m = np.float32(args.depth_interval)
        output.permanent_water_enabled = np.int8(args.permanent_water)
        output.map_directory = str(args.map_dir)
        output.map_format = args.map_format
        output.high_resolution = args.resolution
        output.bounds_west_east_south_north = f"{args.west},{args.east},{args.south},{args.north}"
        output.map_layer_formats = ";".join(f"{name}={value}" for name, value in selected_layers.items())
        output.map_layer_sources = ";".join(f"{name}={value}" for name, value in selected_sources.items())
        output.history = "Created by downscale_duration.py; no tributary fill or backwater adjustment applied."
    print(f"Wrote {args.output}: shape={shape}; valid={np.count_nonzero(valid)}; permanent={np.count_nonzero(permanent_water == 1)}")


if __name__ == "__main__":
    main()

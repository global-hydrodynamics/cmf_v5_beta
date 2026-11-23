#!/usr/bin/env python3
"""Calculate a CaMa-Flood depth-duration table from daily CF NetCDF output."""

from __future__ import annotations

import argparse
from datetime import date, datetime, timedelta
from pathlib import Path

from netCDF4 import Dataset, num2date
import numpy as np

FILL_VALUE = np.float32(-9999.0)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--map-dir", type=Path, required=True)
    parser.add_argument("--map-format", choices=("auto", "netcdf", "binary"), default="auto")
    parser.add_argument("--start-date", type=date.fromisoformat, required=True)
    parser.add_argument("--end-date", type=date.fromisoformat, required=True)
    parser.add_argument("--max-depth", type=float, default=20.0)
    parser.add_argument("--depth-interval", type=float, default=0.05)
    parser.add_argument("--block-rows", type=int, default=16)
    return parser.parse_args()


def load_grid(args: argparse.Namespace):
    # Reuse the package's validated NetCDF/Binary map reader.
    import downscale_flddph as depth

    nx, ny, resolution, west, east, south, north = depth.read_map_geometry(args.map_dir / "params.txt")
    next_x, next_y, _, formats, sources = depth.read_base_map(
        args.map_dir, args.map_format, nx, ny, west, north, resolution
    )
    # The legacy calc_depth-duration.F90 masks cells from the first nextxy plane only.
    active = next_x != -9999
    return depth, (nx, ny, resolution, west, east, south, north), active, formats, sources


def decode_daily_times(variable) -> list[datetime]:
    calendar = getattr(variable, "calendar", "standard")
    values = num2date(variable[:], variable.units, calendar=calendar, only_use_cftime_datetimes=False)
    result = []
    for value in values:
        stamp = datetime(value.year, value.month, value.day, value.hour, value.minute, value.second)
        if stamp.time() != datetime.min.time():
            raise ValueError(f"Daily CF timestamps must be at midnight; found {stamp.isoformat()}")
        result.append(stamp)
    return result


def selected_daily_records(times: list[datetime], start: date, end: date) -> list[int]:
    if start > end:
        raise ValueError("--start-date must be <= --end-date")
    for left, right in zip(times, times[1:]):
        if right - left != timedelta(days=1):
            raise ValueError(f"CF time axis is not daily and continuous near {left} / {right}")
    selected = [index for index, stamp in enumerate(times) if start <= stamp.date() <= end]
    expected = (end - start).days + 1
    dates = [times[index].date() for index in selected]
    if len(dates) != expected:
        missing = [start + timedelta(days=i) for i in range(expected) if start + timedelta(days=i) not in dates]
        duplicates = sorted({day for day in dates if dates.count(day) > 1})
        raise ValueError(
            f"Expected {expected} daily CF records for {start} through {end}; found {len(dates)}. "
            f"Missing dates: {missing[:8]}; duplicate dates: {duplicates[:8]}"
        )
    if len(set(dates)) != len(dates):
        raise ValueError(f"Duplicate daily CF dates in selected period {start} through {end}")
    return selected


def main() -> None:
    args = parse_args()
    if not args.input.is_file():
        raise FileNotFoundError(args.input)
    if args.max_depth <= 0 or args.depth_interval <= 0 or args.block_rows <= 0:
        raise ValueError("max-depth, depth-interval and block-rows must be positive")

    depth, geometry, active, formats, sources = load_grid(args)
    nx, ny, resolution, west, east, south, north = geometry
    nlev = int(args.max_depth / args.depth_interval) + 1
    thresholds = np.maximum(
        np.arange(nlev, dtype=np.float32) * np.float32(args.depth_interval),
        np.float32(0.01),
    )

    with Dataset(args.input) as source:
        for name in ("flddph", "lat", "lon", "time"):
            if name not in source.variables:
                raise ValueError(f"{args.input}: missing variable {name!r}")
        variable = source.variables["flddph"]
        if variable.dimensions != ("time", "lat", "lon") or variable.shape[1:] != (ny, nx):
            raise ValueError(f"{args.input}: flddph must be (time,lat,lon) on {(ny, nx)}; got {variable.shape}")
        if getattr(variable, "units", "") != "m":
            raise ValueError(f"{args.input}: flddph units must be 'm'")
        lat = np.asarray(source.variables["lat"][:], dtype=np.float64)
        lon = np.asarray(source.variables["lon"][:], dtype=np.float64)
        expected_lon = west + (np.arange(nx, dtype=np.float64) + 0.5) * resolution
        expected_lat = north - (np.arange(ny, dtype=np.float64) + 0.5) * resolution
        if not np.allclose(lon, expected_lon, rtol=0, atol=1e-5) or not np.allclose(lat, expected_lat, rtol=0, atol=1e-5):
            raise ValueError(f"{args.input}: coordinates do not match map params.txt")
        times = decode_daily_times(source.variables["time"])
        selected = selected_daily_records(times, args.start_date, args.end_date)
        time_units = source.variables["time"].units
        calendar_name = getattr(source.variables["time"], "calendar", "standard")
        if len(selected) != (args.end_date - args.start_date).days + 1:
            raise ValueError("Selected daily record count does not match the inclusive date range")

        duration = np.full((nlev, ny, nx), FILL_VALUE, dtype=np.float32)
        for row0 in range(0, ny, args.block_rows):
            row1 = min(row0 + args.block_rows, ny)
            cell_active = active[row0:row1]
            q_by_day = np.zeros((len(selected), row1 - row0, nx), dtype=np.int16)
            for day_index, record_index in enumerate(selected):
                data = np.ma.asarray(variable[record_index, row0:row1, :], dtype=np.float32)
                raw = np.asarray(np.ma.filled(data, FILL_VALUE), dtype=np.float32)
                fill = np.float32(getattr(variable, "_FillValue", 1.0e20))
                missing = np.ma.getmaskarray(data) | ~np.isfinite(raw) | (raw == fill) | (raw == FILL_VALUE)
                if np.any(missing & cell_active):
                    raise ValueError(f"{args.input}: missing flddph on active model cells at {times[record_index].date()}")
                q = np.searchsorted(thresholds, raw, side="left")
                q_by_day[day_index] = np.where(cell_active & ~missing, q, 0)
            # q is the number of thresholds strictly below daily depth.
            # Count the q values per cell, then reverse-cumulate to obtain days above each threshold.
            for local_y, local_x in zip(*np.nonzero(cell_active)):
                histogram = np.bincount(q_by_day[:, local_y, local_x], minlength=nlev + 1)
                counts = np.cumsum(histogram[::-1], dtype=np.int32)[::-1][1:]
                duration[:, row0 + local_y, local_x] = counts.astype(np.float32)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with Dataset(args.output, "w", format="NETCDF4") as output:
        output.createDimension("threshold", nlev)
        output.createDimension("lat", ny)
        output.createDimension("lon", nx)
        lat_out = output.createVariable("lat", "f8", ("lat",))
        lon_out = output.createVariable("lon", "f8", ("lon",))
        lat_out[:] = expected_lat
        lon_out[:] = expected_lon
        lat_out.units, lon_out.units = "degrees_north", "degrees_east"
        threshold_out = output.createVariable("depth_threshold", "f4", ("threshold",))
        threshold_out[:] = thresholds
        threshold_out.units = "m"
        threshold_out.long_name = "strict flood-depth exceedance threshold"
        days = output.createVariable("flood_days", "f4", ("threshold", "lat", "lon"),
                                     fill_value=FILL_VALUE, zlib=True, complevel=4)
        days[:, :, :] = np.ma.masked_where(duration == FILL_VALUE, duration)
        days.units = "days"
        days.long_name = "number of daily records with flddph strictly above depth_threshold"
        output.source_file = str(args.input)
        output.source_variable = "flddph(time,lat,lon)"
        output.source_time_units = time_units
        output.source_calendar = calendar_name
        output.period_start_inclusive = args.start_date.isoformat()
        output.period_end_inclusive = args.end_date.isoformat()
        output.record_count = np.int32(len(selected))
        output.daily_record_time_start = times[selected[0]].isoformat()
        output.daily_record_time_end = times[selected[-1]].isoformat()
        output.max_depth_m = np.float32(args.max_depth)
        output.depth_interval_m = np.float32(args.depth_interval)
        output.minimum_threshold_m = np.float32(0.01)
        output.threshold_comparison = "strict greater-than"
        output.map_directory = str(args.map_dir)
        output.map_formats = ";".join(f"{key}={value}" for key, value in formats.items())
        output.map_sources = ";".join(f"{key}={value}" for key, value in sources.items())
        output.history = "Created by calc_duration.py using daily CF-time records."

    print(f"Wrote {args.output}: levels={nlev}, records={len(selected)}, active_cells={np.count_nonzero(active)}")


if __name__ == "__main__":
    main()

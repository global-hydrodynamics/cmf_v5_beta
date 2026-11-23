#!/usr/bin/env python3
"""Select or temporally aggregate CF-timestamped CaMa-Flood flddph NetCDF."""

from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path

from netCDF4 import Dataset, num2date
import numpy as np

FILL_VALUE = np.float32(-9999.0)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--mode", choices=("snapshot", "mean", "maximum"), required=True)
    parser.add_argument("--time", help="Exact CF timestamp for snapshot (for example 2001-09-01T00:00:00).")
    parser.add_argument("--start", help="Inclusive period start for mean/maximum.")
    parser.add_argument("--end", help="Inclusive period end for mean/maximum.")
    return parser.parse_args()


def decode_times(variable) -> list[datetime]:
    calendar = getattr(variable, "calendar", "standard")
    dates = num2date(
        variable[:], variable.units, calendar=calendar,
        only_use_cftime_datetimes=False,
    )
    return [datetime(value.year, value.month, value.day, value.hour,
                     value.minute, value.second, value.microsecond) for value in dates]


def parse_datetime(value: str) -> datetime:
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).replace(tzinfo=None)
    except ValueError as exc:
        raise ValueError(f"Invalid timestamp {value!r}; use YYYY-MM-DD or ISO date/time") from exc


def main() -> None:
    args = parse_args()
    if not args.input.is_file():
        raise FileNotFoundError(args.input)
    if args.mode == "snapshot" and (not args.time or args.start or args.end):
        raise ValueError("snapshot mode requires --time and does not accept --start/--end")
    if args.mode != "snapshot" and (not args.start or not args.end or args.time):
        raise ValueError("mean/maximum mode requires --start and --end only")

    with Dataset(args.input) as source:
        for name in ("flddph", "lat", "lon", "time"):
            if name not in source.variables:
                raise ValueError(f"{args.input}: missing variable {name!r}")
        variable = source.variables["flddph"]
        if variable.dimensions not in (("time", "lat", "lon"), ("lat", "lon")):
            raise ValueError(f"{args.input}: flddph dimensions must be (time,lat,lon) or (lat,lon)")
        times = decode_times(source.variables["time"])
        if variable.dimensions == ("lat", "lon"):
            if len(times) != 1:
                raise ValueError(f"{args.input}: 2D flddph requires exactly one time coordinate")
            values = np.ma.asarray(variable[:], dtype=np.float32)[None, ...]
        else:
            if variable.shape[0] != len(times):
                raise ValueError(f"{args.input}: time coordinate length does not match flddph")
            values = np.ma.asarray(variable[:], dtype=np.float32)
        mask = np.ma.getmaskarray(values) | ~np.isfinite(np.ma.filled(values, np.nan))
        raw = np.asarray(np.ma.filled(values, FILL_VALUE), dtype=np.float32)
        mask |= raw == np.float32(1.0e20)
        values = np.ma.array(raw, mask=mask)
        lat = np.asarray(source.variables["lat"][:], dtype=np.float64)
        lon = np.asarray(source.variables["lon"][:], dtype=np.float64)
        units = getattr(variable, "units", "")
        if units != "m":
            raise ValueError(f"{args.input}: flddph units must be 'm', got {units!r}")
        global_attrs = {name: source.getncattr(name) for name in source.ncattrs()}
        lat_var, lon_var = source.variables["lat"], source.variables["lon"]
        lat_dtype, lon_dtype = lat_var.datatype, lon_var.datatype
        lat_attrs = {name: lat_var.getncattr(name) for name in lat_var.ncattrs()}
        lon_attrs = {name: lon_var.getncattr(name) for name in lon_var.ncattrs()}
        variable_attrs = {name: variable.getncattr(name) for name in variable.ncattrs() if name != "_FillValue"}
        long_name = getattr(variable, "long_name", "CaMa-Flood floodplain depth")

    if values.shape[1:] != (lat.size, lon.size) or lat.size == 0 or lon.size == 0:
        raise ValueError(f"{args.input}: coordinate lengths do not match flddph {values.shape}")
    if args.mode == "snapshot":
        requested = parse_datetime(args.time)
        matches = [index for index, value in enumerate(times) if value == requested]
        if len(matches) != 1:
            raise ValueError(f"Expected one CF time matching {requested.isoformat()}, found {len(matches)}")
        selected = values[matches[0]]
        method_text = f"snapshot at exact CF timestamp {times[matches[0]].isoformat()}"
        time_attrs = {"selected_cf_time": times[matches[0]].isoformat()}
    else:
        start, end = parse_datetime(args.start), parse_datetime(args.end)
        if start > end:
            raise ValueError("--start must be less than or equal to --end")
        indices = [i for i, value in enumerate(times) if start <= value <= end]
        if not indices:
            raise ValueError(f"No CF time coordinates in inclusive period {start} through {end}")
        subset = values[indices]
        selected = np.ma.mean(subset, axis=0) if args.mode == "mean" else np.ma.max(subset, axis=0)
        method_text = f"{args.mode} of CF time-coordinate samples in inclusive period [{start.isoformat()}, {end.isoformat()}]"
        time_attrs = {
            "aggregation_start_inclusive": start.isoformat(),
            "aggregation_end_inclusive": end.isoformat(),
            "aggregation_sample_count": np.int32(len(indices)),
        }

    output_values = np.asarray(np.ma.filled(selected, FILL_VALUE), dtype=np.float32)
    if not np.all(np.isfinite(output_values)):
        raise ValueError("Selected flddph contains non-finite output values")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with Dataset(args.output, "w", format="NETCDF4") as output:
        output.createDimension("lat", lat.size)
        output.createDimension("lon", lon.size)
        lat_out = output.createVariable("lat", lat_dtype, ("lat",))
        lon_out = output.createVariable("lon", lon_dtype, ("lon",))
        lat_out[:] = lat
        lon_out[:] = lon
        for name, attrs in ((lat_out, lat_attrs), (lon_out, lon_attrs)):
            for key, value in attrs.items():
                name.setncattr(key, value)
        flddph = output.createVariable("flddph", "f4", ("lat", "lon"), fill_value=FILL_VALUE, zlib=True, complevel=4)
        flddph[:, :] = np.ma.masked_where(output_values == FILL_VALUE, output_values)
        for key, value in variable_attrs.items():
            if key not in ("units", "long_name"):
                flddph.setncattr(key, value)
        flddph.units = "m"
        flddph.long_name = long_name
        for key, value in global_attrs.items():
            if key not in ("history",):
                output.setncattr(key, value)
        output.source_file = str(args.input)
        output.temporal_selection = method_text
        for key, value in time_attrs.items():
            output.setncattr(key, value)
        output.history = f"Created by aggregate_flddph.py: {method_text}."
    print(f"Wrote {args.output}: mode={args.mode}; shape={output_values.shape}; valid={np.count_nonzero(output_values != FILL_VALUE)}")


if __name__ == "__main__":
    main()

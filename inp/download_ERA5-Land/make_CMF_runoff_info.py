#!/usr/bin/env python3
"""Generate CaMa-Flood configuration information from converted NetCDF runoff."""

from __future__ import annotations

import argparse
import glob
import math
import sys
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import xarray as xr


#==========================================================
# Arguments
#==========================================================

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Write CaMa-Flood runoff forcing metadata from NetCDF files."
    )

    parser.add_argument("--outdir", type=Path, required=True, help="Directory containing converted runoff files")
    parser.add_argument("--outfile", type=Path, required=True, help="Output text file")

    # NetCDF options
    parser.add_argument("--pattern", default="runoff_*.nc", help="NetCDF file pattern. Default: runoff_*.nc")
    parser.add_argument("--variable", default="runoff", help="NetCDF runoff variable name. Default: runoff")
    parser.add_argument("--merge-unit", choices=["daily", "yearly", "monthly"], default="monthly", help="NetCDF output grouping")

    # Common options
    parser.add_argument(
        "--timestep-hours",
        type=float,
        required=True,
        help=(
            "Forcing timestep in hours (must match the converted data)."
        ),
    )
    parser.add_argument("--start", default="", help="Conversion period start date, YYYY-MM-DD")
    parser.add_argument("--end", default="", help="Conversion period end date, YYYY-MM-DD")
    parser.add_argument("--sample-name", default="ERA5-Land runoff", help="Name shown in the text header")
    parser.add_argument("--prefix", default="runoff_", help='NetCDF runoff file prefix only. Default: "runoff_"')
    parser.add_argument("--suffix", default=".nc", help='NetCDF runoff file suffix. Default: ".nc"')
    parser.add_argument("--overwrite", action="store_true", help="Overwrite output text file")

    return parser.parse_args()


#==========================================================
# Small utilities
#==========================================================

def fmt_float(x: Any, ndigits: int = 8) -> str:
    try:
        xf = float(x)
    except Exception:
        return str(x)

    if not np.isfinite(xf):
        return "NaN"

    if abs(xf - round(xf)) < 1.0e-9:
        return str(int(round(xf)))

    text = f"{xf:.{ndigits}f}".rstrip("0").rstrip(".")
    if text == "-0":
        text = "0"
    return text


def find_files(outdir: Path, pattern: str) -> list[Path]:
    return sorted(Path(p) for p in glob.glob(str(outdir / pattern)))


def find_coord_name(ds: xr.Dataset, candidates: list[str]) -> str:
    for name in candidates:
        if name in ds.coords:
            return name
        if name in ds.dims:
            return name
    raise KeyError(f"Could not find coordinate from candidates: {candidates}")


def unique_finite_sorted(values: np.ndarray) -> np.ndarray:
    arr = np.asarray(values, dtype=float).ravel()
    arr = arr[np.isfinite(arr)]
    if arr.size == 0:
        return arr
    return np.sort(np.unique(np.round(arr, 10)))


def extract_axis_values(ds: xr.Dataset, coord_name: str) -> np.ndarray:
    coord = ds[coord_name]
    values = np.asarray(coord.values, dtype=float)

    if values.ndim == 1:
        return values

    if values.ndim >= 2:
        return unique_finite_sorted(values)

    vals = unique_finite_sorted(values)
    if vals.size == 0:
        raise ValueError(f"Coordinate {coord_name} has no finite values.")
    return vals


def infer_axis_order(ds: xr.Dataset, coord_name: str, axis: str) -> str:
    coord = ds[coord_name]
    values = np.asarray(coord.values, dtype=float)

    if values.ndim == 1 and values.size >= 2:
        if values[0] > values[-1]:
            return "NtoS" if axis == "lat" else "decreasing"
        if values[0] < values[-1]:
            return "StoN" if axis == "lat" else "increasing"

    if values.ndim == 2:
        if axis == "lat":
            col = values[:, 0]
            col = col[np.isfinite(col)]
            if col.size >= 2:
                if col[0] > col[-1]:
                    return "NtoS"
                if col[0] < col[-1]:
                    return "StoN"

            row = values[0, :]
            row = row[np.isfinite(row)]
            if row.size >= 2:
                if row[0] > row[-1]:
                    return "NtoS"
                if row[0] < row[-1]:
                    return "StoN"

        if axis == "lon":
            row = values[0, :]
            row = row[np.isfinite(row)]
            if row.size >= 2:
                if row[0] < row[-1]:
                    return "increasing"
                if row[0] > row[-1]:
                    return "decreasing"

    return "unknown"


def infer_resolution(values: np.ndarray) -> float:
    vals = np.asarray(values, dtype=float).ravel()
    vals = vals[np.isfinite(vals)]
    vals = np.sort(np.unique(np.round(vals, 10)))

    if vals.size < 2:
        return float("nan")

    diffs = np.diff(vals)
    diffs = diffs[(diffs > 0) & np.isfinite(diffs)]

    if diffs.size == 0:
        return float("nan")

    return float(np.min(diffs))


def infer_time_info(ds: xr.Dataset, timestep_hours_arg: float) -> dict[str, Any]:
    if "time" not in ds.coords:
        return {
            "ntime": 0,
            "time_start": "N/A",
            "time_end": "N/A",
            "time_step_hours_inferred": timestep_hours_arg,
        }

    times = pd.to_datetime(ds["time"].values)
    ntime = len(times)

    if ntime >= 2:
        dt_seconds = np.diff(times.values).astype("timedelta64[s]").astype(float)
        dt_seconds = dt_seconds[np.isfinite(dt_seconds)]
        dt_hours = float(np.median(dt_seconds) / 3600.0) if dt_seconds.size else timestep_hours_arg
    else:
        dt_hours = timestep_hours_arg

    return {
        "ntime": ntime,
        "time_start": str(times[0]) if ntime else "N/A",
        "time_end": str(times[-1]) if ntime else "N/A",
        "time_step_hours_inferred": dt_hours,
    }


def read_netcdf_metadata(args: argparse.Namespace) -> dict[str, Any] | None:
    files = find_files(args.outdir, args.pattern)
    if not files:
        return None

    sample_file = files[0]
    ds = xr.open_dataset(sample_file)

    if args.variable not in ds.data_vars:
        available = list(ds.data_vars)
        raise KeyError(f"Variable '{args.variable}' not found in {sample_file}. Available: {available}")

    lat_name = find_coord_name(ds, ["lat", "latitude", "y"])
    lon_name = find_coord_name(ds, ["lon", "longitude", "x"])

    lat_values = extract_axis_values(ds, lat_name)
    lon_values = extract_axis_values(ds, lon_name)

    lat_unique = unique_finite_sorted(lat_values)
    lon_unique = unique_finite_sorted(lon_values)

    ny = int(lat_unique.size)
    nx = int(lon_unique.size)

    dlat = infer_resolution(lat_values)
    dlon = infer_resolution(lon_values)

    if np.isfinite(dlat) and np.isfinite(dlon) and math.isclose(dlat, dlon, rel_tol=1.0e-4, abs_tol=1.0e-8):
        gsize = dlat
    elif np.isfinite(dlat) and not np.isfinite(dlon):
        gsize = dlat
    elif np.isfinite(dlon) and not np.isfinite(dlat):
        gsize = dlon
    else:
        gsize = float("nan")

    olat = infer_axis_order(ds, lat_name, "lat")

    lon_min = float(np.nanmin(lon_values))
    lon_max = float(np.nanmax(lon_values))
    lat_min = float(np.nanmin(lat_values))
    lat_max = float(np.nanmax(lat_values))

    westin = lon_min - dlon * 0.5 if np.isfinite(dlon) else float("nan")
    eastin = lon_max + dlon * 0.5 if np.isfinite(dlon) else float("nan")
    southin = lat_min - dlat * 0.5 if np.isfinite(dlat) else float("nan")
    northin = lat_max + dlat * 0.5 if np.isfinite(dlat) else float("nan")

    var = ds[args.variable]
    units = str(var.attrs.get("units", "unknown"))
    long_name = str(var.attrs.get("long_name", ""))
    fill_value = var.encoding.get("_FillValue", var.attrs.get("_FillValue", var.attrs.get("missing_value", "N/A")))
    time_info = infer_time_info(ds, args.timestep_hours)

    file_rule = {"daily": "runoff_YYYYMMDD.nc", "monthly": "runoff_YYYYMM.nc", "yearly": "runoff_YYYY.nc"}[args.merge_unit]

    return {
        "source_format": "netcdf",
        "files": files,
        "sample_file": sample_file,
        "nx": nx,
        "ny": ny,
        "gsize": gsize,
        "westin": westin,
        "eastin": eastin,
        "northin": northin,
        "southin": southin,
        "olat": olat,
        "dlon": dlon,
        "dlat": dlat,
        "forcing_timestep_hours": float(args.timestep_hours),
        "time_info": time_info,
        "file_rule": file_rule,
        "lon_name": lon_name,
        "lat_name": lat_name,
        "lon_min_center": lon_min,
        "lon_max_center": lon_max,
        "lat_min_center": lat_min,
        "lat_max_center": lat_max,
        "variable_units": units,
        "variable_long_name": long_name,
        "fill_value": fill_value,
    }


def main() -> int:
    args = parse_args()

    try:
        if args.outfile.exists() and not args.overwrite:
            raise FileExistsError(f"Output file exists: {args.outfile}. Use --overwrite to replace it.")

        nc_meta = read_netcdf_metadata(args)
        primary = nc_meta
        if primary is None:
            raise FileNotFoundError("No NetCDF files found to inspect.")

        forcing_timestep_hours = float(primary.get("forcing_timestep_hours", args.timestep_hours))
        drofunit = 1000.0 * forcing_timestep_hours * 3600.0

        args.outfile.parent.mkdir(parents=True, exist_ok=True)

        netcdf_rule = primary["file_rule"]

        lines: list[str] = []
        lines.append("#==========================================================")
        lines.append("# CaMa-Flood runoff forcing information")
        lines.append("#==========================================================")
        lines.append(f"# Sample name: {args.sample_name}")
        lines.append(f"# Source format inspected: {primary['source_format']}")
        lines.append(f"# Created from: {primary.get('sample_file', 'N/A')}")
        if args.start or args.end:
            lines.append(f"# Requested period: {args.start} to {args.end}")
        lines.append("")

        lines.append("#----------------------------------------------------------")
        lines.append("# 1. Parameters for generating the CaMa-Flood input mapping table")
        lines.append("#----------------------------------------------------------")
        lines.append(f"GRSIZEIN={fmt_float(primary['gsize'])}       # input grid size [degree]")
        lines.append(f"WESTIN={fmt_float(primary['westin'])}        # input domain west edge")
        lines.append(f"EASTIN={fmt_float(primary['eastin'])}        # input domain east edge")
        lines.append(f"NORTHIN={fmt_float(primary['northin'])}      # input domain north edge")
        lines.append(f"SOUTHIN={fmt_float(primary['southin'])}      # input domain south edge")
        lines.append(f"OLAT=\"{primary['olat']}\"        # north-south order of input data")
        lines.append("")
        lines.append("# Example:")
        lines.append("# ./generate_inpmat $MAPTAG $GRSIZEIN $WESTIN $EASTIN $NORTHIN $SOUTHIN $OLAT diminfo.txt inpmat.bin")
        lines.append("")

        lines.append("#----------------------------------------------------------")
        lines.append("# 2. Common CaMa-Flood namelist parameters")
        lines.append("#----------------------------------------------------------")
        lines.append("#============================")
        lines.append("#*** 1f. forcing setting")
        lines.append(f"IFRQ_INP=\"{fmt_float(forcing_timestep_hours, 3)}\"       # input forcing frequency [hour]")
        lines.append(f"DROFUNIT=\"{fmt_float(drofunit, 3)}\"       # [mm/{fmt_float(forcing_timestep_hours, 3)}h -> m/s] runoff unit conversion")
        lines.append("# Unit conversion:")
        lines.append("#   runoff_m_per_s = runoff_mm_per_timestep / DROFUNIT")
        lines.append("")

        lines.append("#----------------------------------------------------------")
        lines.append("# 3. NetCDF runoff forcing namelist parameters")
        lines.append("#----------------------------------------------------------")
        lines.append("#----- for netCDF runoff forcing")
        lines.append(f"CROFPRE=\"{args.prefix}\"       # runoff file prefix")
        lines.append(f"CROFSUF=\"{args.suffix}\"       # runoff file suffix")
        lines.append('LINPCDF=.TRUE.')
        grouping = {"daily": "DAY", "monthly": "MON", "yearly": "YEAR"}[args.merge_unit]
        lines.append(f'CROFFREQ="{grouping}"')
        lines.append('CVNTIME="time"')
        lines.append(f"CVNROF=\"{args.variable}\"       # netCDF runoff variable name")
        lines.append(f"# File naming rule: {netcdf_rule}")
        lines.append("")

        lines.append("#----------------------------------------------------------")
        lines.append("# 4. Source metadata summary")
        lines.append("#----------------------------------------------------------")
        lines.append(f"source_format={primary['source_format']}")
        lines.append(f"nx={primary['nx']}")
        lines.append(f"ny={primary['ny']}")
        lines.append(f"dlon={fmt_float(primary['dlon'])}")
        lines.append(f"dlat={fmt_float(primary['dlat'])}")
        lines.append(f"forcing_timestep_hours={fmt_float(forcing_timestep_hours, 3)}")
        lines.append(f"time_step_hours_config={fmt_float(args.timestep_hours, 3)}")
        lines.append(f"time_step_hours_inferred={fmt_float(primary['time_info']['time_step_hours_inferred'], 3)}")
        lines.append(f"ntime_in_sample={primary['time_info']['ntime']}")
        lines.append(f"time_start_in_sample={primary['time_info']['time_start']}")
        lines.append(f"time_end_in_sample={primary['time_info']['time_end']}")

        if nc_meta is not None:
            lines.append("")
            lines.append("# NetCDF metadata")
            lines.append(f"netcdf_files_found={len(nc_meta['files'])}")
            lines.append(f"netcdf_sample_file={nc_meta['sample_file']}")
            lines.append(f"lon_name={nc_meta['lon_name']}")
            lines.append(f"lat_name={nc_meta['lat_name']}")
            lines.append(f"lon_min_center={fmt_float(nc_meta['lon_min_center'])}")
            lines.append(f"lon_max_center={fmt_float(nc_meta['lon_max_center'])}")
            lines.append(f"lat_min_center={fmt_float(nc_meta['lat_min_center'])}")
            lines.append(f"lat_max_center={fmt_float(nc_meta['lat_max_center'])}")
            lines.append(f"variable_name={args.variable}")
            lines.append(f"variable_units={nc_meta['variable_units']}")
            lines.append(f"variable_long_name={nc_meta['variable_long_name']}")
            lines.append(f"fill_value={nc_meta['fill_value']}")

        lines.append("")

        args.outfile.write_text("\n".join(lines), encoding="utf-8")
        print(f"[INFO] Wrote runoff information file: {args.outfile}")
        return 0

    except Exception as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())

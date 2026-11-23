#!/usr/bin/env python3
"""Extract Step 21 gauge-cell model flows and supplied observations for overlay."""

from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime
from pathlib import Path

from netCDF4 import Dataset, num2date
import numpy as np

STATION_NAMES = {153: "Lobith", 63: "Speyer", 28: "Maxau"}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as stream:
        return list(csv.DictReader(stream))


def date_text(value) -> str:
    return value.strftime("%Y-%m-%dT%H:%M:%S")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tutorial-dir", type=Path, required=True)
    parser.add_argument("--model-netcdf", type=Path, required=True)
    parser.add_argument("--observation-csv", type=Path, required=True)
    parser.add_argument("--allocation-csv", type=Path, required=True)
    parser.add_argument("--dataset-json", type=Path, required=True)
    parser.add_argument("--output-csv", type=Path, required=True)
    parser.add_argument("--summary-json", type=Path, required=True)
    parser.add_argument("--start", default="2021-07-12T00:00:00")
    parser.add_argument("--end-exclusive", default="2021-07-17T00:00:00")
    args = parser.parse_args()

    tutorial_root = args.tutorial_dir.resolve()

    def relative_path(path: Path) -> str:
        return path.resolve().relative_to(tutorial_root).as_posix()

    start = datetime.fromisoformat(args.start)
    end = datetime.fromisoformat(args.end_exclusive)
    if end <= start:
        raise ValueError("end-exclusive must be later than start")

    allocation = {int(row["station_id"]): row for row in read_csv(args.allocation_csv)}
    if set(STATION_NAMES) - allocation.keys():
        raise ValueError("Step 21 allocation is missing one or more requested stations")

    model_rows: list[dict[str, str]] = []
    model_peaks: dict[str, dict[str, object]] = {}
    with Dataset(args.model_netcdf) as ds:
        if "outflw" not in ds.variables or "time" not in ds.variables:
            raise ValueError(f"Expected outflw and time variables in {args.model_netcdf}")
        flow = ds.variables["outflw"]
        time_var = ds.variables["time"]
        if flow.dimensions != ("time", "lat", "lon"):
            raise ValueError(f"Unexpected outflw dimensions: {flow.dimensions}")
        if getattr(flow, "units", None) != "m3/s":
            raise ValueError(f"Expected verified model outflw units m3/s, got {getattr(flow, 'units', None)!r}")
        time_units = getattr(time_var, "units", None)
        calendar = getattr(time_var, "calendar", "standard")
        if not time_units:
            raise ValueError("Model time coordinate has no CF units")
        decoded = num2date(time_var[:], units=time_units, calendar=calendar,
                           only_use_cftime_datetimes=False, only_use_python_datetimes=True)
        model_times = [datetime(value.year, value.month, value.day, value.hour, value.minute, value.second)
                       for value in decoded]
        keep = [i for i, t in enumerate(model_times) if start <= t < end]
        if not keep:
            raise ValueError("No hourly model records fall within the requested time range")

        for station_id, name in STATION_NAMES.items():
            row = allocation[station_id]
            if row["station_name"] != name:
                raise ValueError(f"Station {station_id} name differs from Step 21 allocation")
            y, x = int(row["model_row_0based"]), int(row["model_col_0based"])
            if not (0 <= y < flow.shape[1] and 0 <= x < flow.shape[2]):
                raise ValueError(f"Step 21 cell for {name} is outside the model output grid: {(y, x)}")
            values = np.ma.asarray(flow[keep, y, x], dtype=np.float64).filled(np.nan)
            if not np.isfinite(values).any():
                raise ValueError(f"No finite model values for {name} at allocation cell {(y, x)}")
            station_peak = int(np.nanargmax(values))
            model_peaks[str(station_id)] = {
                "station_name": name,
                "cell_row_0based": y,
                "cell_col_0based": x,
                "valid_records": int(np.isfinite(values).sum()),
                "peak_discharge": float(values[station_peak]),
                "peak_datetime_utc": model_times[keep[station_peak]].isoformat() + "Z",
                "temporal_semantics": getattr(flow, "cell_methods", "not specified"),
            }
            for index, value in zip(keep, values):
                if np.isfinite(value):
                    timestamp = model_times[index]
                    iso = timestamp.isoformat(timespec="seconds")
                    model_rows.append({
                        "station_id": str(station_id), "station_name": name, "source": "model",
                        "datetime_original": iso, "datetime_comparison": iso + "Z",
                        "discharge": f"{float(value):.9g}", "unit": "m3/s",
                        "time_reference_status": "UTC interpreted per CF default; file has no global Conventions attribute",
                    })
        model_metadata = {
            "path": relative_path(args.model_netcdf), "variable": "outflw",
            "dimensions": list(flow.dimensions), "units": flow.units,
            "cell_methods": getattr(flow, "cell_methods", None),
            "time_units": time_units, "calendar": calendar,
            "time_reference": "UTC interpreted under CF conventions because timezone is omitted; the file has no global Conventions attribute",
            "time_reference_source": "https://cfconventions.org/Data/cf-conventions/cf-conventions-1.11/cf-conventions.html",
            "records_in_comparison_window": len(keep),
            "first_record_in_window": model_times[keep[0]].isoformat() + "Z",
            "last_record_in_window": model_times[keep[-1]].isoformat() + "Z",
        }

    observed_rows: list[dict[str, str]] = []
    observed_peaks: dict[str, dict[str, object]] = {}
    records = read_csv(args.observation_csv)
    for station_id, name in STATION_NAMES.items():
        values_for_station: list[tuple[datetime, float]] = []
        for row in records:
            timestamp = datetime.strptime(row["Timestamp"], "%Y-%m-%d %H:%M")
            if not (start <= timestamp < end):
                continue
            raw = row[str(station_id)]
            value = float(raw)
            if not np.isfinite(value):
                continue
            values_for_station.append((timestamp, value))
            observed_rows.append({
                "station_id": str(station_id), "station_name": name, "source": "observation",
                "datetime_original": row["Timestamp"],
                "datetime_comparison": timestamp.isoformat(timespec="seconds"),
                "discharge": f"{value:.9g}", "unit": "not declared in source",
                "time_reference_status": "timezone unknown; source timestamp plotted as supplied",
            })
        if not values_for_station:
            raise ValueError(f"No observation records for {name} in requested time range")
        peak_time, peak_value = max(values_for_station, key=lambda item: item[1])
        observed_peaks[str(station_id)] = {
            "station_name": name,
            "valid_records": len(values_for_station),
            "peak_discharge": peak_value,
            "peak_datetime_as_supplied": peak_time.isoformat(timespec="minutes"),
            "temporal_semantics": "provider-described six-hour mean with interval-end labels",
        }

    args.output_csv.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = ["station_id", "station_name", "source", "datetime_original",
                  "datetime_comparison", "discharge", "unit", "time_reference_status"]
    with args.output_csv.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(model_rows)
        writer.writerows(observed_rows)

    source_meta = json.loads(args.dataset_json.read_text(encoding="utf-8"))
    observation_info = source_meta["time_series"]
    summary = {
        "schema_version": 1,
        "comparison_period": {"start_inclusive": args.start, "end_exclusive": args.end_exclusive},
        "overlay_interpretation": "provisional nominal-label overlay; no timezone conversion or temporal resampling",
        "inputs": {
            "model_netcdf": relative_path(args.model_netcdf),
            "observation_csv": relative_path(args.observation_csv),
            "step21_allocation_csv": relative_path(args.allocation_csv),
            "step04_dataset_metadata": relative_path(args.dataset_json),
        },
        "model": model_metadata,
        "observation": {
            "path": relative_path(args.observation_csv),
            "cadence": observation_info.get("cadence"),
            "value_semantics": observation_info.get("value_semantics"),
            "timezone": observation_info.get("timezone"),
            "unit": observation_info.get("discharge_unit"),
            "time_reference_status": "unresolved; original labels retained and overlaid without adjustment",
            "interval_end_note": "provider describes each supplied value as a six-hour mean labelled at interval end; source file has no bounds or cell_methods",
            "valid_records_per_station": next(iter(observed_peaks.values()))["valid_records"],
        },
        "station_series": {
            str(station_id): {"model": model_peaks[str(station_id)],
                              "observation": observed_peaks[str(station_id)]}
            for station_id in STATION_NAMES
        },
        "processing": {
            "model_cell_indexing": "Step 21 model_row_0based/model_col_0based applied to outflw(time,lat,lon)",
            "observation_source_order": "CSV Timestamp labels and station ID columns retained",
            "temporal_pairing_or_interpolation": "none",
            "value_conversion": "none",
            "timeseries_csv": relative_path(args.output_csv),
        },
        "limitations": [
            "Observation discharge unit is not declared; numerical overlay does not establish unit equivalence.",
            "Observation timezone is unknown; apparent timing differences may include a clock-reference offset.",
            "Observation values are provider-described six-hour means with interval-end labels; model output is hourly time mean.",
            "This is an exploratory hydrograph comparison, not a skill assessment; no metrics were calculated.",
        ],
    }
    args.summary_json.parent.mkdir(parents=True, exist_ok=True)
    args.summary_json.write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Wrote {len(model_rows)} model and {len(observed_rows)} observation records to {args.output_csv}")
    print(f"Wrote summary metadata to {args.summary_json}")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Inspect the supplied Rhine discharge files and write Step 4 metadata."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from datetime import datetime
from pathlib import Path

import netCDF4
import numpy as np


SOURCE_NAMES = {
    "allstations.csv": "Station metadata supplied with the dataset",
    "Qobs_06_2021_st153_63_28.csv": "ECMWF-supplied discharge time series (CSV)",
    "Qobs_06_2021_st153_63_28.nc": "ECMWF-supplied discharge time series (NetCDF4)",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def read_csv_timeseries(path: Path):
    with path.open(newline="", encoding="utf-8-sig") as stream:
        reader = csv.DictReader(stream)
        rows = list(reader)
        station_ids = [int(name) for name in reader.fieldnames[1:]]
    times = [datetime.strptime(row["Timestamp"], "%Y-%m-%d %H:%M") for row in rows]
    values = {station_id: np.array([float(row[str(station_id)]) if row[str(station_id)] else np.nan for row in rows], dtype=np.float64)
              for station_id in station_ids}
    return station_ids, times, values


def read_station_metadata(path: Path):
    with path.open(newline="", encoding="utf-8-sig") as stream:
        rows = list(csv.DictReader(stream))
    stations = {int(row["Id"]): row for row in rows}
    if len(stations) != len(rows):
        raise ValueError("Duplicate station IDs in allstations.csv")
    return stations


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--tutorial-dir", type=Path, required=True)
    args = parser.parse_args()
    root = args.tutorial_dir.resolve()
    source_dir = root / "observation" / "stations_data"
    station_file = source_dir / "allstations.csv"
    csv_file = source_dir / "Qobs_06_2021_st153_63_28.csv"
    nc_file = source_dir / "Qobs_06_2021_st153_63_28.nc"
    for path in (station_file, csv_file, nc_file):
        if not path.is_file():
            raise FileNotFoundError(path)

    station_ids, times, csv_values = read_csv_timeseries(csv_file)
    stations = read_station_metadata(station_file)
    if set(station_ids) != set(stations):
        raise ValueError("Station IDs differ between time series and allstations.csv")
    if len(times) != 1460 or any((b - a).total_seconds() != 21600 for a, b in zip(times, times[1:])):
        raise ValueError("Unexpected record count or non-six-hour timestamp spacing")
    if times[0] != datetime(2021, 1, 1, 6) or times[-1] != datetime(2022, 1, 1, 0):
        raise ValueError("Unexpected supplied time coverage")

    with netCDF4.Dataset(nc_file) as dataset:
        nc_station_ids = [int(value) for value in dataset.variables["station"][:]]
        time_var = dataset.variables["time"]
        time_units = str(time_var.units)
        calendar = str(getattr(time_var, "calendar", "standard"))
        nc_times = list(netCDF4.num2date(time_var[:], time_var.units, time_var.calendar,
                                         only_use_cftime_datetimes=False,
                                         only_use_python_datetimes=True))
        nc_times = [value.replace(tzinfo=None) for value in nc_times]
        discharge = np.ma.asarray(dataset.variables["discharge"][:], dtype=np.float32)
        description = str(getattr(dataset, "description", ""))
        history = str(getattr(dataset, "history", ""))
        nc_dimensions = {name: len(dim) for name, dim in dataset.dimensions.items()}
        nc_variable = dataset.variables["discharge"]
        nc_units = getattr(nc_variable, "units", None)
        nc_fill = str(getattr(nc_variable, "_FillValue", ""))
        nc_variable_attributes = sorted(nc_variable.ncattrs())
    if nc_station_ids != station_ids or nc_times != times:
        raise ValueError("CSV and NetCDF station order or timestamps differ")
    if discharge.shape != (len(times), len(station_ids)):
        raise ValueError(f"Unexpected NetCDF discharge shape: {discharge.shape}")

    full_year = (times[0], times[-1])
    july_start, july_end = datetime(2021, 7, 1), datetime(2021, 8, 1)
    july_indices = [i for i, value in enumerate(times) if july_start < value <= july_end]
    if len(july_indices) != 124:
        raise ValueError(f"Expected 124 July interval-end records, got {len(july_indices)}")

    inventory_rows = []
    allocation = []
    representation_differences = []
    for column, station_id in enumerate(station_ids):
        metadata = stations[station_id]
        csv_series = csv_values[station_id]
        nc_series = np.asarray(discharge[:, column].filled(np.nan), dtype=np.float32)
        valid = np.isfinite(csv_series) & np.isfinite(nc_series)
        float32_equal = bool(np.array_equal(csv_series.astype(np.float32), nc_series, equal_nan=True))
        finite_pair = np.isfinite(csv_series) & np.isfinite(nc_series)
        abs_difference = np.abs(csv_series[finite_pair] - nc_series[finite_pair].astype(np.float64))
        relative_difference = abs_difference / np.abs(csv_series[finite_pair])
        max_difference_index = int(np.argmax(abs_difference)) if len(abs_difference) else 0
        pair_times = [value for value, is_valid in zip(times, finite_pair) if is_valid]
        representation_differences.append({
            "station_id": station_id,
            "maximum_absolute_difference": float(abs_difference[max_difference_index]) if len(abs_difference) else None,
            "maximum_relative_difference": float(relative_difference.max()) if len(relative_difference) else None,
            "example_time_as_supplied": pair_times[max_difference_index].isoformat(sep=" ") if len(pair_times) else None,
        })
        july_values = csv_series[july_indices]
        july_peak_index = july_indices[int(np.nanargmax(july_values))]
        july_peak_time = times[july_peak_index]
        inventory_rows.append({
            "station_id": station_id,
            "station_name": metadata["Name"],
            "river": metadata["River"],
            "country": metadata["Country"],
            "latitude": metadata["StatLat"],
            "longitude": metadata["StatLon"],
            "source_dataset": "CEMS Observed Discharge Time Series",
            "available_start": times[0].isoformat(sep=" "),
            "available_end": times[-1].isoformat(sep=" "),
            "temporal_resolution": "6 hours",
            "record_count": len(times),
            "missing_record_count": int((~valid).sum()),
            "data_availability_status": "complete_regular_series" if valid.all() else "missing_values_present",
            "discharge_unit": "not declared",
            "source_timezone": "not declared",
            "full_year_min": f"{np.nanmin(csv_series):.6f}",
            "full_year_max": f"{np.nanmax(csv_series):.6f}",
            "full_year_mean": f"{np.nanmean(csv_series):.6f}",
            "july_peak_value": f"{csv_series[july_peak_index]:.6f}",
            "july_peak_time_as_supplied": july_peak_time.isoformat(sep=" "),
            "july_record_count": len(july_indices),
        })
        alloc = {"station_id": station_id, "station_name": metadata["Name"], "groups": {}}
        for prefix in ("Cama1", "Cama3", "Cama6", "Cama15"):
            alloc["groups"][prefix] = {
                "longitude": float(metadata[f"{prefix}lon"]),
                "latitude": float(metadata[f"{prefix}lat"]),
                "area_value_unit_undeclared": float(metadata[f"{prefix}area"]),
                "row": int(metadata[f"{prefix}row"]),
                "column": int(metadata[f"{prefix}col"]),
            }
        allocation.append(alloc)

    metadata_root = root / "metadata"
    metadata_root.mkdir(exist_ok=True)
    csv_out = metadata_root / "04_discharge_inventory.csv"
    fields = list(inventory_rows[0])
    with csv_out.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(inventory_rows)

    file_records = []
    for filename, role in SOURCE_NAMES.items():
        path = source_dir / filename
        file_records.append({"path": path.relative_to(root).as_posix(), "role": role,
                             "size_bytes": path.stat().st_size, "sha256": sha256(path)})
    dataset_json = {
        "schema_version": 1,
        "step": "04",
        "dataset_name": "CEMS Observed Discharge Time Series",
        "provider": "ECMWF; supplied by Cinzia Mazzetti",
        "redistribution": {"status": "maintainer_confirmed_for_tutorial", "formal_open_license": "not identified"},
        "original_observing_agency": None,
        "source_files": file_records,
        "source_layout": {
            "station_metadata_csv": {"records": len(stations), "columns": 27},
            "discharge_csv": {"records": len(times), "columns": 1 + len(station_ids),
                              "header": ["Timestamp", *[str(value) for value in station_ids]],
                              "timestamp_format": "YYYY-MM-DD HH:MM; no timezone suffix"},
            "discharge_netcdf": {"format": "NETCDF4", "dimensions": nc_dimensions,
                                 "variables": {"discharge": {"type": str(nc_variable.dtype), "dimensions": ["time", "station"], "units": nc_units or None},
                                               "time": {"type": str(time_var.dtype), "units": time_units, "calendar": calendar},
                                               "station": {"type": "int64", "values": nc_station_ids}}},
        },
        "time_series": {
            "record_count_per_station": len(times),
            "station_ids_in_time_series_order": station_ids,
            "start_as_supplied": times[0].isoformat(sep=" "),
            "end_as_supplied": times[-1].isoformat(sep=" "),
            "timezone": None,
            "cadence": "6 hours",
            "value_semantics": "Six-hour mean discharge with interval-end timestamps, as described by provider correspondence; source files do not encode bounds/cell_methods.",
            "discharge_unit": nc_units or None,
            "csv_netcdf_station_time_match": True,
            "csv_values_cast_to_netcdf_float32_exact": all(
                np.array_equal(csv_values[sid].astype(np.float32), np.asarray(discharge[:, col].filled(np.nan), dtype=np.float32), equal_nan=True)
                for col, sid in enumerate(nc_station_ids)),
            "netcdf_dimensions": nc_dimensions,
            "netcdf_time_units": time_units,
            "netcdf_calendar": calendar,
            "netcdf_discharge_type": str(nc_variable.dtype),
            "netcdf_discharge_attributes": nc_variable_attributes,
            "netcdf_description": description,
            "netcdf_history": history or None,
            "netcdf_fill_value": nc_fill,
            "netcdf_quality_flags": "not present",
            "missing_csv_values_total": int(sum((~np.isfinite(v)).sum() for v in csv_values.values())),
            "missing_netcdf_values_total": int((~np.isfinite(np.asarray(discharge.filled(np.nan)))).sum()),
            "nonpositive_discharge_values_total": int(sum((v[np.isfinite(v)] <= 0).sum() for v in csv_values.values())),
            "duplicate_timestamps": len(times) - len(set(times)),
            "representation_difference_summary": representation_differences,
        },
        "stations": [
            {"station_id": sid, "name": stations[sid]["Name"], "river": stations[sid]["River"],
             "country": stations[sid]["Country"], "longitude": float(stations[sid]["StatLon"]),
             "latitude": float(stations[sid]["StatLat"]), "provisional_area_value_unit_undeclared": float(stations[sid]["ProvArea"])}
            for sid in station_ids
        ],
        "station_discrepancy": "Bonn/6 is absent; supplied files contain Speyer/63. Do not treat Speyer as a Bonn substitute.",
        "model_allocation_reference": {
            "description": "Literal Cama1/Cama3/Cama6/Cama15 fields copied by station ID from allstations.csv. They are distinct from station coordinates and have no declared units or verified map version/grid interpretation.",
            "records": allocation,
            "historical_numerical_check": {
                "source": "Earlier read-only inventory inspection, 2026-11-20; not rerun by the Step 4 script",
                "result": "All 12 supplied CamaN coordinate pairs were consistent within 3.333333343e-06 degrees with the cell-centre equations longitude=-180+(column+0.5)*(N/60), latitude=90-(row+0.5)*(N/60), for N=1,3,6,15.",
                "interpretation": "Supports but does not prove the stated global-grid spacing and zero-based indices. It is not a check against the target map, map version, datum or allocation convention.",
            },
        },
        "july_2021": {"selection": "end labels in (2021-07-01 00:00, 2021-08-01 00:00]", "record_count_per_station": len(july_indices),
                       "peaks": [{"station_id": row["station_id"], "station_name": row["station_name"],
                                  "value": float(row["july_peak_value"]), "time_as_supplied": row["july_peak_time_as_supplied"]}
                                 for row in inventory_rows]},
        "next_step_handoff": {"time_series_csv": "observation/stations_data/Qobs_06_2021_st153_63_28.csv",
                              "station_inventory": "metadata/04_discharge_inventory.csv", "status": "prepared_for_later_matching; units/timezone/map allocation remain unverified"},
    }
    json_out = metadata_root / "04_discharge_dataset.json"
    json_out.write_text(json.dumps(dataset_json, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Wrote {csv_out.relative_to(root)} and {json_out.relative_to(root)}")
    print(f"Validated {len(station_ids)} stations × {len(times)} records; float32 CSV/NetCDF equality: {dataset_json['time_series']['csv_values_cast_to_netcdf_float32_exact']}")
    for row in inventory_rows:
        print(f"{row['station_id']} {row['station_name']}: July max {row['july_peak_value']} at {row['july_peak_time_as_supplied']}")


if __name__ == "__main__":
    main()

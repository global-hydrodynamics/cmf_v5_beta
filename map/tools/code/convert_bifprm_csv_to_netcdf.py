#!/usr/bin/env python3
"""Convert the finalized bifprm.csv table to its static NetCDF-4 counterpart."""
from __future__ import annotations

import argparse
import csv
import os
from pathlib import Path
import re
import tempfile

import numpy as np


REQUIRED_COLUMNS = (
    "pth_id", "ix", "iy", "jx", "jy", "length", "elevtn", "depth",
    "riv_width", "start_lat", "start_lon", "end_lat", "end_lon", "ibsn", "jbsn",
)
INT_COLUMNS = ("pth_id", "ix", "iy", "jx", "jy", "ibsn", "jbsn")
FLOAT_COLUMNS = (
    "start_lat", "start_lon", "end_lat", "end_lon", "length", "elevtn", "depth", "riv_width",
)
OVERLAND_PATTERN = re.compile(r"^ovl_width_(\d+)$")


def load_table(path: Path) -> tuple[list[str], list[dict[str, str]], int]:
    with path.open("r", newline="", encoding="utf-8") as stream:
        reader = csv.DictReader(stream)
        raw_columns = reader.fieldnames
        if not raw_columns:
            raise ValueError(f"{path}: missing CSV header")
        columns = [name.strip() for name in raw_columns]
        reader.fieldnames = columns
        if len(columns) != len(set(columns)):
            raise ValueError(f"{path}: duplicate CSV column names")
        missing = [name for name in REQUIRED_COLUMNS if name not in columns]
        if missing:
            raise ValueError(f"{path}: missing required columns: {', '.join(missing)}")
        widths = []
        for name in columns:
            match = OVERLAND_PATTERN.fullmatch(name)
            if not match:
                if name.startswith("ovl_width_"):
                    raise ValueError(f"{path}: invalid overland width column {name!r}")
                continue
            index = int(match.group(1))
            if str(index) != match.group(1):
                raise ValueError(f"{path}: invalid overland width column {name!r}")
            widths.append((index, name))
        widths.sort()
        if [index for index, _ in widths] != list(range(1, len(widths) + 1)):
            raise ValueError(f"{path}: overland columns must be consecutive from ovl_width_1")
        rows = []
        for line_number, raw_row in enumerate(reader, 2):
            if None in raw_row:
                raise ValueError(f"{path}: malformed field count on CSV line {line_number}")
            rows.append({key.strip(): (value.strip() if value is not None else None)
                         for key, value in raw_row.items()})
    return columns, rows, len(widths)


def convert(csv_path: Path, output_path: Path) -> None:
    columns, rows, nlayer = load_table(csv_path)
    npath = len(rows)
    data: dict[str, np.ndarray] = {}
    for name in INT_COLUMNS:
        try:
            values = np.asarray([int(row[name]) for row in rows], dtype=np.int64)
        except (TypeError, ValueError) as exc:
            raise ValueError(f"{csv_path}: invalid integer values in {name}") from exc
        if values.size and (values.min() < np.iinfo(np.int32).min or values.max() > np.iinfo(np.int32).max):
            raise ValueError(f"{csv_path}: {name} exceeds the int32 range")
        data[name] = values.astype(np.int32)

    for name in FLOAT_COLUMNS:
        try:
            values = np.asarray([float(row[name]) for row in rows], dtype=np.float64)
        except (TypeError, ValueError) as exc:
            raise ValueError(f"{csv_path}: invalid numeric values in {name}") from exc
        if not np.isfinite(values).all():
            raise ValueError(f"{csv_path}: non-finite values in {name}")
        converted = values.astype(np.float32)
        if not np.isfinite(converted).all():
            raise ValueError(f"{csv_path}: values in {name} exceed the float32 range")
        data[name] = converted

    widths = np.empty((nlayer, npath), dtype=np.float32)
    for layer in range(1, nlayer + 1):
        name = f"ovl_width_{layer}"
        try:
            values = np.asarray([float(row[name]) for row in rows], dtype=np.float64)
        except (TypeError, ValueError) as exc:
            raise ValueError(f"{csv_path}: invalid numeric values in {name}") from exc
        if not np.isfinite(values).all():
            raise ValueError(f"{csv_path}: non-finite values in {name}")
        converted = values.astype(np.float32)
        if not np.isfinite(converted).all():
            raise ValueError(f"{csv_path}: values in {name} exceed the float32 range")
        widths[layer - 1, :] = converted

    ids = data["pth_id"]
    if not np.array_equal(ids, np.arange(1, npath + 1, dtype=np.int32)):
        raise ValueError(f"{csv_path}: pth_id must be consecutive from 1 and equal the data-row index")
    endpoints = list(zip(data["ix"], data["iy"], data["jx"], data["jy"]))
    seen: set[tuple[int, int, int, int]] = set()
    duplicate = []
    for endpoint in endpoints:
        if endpoint in seen:
            duplicate.append(endpoint)
        seen.add(endpoint)
    if duplicate:
        rendered = ", ".join(str(item) for item in duplicate[:10])
        raise ValueError(f"{csv_path}: duplicate endpoint tuples (ix,iy,jx,jy): {rendered}")
    if npath and np.any(data["ibsn"] > data["jbsn"]):
        raise ValueError(f"{csv_path}: ibsn and jbsn must be stored in ascending numeric order")

    try:
        from netCDF4 import Dataset
    except Exception as exc:
        raise RuntimeError("NetCDF conversion requires Python package netCDF4 (python3 -m pip install netCDF4)") from exc

    output_path.parent.mkdir(parents=True, exist_ok=True)
    file_descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{output_path.name}.", suffix=".tmp", dir=output_path.parent
    )
    os.close(file_descriptor)
    temporary_path = Path(temporary_name)
    try:
        with Dataset(temporary_path, "w", format="NETCDF4") as dataset:
            dataset.createDimension("path", npath if npath else None)
            if nlayer:
                dataset.createDimension("layer", nlayer)
            dataset.title = "Static CaMa-Flood bifurcation-path parameters"
            dataset.summary = "Converted without filtering, reordering, or recalculating values from bifprm.csv."
            dataset.format_version = "1.0"
            dataset.source_bifori = "bifori.csv"
            dataset.overland_layer_count = np.int32(nlayer)
            dataset.pth_id_semantics = "One-based row index assigned after path filtering; map-configuration-specific."
            dataset.endpoint_coordinate_definition = (
                "Start coordinates retain bifori.csv values; end coordinates are unit-catchment outlet coordinates "
                "from lonlat.bin records 1 (longitude) and 2 (latitude) at (jx,jy)."
            )
            dataset.basin_id_definition = "ibsn and jbsn are endpoint basin IDs stored in ascending numeric order."
            dataset.source_map = csv_path.resolve().parent.name

            descriptions = {
                "pth_id": ("Bifurcation path row identifier", "1", None),
                "ix": ("Starting x grid index", "1", "Fortran-style one-based map column index."),
                "iy": ("Starting y grid index", "1", "Fortran-style one-based map row index."),
                "jx": ("Ending x grid index", "1", "Fortran-style one-based map column index."),
                "jy": ("Ending y grid index", "1", "Fortran-style one-based map row index."),
                "start_lat": ("Starting latitude from bifori.csv", "degrees_north", None),
                "start_lon": ("Starting longitude from bifori.csv", "degrees_east", None),
                "end_lat": ("Unit-catchment outlet latitude at (jx,jy)", "degrees_north", None),
                "end_lon": ("Unit-catchment outlet longitude at (jx,jy)", "degrees_east", None),
                "length": ("Bifurcation-path length", "m", None),
                "elevtn": ("Bifurcation-path elevation", "m", None),
                "depth": ("Estimated bifurcation-channel depth", "m", None),
                "riv_width": ("River-channel bifurcation width", "m", "Distinct from overland bifurcation layers."),
                "ibsn": ("Smaller numeric endpoint basin identifier", "1", "Stored in ascending order with jbsn; not a directional endpoint label."),
                "jbsn": ("Larger or equal numeric endpoint basin identifier", "1", "Stored in ascending order with ibsn; not a directional endpoint label."),
            }
            for name in ("pth_id", "ix", "iy", "jx", "jy", "start_lat", "start_lon",
                         "end_lat", "end_lon", "length", "elevtn", "depth", "riv_width", "ibsn", "jbsn"):
                long_name, units, description = descriptions[name]
                variable = dataset.createVariable(
                    name, "i4" if name in INT_COLUMNS else "f4", ("path",),
                    zlib=True, complevel=3, shuffle=True, fill_value=False,
                )
                variable.long_name = long_name
                variable.units = units
                if description:
                    variable.description = description
                if name == "depth":
                    variable.missing_value = np.float32(-9999.0)
                variable[:] = data[name]

            if nlayer:
                width_variable = dataset.createVariable(
                    "ovl_width", "f4", ("layer", "path"),
                    zlib=True, complevel=3, shuffle=True, fill_value=False,
                )
                width_variable.long_name = "Overland bifurcation width by overland layer"
                width_variable.units = "m"
                width_variable.description = "Layer index k corresponds to CSV column ovl_width_k; layer indexing starts at 1."
                width_variable[:] = widths
        os.replace(temporary_path, output_path)
    except Exception:
        temporary_path.unlink(missing_ok=True)
        raise


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("csv_file", type=Path, help="finalized bifprm.csv table")
    parser.add_argument(
        "netcdf_file", nargs="?", type=Path,
        help="output path (default: bifprm.nc next to the CSV)",
    )
    args = parser.parse_args()
    output_path = args.netcdf_file or args.csv_file.with_name("bifprm.nc")
    try:
        convert(args.csv_file, output_path)
    except (OSError, ValueError, RuntimeError) as exc:
        parser.exit(1, f"ERROR: {exc}\n")
    print(f"Created {output_path} from {args.csv_file}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

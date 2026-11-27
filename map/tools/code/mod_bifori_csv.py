# SPDX-License-Identifier: Apache-2.0
"""Read and write FLOW's named bifurcation-source CSV interface."""
from dataclasses import dataclass
import csv
from io import StringIO
import re
from pathlib import Path

import numpy as np


INTEGER_FIELDS = ('path_id', 'ix', 'iy', 'jx', 'jy')
REAL_FIELDS = ('length', 'elevtn', 'riv_width', 'start_lat', 'start_lon')
REQUIRED_FIELDS = INTEGER_FIELDS + REAL_FIELDS
OVERLAND_PATTERN = re.compile(r'^ovl_width_(\d+)$')


@dataclass(frozen=True)
class BiforiTable:
    """Named source rows, preserving path IDs, input columns, and value text."""

    fields: tuple[str, ...]
    rows: tuple[dict[str, str], ...]
    overland_fields: tuple[str, ...]

    @property
    def width_count(self) -> int:
        """Return stored width count including the river channel."""
        return 1 + len(self.overland_fields)


def read_bifori_csv(path: str | Path) -> BiforiTable:
    """Read FLOW bifurcation paths, validating required numeric fields.

    Extra named columns are retained for regional pass-through. Widths are
    `riv_width` followed by consecutive `ovl_width_1..N`; numeric text is
    preserved in the returned row dictionaries and can be parsed as float32
    at the existing scientific calculation boundary.
    """
    source = Path(path)
    with source.open(newline='', encoding='utf-8-sig') as stream:
        reader = csv.DictReader(stream, skipinitialspace=True)
        fields = tuple(name.strip() for name in (reader.fieldnames or ()))
        if not fields or len(fields) != len(set(fields)):
            raise ValueError(f'{source}: missing or duplicate CSV column names')
        reader.fieldnames = list(fields)
        missing = [name for name in REQUIRED_FIELDS if name not in fields]
        if missing:
            raise ValueError(f'{source}: missing required columns: {", ".join(missing)}')

        layer_ids = []
        for name in fields:
            match = OVERLAND_PATTERN.fullmatch(name)
            if match:
                if str(int(match.group(1))) != match.group(1):
                    raise ValueError(f'{source}: invalid overland width column {name}')
                layer_ids.append(int(match.group(1)))
        layer_ids.sort()
        if layer_ids != list(range(1, len(layer_ids) + 1)):
            raise ValueError(f'{source}: overland columns must be consecutive from ovl_width_1')
        malformed = [name for name in fields
                      if name.startswith('ovl_width_') and not OVERLAND_PATTERN.fullmatch(name)]
        if malformed:
            raise ValueError(f'{source}: invalid overland width column {malformed[0]}')
        overland_fields = tuple(f'ovl_width_{index}' for index in layer_ids)

        rows = []
        path_ids = set()
        numeric_fields = REAL_FIELDS + overland_fields
        for row_number, raw_row in enumerate(reader, 1):
            if None in raw_row or any(value is None for value in raw_row.values()):
                raise ValueError(f'{source}: unexpected field count at CSV data row {row_number}')
            row = {name: (raw_row[name] or '').strip() for name in fields}
            required_values = REQUIRED_FIELDS + overland_fields
            if any(not row[name] for name in required_values):
                raise ValueError(f'{source}: missing required value at CSV data row {row_number}')
            try:
                integers = {name: int(row[name]) for name in INTEGER_FIELDS}
                reals = {name: np.float32(row[name]) for name in numeric_fields}
            except (TypeError, ValueError, OverflowError) as exc:
                raise ValueError(f'{source}: invalid scientific value at CSV data row {row_number}') from exc
            path_id = integers['path_id']
            if path_id < 1 or path_id in path_ids:
                raise ValueError(f'{source}: path_id must be positive and unique (row {row_number})')
            if not all(np.isfinite(value) for value in reals.values()):
                raise ValueError(f'{source}: non-finite scientific value at CSV data row {row_number}')
            path_ids.add(path_id)
            rows.append(row)

    return BiforiTable(fields, tuple(rows), overland_fields)


def write_bifori_csv(path: str | Path, fields: tuple[str, ...], rows: list[dict[str, str]]) -> None:
    """Write named rows with aligned commas while preserving value strings."""
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    encoded_rows = [[_encode_csv_cell(row.get(name, '')) for name in fields] for row in rows]
    encoded_fields = [_encode_csv_cell(name) for name in fields]
    widths = [max([len(header), *(len(row[index]) for row in encoded_rows)])
              for index, header in enumerate(encoded_fields)]
    with target.open('w', newline='', encoding='utf-8') as stream:
        stream.write(','.join(value.rjust(width) for value, width in zip(encoded_fields, widths)) + '\n')
        for row in encoded_rows:
            stream.write(','.join(value.rjust(width) for value, width in zip(row, widths)) + '\n')


def _encode_csv_cell(value: str) -> str:
    """Return one standard CSV-escaped cell for aligned text output."""
    stream = StringIO()
    csv.writer(stream, lineterminator='\n').writerow([str(value)])
    return stream.getvalue()[:-1]


def crop_bifori_records(rows, nextx, nx: int, ny: int, dx: int, dy: int):
    """Shift and retain paths using the established strict crop and edge rules."""
    selected = []
    for record in rows:
        ix, iy, jx, jy = (int(record[name]) for name in ('ix', 'iy', 'jx', 'jy'))
        ix, iy, jx, jy = ix-dx, iy-dy, jx-dx, jy-dy
        if not (0 < ix < nx and 0 < jx < nx and 0 < iy < ny and 0 < jy < ny):
            continue
        if nextx[iy-1, ix-1] == -9999 or nextx[jy-1, jx-1] == -9999:
            continue
        row = dict(record)
        row.update(ix=str(ix), iy=str(iy), jx=str(jx), jy=str(jy))
        selected.append(row)
    return selected

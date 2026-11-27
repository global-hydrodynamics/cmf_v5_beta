# SPDX-License-Identifier: Apache-2.0
"""Read and write the standard CSV inventory for high-resolution map tiles."""
from __future__ import annotations

import csv
from dataclasses import dataclass
import math
from pathlib import Path


LOCATION_FIELDS = ('iarea', 'carea', 'west', 'east', 'south', 'north', 'nx', 'ny', 'csize')
_NUMERIC_FIELDS = {'iarea', 'west', 'east', 'south', 'north', 'nx', 'ny', 'csize'}


@dataclass(frozen=True)
class LocationArea:
    """One tile's original inventory row and regular geographic grid geometry."""

    iarea: int
    carea: str
    west: float
    east: float
    south: float
    north: float
    nx: int
    ny: int
    csize: float

    def as_dict(self) -> dict[str, int | float | str]:
        return {field: getattr(self, field) for field in LOCATION_FIELDS}


def _validate_area(area: LocationArea, path: Path, row_number: int) -> None:
    numbers = (area.west, area.east, area.south, area.north, area.csize)
    if not area.carea or area.iarea < 1 or area.nx < 1 or area.ny < 1:
        raise ValueError(f'{path}:{row_number}: invalid tile id or dimensions')
    if not all(math.isfinite(value) for value in numbers) or area.csize <= 0:
        raise ValueError(f'{path}:{row_number}: invalid non-finite bounds or cell size')
    if area.east <= area.west or area.north <= area.south:
        raise ValueError(f'{path}:{row_number}: invalid geographic extent')
    if not math.isclose((area.east-area.west)/area.nx, area.csize, rel_tol=1e-6, abs_tol=1e-8):
        raise ValueError(f'{path}:{row_number}: nx conflicts with extent and csize')
    if not math.isclose((area.north-area.south)/area.ny, area.csize, rel_tol=1e-6, abs_tol=1e-8):
        raise ValueError(f'{path}:{row_number}: ny conflicts with extent and csize')


def read_location_csv(path: Path) -> list[LocationArea]:
    """Read CSV tile metadata, stripping alignment whitespace from every field."""
    path = Path(path)
    try:
        with path.open(newline='', encoding='utf-8-sig') as stream:
            reader = csv.DictReader(stream)
            header = [name.strip().lower() for name in (reader.fieldnames or [])]
            if tuple(header) != LOCATION_FIELDS:
                raise ValueError(f'{path}: header must be {",".join(LOCATION_FIELDS)}')
            areas = []
            for row_number, raw in enumerate(reader, 2):
                if raw is None or all(value is None or not value.strip() for value in raw.values()):
                    continue
                row = {key.strip().lower(): (value or '').strip() for key, value in raw.items() if key is not None}
                if None in raw or set(row) != set(LOCATION_FIELDS):
                    raise ValueError(f'{path}:{row_number}: expected exactly {len(LOCATION_FIELDS)} fields')
                try:
                    area = LocationArea(
                        int(row['iarea']), row['carea'],
                        float(row['west']), float(row['east']), float(row['south']), float(row['north']),
                        int(row['nx']), int(row['ny']), float(row['csize']),
                    )
                except ValueError as exc:
                    raise ValueError(f'{path}:{row_number}: invalid location field') from exc
                _validate_area(area, path, row_number)
                areas.append(area)
    except OSError as exc:
        raise ValueError(f'cannot read location CSV {path}: {exc}') from exc
    if not areas:
        raise ValueError(f'{path}: tile inventory is empty')
    if len({area.iarea for area in areas}) != len(areas):
        raise ValueError(f'{path}: duplicate iarea values')
    if len({area.carea for area in areas}) != len(areas):
        raise ValueError(f'{path}: duplicate carea values')
    return areas


def _format_area(area: LocationArea) -> list[str]:
    _validate_area(area, Path('location.csv'), 0)
    return [str(area.iarea), area.carea, repr(area.west), repr(area.east), repr(area.south),
            repr(area.north), str(area.nx), str(area.ny), repr(area.csize)]


def write_location_csv(path: Path, areas: list[LocationArea]) -> None:
    """Write aligned, deterministic CSV while retaining ordinary CSV syntax."""
    path = Path(path)
    if not areas:
        raise ValueError('cannot write an empty high-resolution tile inventory')
    rows = [_format_area(area) for area in areas]
    if len({row[0] for row in rows}) != len(rows) or len({row[1] for row in rows}) != len(rows):
        raise ValueError('duplicate iarea or carea values in high-resolution tile inventory')
    widths = [max(len(LOCATION_FIELDS[i]), *(len(row[i]) for row in rows)) for i in range(len(LOCATION_FIELDS))]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w', newline='', encoding='utf-8') as stream:
        writer = csv.writer(stream, lineterminator='\n')
        writer.writerow([name.rjust(widths[i]) if name in _NUMERIC_FIELDS else name.ljust(widths[i])
                         for i, name in enumerate(LOCATION_FIELDS)])
        for row in rows:
            writer.writerow([value.rjust(widths[i]) if LOCATION_FIELDS[i] in _NUMERIC_FIELDS
                             else value.ljust(widths[i]) for i, value in enumerate(row)])


def read_location_txt(path: Path) -> list[LocationArea]:
    """Read the retired counted text format at explicit legacy boundaries only."""
    path = Path(path)
    try:
        lines = [line.strip() for line in path.read_text(encoding='utf-8').splitlines() if line.strip()]
    except OSError as exc:
        raise ValueError(f'cannot read legacy location metadata {path}: {exc}') from exc
    if len(lines) < 2:
        raise ValueError(f'{path}: legacy location file requires a count and header')
    try:
        count = int(lines[0].split()[0])
    except (ValueError, IndexError) as exc:
        raise ValueError(f'{path}: invalid legacy area count') from exc
    if [value.lower() for value in lines[1].split()] != list(LOCATION_FIELDS):
        raise ValueError(f'{path}: invalid legacy location header')
    if count < 1 or len(lines) != count + 2:
        raise ValueError(f'{path}: declared {count} areas but found {len(lines)-2} records')
    areas = []
    for row_number, line in enumerate(lines[2:], 3):
        fields = line.split()
        if len(fields) != len(LOCATION_FIELDS):
            raise ValueError(f'{path}:{row_number}: expected {len(LOCATION_FIELDS)} values')
        try:
            area = LocationArea(int(fields[0]), fields[1], *(float(value) for value in fields[2:6]),
                                int(fields[6]), int(fields[7]), float(fields[8]))
        except ValueError as exc:
            raise ValueError(f'{path}:{row_number}: invalid legacy location field') from exc
        _validate_area(area, path, row_number)
        areas.append(area)
    if len({area.iarea for area in areas}) != len(areas) or len({area.carea for area in areas}) != len(areas):
        raise ValueError(f'{path}: duplicate area index or name')
    return areas


def write_location_txt(path: Path, areas: list[LocationArea]) -> None:
    """Write the retired counted text format for explicit Binary compatibility."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w', encoding='utf-8', newline='') as stream:
        stream.write(f'{len(areas):6d}  narea\n')
        stream.write('iarea carea west east south north nx ny csize\n')
        for area in areas:
            _validate_area(area, path, area.iarea + 2)
            fields = (area.iarea, area.carea, repr(area.west), repr(area.east), repr(area.south),
                      repr(area.north), area.nx, area.ny, repr(area.csize))
            stream.write(' '.join(str(value) for value in fields) + '\n')

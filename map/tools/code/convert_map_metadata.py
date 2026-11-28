# SPDX-License-Identifier: Apache-2.0
"""Convert legacy map TXT metadata and standard v5 NML/CSV metadata."""
from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
import math
import os
from pathlib import Path
import re
import stat
import tempfile

from hires_metadata import read_location_csv, read_location_txt, write_location_csv, write_location_txt
from map_metadata import (read_diminfo_nml, read_legacy_values, read_nml_values,
                          render_legacy, render_nml)
from mod_bifori_csv import read_bifori_csv, write_bifori_csv
from mod_bifprm_csv import read_bifprm_csv


ALLOCATION_SCHEMAS = {
    'GRDC_alloc': ('ID', 'lat', 'lon', 'area_Input', 'area_CaMa', 'error', 'diff', 'Type',
                   'ix1', 'iy1', 'ix2', 'iy2', 'area1', 'area2'),
    'GRanD_river': ('ID', 'lat', 'lon', 'area_CaMa', 'area_Input', 'error', 'diff', 'ix', 'iy',
                    'cap_mcm', 'year', 'damname', 'rivname'),
    'GRanD_small': ('ID', 'lat', 'lon', 'area_CaMa', 'area_Input', 'error', 'diff', 'ix', 'iy',
                    'cap_mcm', 'year', 'damname', 'rivname'),
    'GRanD_error': ('ID', 'lat', 'lon', 'area_CaMa', 'area_Input', 'error', 'diff', 'ix', 'iy',
                    'cap_mcm', 'year', 'damname', 'rivname'),
    'MLIT_levelgauge': ('ID', 'lat', 'lon', 'area', 'Type', 'ix1', 'iy1', 'ix2', 'iy2',
                        'elv_outlet', 'elv_gauge', 'elv_upst', 'dst_outlet', 'dst_upst', 'upa_outlet'),
}
ALLOCATION_LAYOUTS = {
    'GRDC_alloc': (('i', 10), ('f', 10, 3), ('f', 10, 3), *[('f', 12, 2)] * 4,
                   ('i', 8), ('i', 8), ('i', 6), ('i', 8), ('i', 6), ('f', 12, 1), ('f', 12, 1)),
    'GRanD_river': (('i', 10), ('f', 10, 3), ('f', 10, 3), *[('f', 12, 1)] * 4,
                    ('i', 8), ('i', 8), ('f', 12, 1), ('i', 6), ('x', 2), ('s', 30), ('x', 2), ('s', 30)),
    'GRanD_small': (('i', 10), ('f', 10, 3), ('f', 10, 3), *[('f', 12, 1)] * 4,
                    ('i', 8), ('i', 8), ('f', 12, 1), ('i', 6), ('x', 2), ('s', 30), ('x', 2), ('s', 30)),
    'GRanD_error': (('i', 10), ('f', 10, 3), ('f', 10, 3), *[('f', 12, 1)] * 4,
                    ('i', 8), ('i', 8), ('f', 12, 1), ('i', 6), ('x', 2), ('s', 30), ('x', 2), ('s', 30)),
    'MLIT_levelgauge': (('i', 10), ('f', 10, 3), ('f', 10, 3), ('f', 12, 1), ('i', 8),
                        ('i', 8), ('i', 6), ('i', 8), ('i', 6), *[('f', 12, 2)] * 5, ('f', 15, 2)),
}
ALLOCATION_HEADERS = {
    'GRDC_alloc': '        ID       lat       lon  area_Input   area_CaMa       error        diff    Type     ix1   iy1     ix2   iy2       area1       area2',
    'GRanD_river': ('        ID       lat       lon   area_CaMa  area_Input       error        diff'
                    '      ix      iy     cap_mcm  year  damname                         rivname'),
    'GRanD_small': ('        ID       lat       lon   area_CaMa  area_Input       error        diff'
                    '      ix      iy     cap_mcm  year  damname                         rivname'),
    'GRanD_error': ('        ID       lat       lon   area_CaMa  area_Input       error        diff'
                    '      ix      iy     cap_mcm  year  damname                         rivname'),
    'MLIT_levelgauge': ('        ID       lat       lon        area    Type     ix1   iy1     ix2   iy2'
                        '  elv_outlet   elv_gauge    elv_upst  dst_outlet    dst_upst     upa_outlet'),
}


@dataclass
class Conversion:
    source: Path
    destination: Path
    count: int
    omitted_columns: tuple[str, ...] = ()


def _atomic_write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile('w', encoding='utf-8', newline='', dir=path.parent,
                                         prefix=f'.{path.name}.', delete=False) as stream:
            temporary = Path(stream.name)
            stream.write(content)
        _set_output_mode(temporary, path)
        temporary.replace(path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def _set_output_mode(temporary: Path, destination: Path) -> None:
    mode = stat.S_IMODE(destination.stat().st_mode) if destination.exists() else 0o644
    os.chmod(temporary, mode)


def _atomic_table(path: Path, writer) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile('w', encoding='utf-8', newline='', dir=path.parent,
                                     prefix=f'.{path.name}.', delete=False) as stream:
        temporary = Path(stream.name)
    try:
        writer(temporary)
        _set_output_mode(temporary, path)
        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)


def _read_bifori_txt(path: Path):
    lines = [line.split() for line in path.read_text(encoding='utf-8').splitlines() if line.strip()]
    if not lines or len(lines[0]) < 2:
        raise ValueError(f'{path}: expected npath and nlev header')
    npath, nlev = map(int, lines[0][:2])
    if npath < 1 or nlev < 1 or len(lines) != npath + 1:
        raise ValueError(f'{path}: invalid path/layer counts')
    fields = ('path_id', 'ix', 'iy', 'jx', 'jy', 'length', 'elevtn', 'riv_width',
              *(f'ovl_width_{i}' for i in range(1, nlev)), 'start_lat', 'start_lon')
    rows = []
    for index, values in enumerate(lines[1:], 1):
        if len(values) != len(fields) - 1:
            raise ValueError(f'{path}: row {index} has {len(values)} values, expected {len(fields)-1}')
        try:
            tuple(int(value) for value in values[:4])
            numeric = tuple(float(value) for value in values[4:])
        except ValueError as exc:
            raise ValueError(f'{path}: invalid numeric value in row {index}') from exc
        if not all(math.isfinite(value) for value in numeric):
            raise ValueError(f'{path}: non-finite value in row {index}')
        rows.append(dict(zip(fields, (str(index), *values))))
    return fields, rows


def _bifori_txt_content(path: Path) -> tuple[str, int]:
    table = read_bifori_csv(path)
    allowed = set(table.fields)
    if any(name not in {'path_id', 'ix', 'iy', 'jx', 'jy', 'length', 'elevtn', 'riv_width',
                        'start_lat', 'start_lon', *table.overland_fields} for name in allowed):
        if any(row.get(name, '').strip() for row in table.rows for name in allowed - {
            'path_id', 'ix', 'iy', 'jx', 'jy', 'length', 'elevtn', 'riv_width', 'start_lat',
            'start_lon', *table.overland_fields}):
            raise ValueError(f'{path}: populated extra columns cannot be represented in legacy bifori.txt')
    for index, row in enumerate(table.rows, 1):
        if int(row['path_id']) != index:
            raise ValueError(f'{path}: legacy bifori.txt requires row-ordered path_id values')
    content = [f'{len(table.rows):6d} {table.width_count:4d}\n']
    for row in table.rows:
        values = [row[name] for name in ('ix', 'iy', 'jx', 'jy', 'length', 'elevtn', 'riv_width')]
        values.extend(row[name] for name in table.overland_fields)
        values.extend(row[name] for name in ('start_lat', 'start_lon'))
        content.append(' '.join(values) + '\n')
    return ''.join(content), len(table.rows)


def _bifprm_txt_content(path: Path) -> tuple[str, int, tuple[str, ...]]:
    rows = read_bifprm_csv(path)
    with path.open(newline='', encoding='utf-8-sig') as stream:
        reader = csv.DictReader(stream)
        fields = [name.strip() for name in (reader.fieldnames or [])]
        raw_rows = [
            {key.strip(): value for key, value in row.items() if key is not None}
            for row in reader
        ]
    widths = ['riv_width'] + sorted((name for name in fields if re.fullmatch(r'ovl_width_[1-9]\d*', name)),
                                    key=lambda name: int(name.rsplit('_', 1)[1]))
    extras = set(fields) - set(('pth_id', 'ix', 'iy', 'jx', 'jy', 'length', 'elevtn', 'depth',
                                'start_lat', 'start_lon', 'end_lat', 'end_lon', 'ibsn', 'jbsn', *widths))
    if extras and any((row.get(name) or '').strip() for row in raw_rows for name in extras):
        raise ValueError(f'{path}: populated extra columns cannot be represented in legacy bifprm.txt')
    for index, (parsed, row) in enumerate(zip(rows, raw_rows), 1):
        if parsed['pth_id'] != index:
            raise ValueError(f'{path}: legacy bifprm.txt requires row-ordered pth_id values')
    nlev = len(widths)
    if nlev < 1:
        raise ValueError(f'{path}: at least riv_width is required')
    content = [f'{len(rows):8d} {nlev:4d}\n']
    for row in raw_rows:
        names = ('ix', 'iy', 'jx', 'jy', 'length', 'elevtn', 'depth', *widths,
                 'start_lat', 'start_lon', 'ibsn', 'jbsn')
        content.append(' '.join((row.get(name) or '').strip() for name in names) + '\n')
    omitted_columns = tuple(name for name in ('end_lat', 'end_lon') if name in fields)
    return ''.join(content), len(rows), omitted_columns


def _bifprm_csv_from_txt(source: Path, destination: Path) -> int:
    lines = [line.split() for line in source.read_text(encoding='utf-8').splitlines() if line.strip()]
    if not lines or len(lines[0]) < 2:
        raise ValueError('expected npath and nlev header')
    count, nlev = map(int, lines[0][:2])
    if count < 1 or nlev < 1 or len(lines) != count + 1:
        raise ValueError('invalid path/layer counts')
    fields = ['pth_id', 'ix', 'iy', 'jx', 'jy', 'length', 'elevtn', 'depth', 'riv_width']
    fields.extend(f'ovl_width_{i}' for i in range(1, nlev))
    fields.extend(('start_lat', 'start_lon', 'ibsn', 'jbsn'))
    output_fields = [*fields[:8], 'riv_width', *(f'ovl_width_{i}' for i in range(1, nlev)),
                     'start_lat', 'start_lon', 'end_lat', 'end_lon', 'ibsn', 'jbsn']
    rows = []
    expected = len(fields) - 1
    for index, values in enumerate(lines[1:], 1):
        if len(values) != expected:
            raise ValueError(f'row {index} has {len(values)} fields, expected {expected}')
        try:
            tuple(int(value) for value in (*values[:4], *values[-2:]))
            numeric = tuple(float(value) for value in values[4:-2])
        except ValueError as exc:
            raise ValueError(f'invalid numeric value in row {index}') from exc
        if not all(math.isfinite(value) for value in numeric):
            raise ValueError(f'non-finite value in row {index}')
        row = dict(zip(fields[1:], values))
        row.update(pth_id=str(index), end_lat='-9999', end_lon='-9999')
        rows.append(row)

    def write_csv(temp):
        with temp.open('w', newline='', encoding='utf-8') as stream:
            writer = csv.DictWriter(stream, fieldnames=output_fields, lineterminator='\n')
            writer.writeheader()
            writer.writerows(rows)
    _atomic_table(destination, write_csv)
    return len(rows)


def _field_slices(layout):
    offset = 0
    slices = []
    for item in layout:
        width = item[1]
        slices.append(slice(offset, offset + width))
        offset += width
    return slices, offset


def _legacy_diminfo(value) -> str:
    # The v4 positional descriptor stores dimensions, matrix filename, and
    # model-grid bounds. New input-grid provenance has no v4 field.
    legacy_values = (value.nx, value.ny, value.nlfp, value.nxin, value.nyin,
                     value.inpn, value.inpmat_file, value.west, value.east,
                     value.north, value.south)
    labels = ('nXX', 'nYY', 'floodplain layer', 'input nXX', 'input nYY', 'input num',
              'inpmat file', 'west edge', 'east edge', 'north edge', 'south edge')
    rows = []
    for item, label in zip(legacy_values, labels):
        token = str(item) if isinstance(item, int) else str(item)
        rows.append(f'{token:>24}     !! {label}\n')
    return ''.join(rows)


def _parse_allocation_txt(path: Path, kind: str):
    layout = ALLOCATION_LAYOUTS[kind]
    slices, width = _field_slices(layout)
    lines = path.read_text(encoding='utf-8').splitlines()
    if not lines:
        raise ValueError(f'{path}: missing legacy header')
    rows = []
    for line_number, line in enumerate(lines[1:], 2):
        if not line.strip():
            continue
        values = []
        field_iter = iter(ALLOCATION_SCHEMAS[kind])
        for field_slice, descriptor in zip(slices, layout):
            if descriptor[0] == 'x':
                continue
            field = next(field_iter)
            value = line[field_slice].strip()
            if descriptor[0] == 's':
                values.append(value)
            else:
                if not value:
                    raise ValueError(f'{path}:{line_number}: missing fixed-width value')
                try:
                    if descriptor[0] == 'i':
                        values.append(str(int(value)))
                    else:
                        number = float(value)
                        if not math.isfinite(number):
                            raise ValueError(f'{path}:{line_number}: non-finite value {value!r}')
                        values.append(str(number))
                except ValueError as exc:
                    raise ValueError(f'{path}:{line_number}: invalid fixed-width value {value!r}') from exc
        if line[width:].strip():
            raise ValueError(f'{path}:{line_number}: unexpected values beyond the documented record width')
        rows.append(dict(zip(ALLOCATION_SCHEMAS[kind], values)))
    return rows


def _fmt_allocation(value: str, descriptor, path: Path) -> str:
    kind = descriptor[0]
    width = descriptor[1]
    if kind == 's':
        if len(value) > width:
            raise ValueError(f'{path}: string value exceeds legacy {width}-character field')
        return value.ljust(width)
    try:
        if kind == 'i':
            result = f'{int(value):{width}d}'
        else:
            number = float(value)
            if not math.isfinite(number):
                raise ValueError(f'{path}: non-finite value {value!r}')
            result = f'{number:{width}.{descriptor[2]}f}'
    except ValueError as exc:
        raise ValueError(f'{path}: invalid value {value!r}') from exc
    if len(result) > width:
        raise ValueError(f'{path}: value {value!r} overflows legacy {width}-character field')
    return result


def _allocation_csv_to_txt(path: Path, kind: str) -> tuple[str, int]:
    with path.open(newline='', encoding='utf-8-sig') as stream:
        reader = csv.DictReader(stream)
        fields = [name.strip() for name in (reader.fieldnames or [])]
        rows = [{key.strip(): (value or '').strip() for key, value in row.items() if key is not None}
                for row in reader]
    expected = ALLOCATION_SCHEMAS[kind]
    if not set(expected).issubset(fields):
        raise ValueError(f'{path}: missing required columns {sorted(set(expected)-set(fields))}')
    extras = set(fields) - set(expected)
    if extras and any(row.get(name, '') for row in rows for name in extras):
        raise ValueError(f'{path}: populated extra columns cannot be represented in legacy TXT')
    output = [ALLOCATION_HEADERS[kind] + '\n']
    for number, row in enumerate(rows, 1):
        if any(not row.get(name, '') for name in expected):
            raise ValueError(f'{path}: missing required value in row {number}')
        cells = []
        values = iter(expected)
        for layout in ALLOCATION_LAYOUTS[kind]:
            if layout[0] == 'x':
                cells.append(' ' * layout[1])
            else:
                name = next(values)
                cells.append(_fmt_allocation(row[name], layout, path))
        output.append(''.join(cells) + '\n')
    return ''.join(output), len(rows)


def _convert_families(map_dir: Path, direction: str) -> list[Conversion]:
    conversions = []
    failures = []

    def run(source: Path, destination: Path, convert):
        if not source.is_file():
            return
        try:
            result = convert(source, destination)
            if isinstance(result, tuple):
                count, omitted_columns = result
            else:
                count, omitted_columns = result, ()
            conversions.append(Conversion(source, destination, count, omitted_columns))
        except (OSError, ValueError, csv.Error) as exc:
            failures.append(f'{source}: {exc}')
            print(f'ERROR: {source}: {exc}')

    def text_pair(src, dst, reader, renderer, count=1):
        def convert(source, destination):
            value = reader(source)
            content = renderer(value)
            _atomic_write(destination, content)
            return count
        run(src, dst, convert)

    txt_to_meta = direction == 'txt2meta'
    text_pair(map_dir / ('params.txt' if txt_to_meta else 'params.nml'),
              map_dir / ('params.nml' if txt_to_meta else 'params.txt'),
              (lambda p: read_legacy_values(p)[1]) if txt_to_meta else read_nml_values,
              render_nml if txt_to_meta else render_legacy, 8)

    if not txt_to_meta:
        for source in sorted(map_dir.glob('diminfo_*.nml')):
            suffix = source.name.removeprefix('diminfo_').removesuffix('.nml')
            destination = map_dir / f'diminfo_{suffix}.txt'
            text_pair(source, destination, read_diminfo_nml, _legacy_diminfo, 11)

    for folder in sorted(path for path in map_dir.iterdir()
                         if path.is_dir() and not path.is_symlink()
                         and path.name.lower() not in {'binary', 'cog'}):
        name = 'location.txt' if txt_to_meta else 'location.csv'
        source = folder / name
        destination = folder / ('location.csv' if txt_to_meta else 'location.txt')
        def location_convert(src, dst):
            areas = read_location_txt(src) if txt_to_meta else read_location_csv(src)
            if txt_to_meta:
                _atomic_table(dst, lambda temp: write_location_csv(temp, areas))
            else:
                _atomic_table(dst, lambda temp: write_location_txt(temp, areas))
            return len(areas)
        run(source, destination, location_convert)

    if txt_to_meta:
        def bifori_convert(src, dst):
            fields, rows = _read_bifori_txt(src)
            _atomic_table(dst, lambda temp: write_bifori_csv(temp, fields, rows))
            return len(rows)
        run(map_dir / 'bifori.txt', map_dir / 'bifori.csv', bifori_convert)
        run(map_dir / 'bifprm.txt', map_dir / 'bifprm.csv', _bifprm_csv_from_txt)
    else:
        def bifori_reverse(src, dst):
            content, count = _bifori_txt_content(src)
            _atomic_write(dst, content)
            return count
        run(map_dir / 'bifori.csv', map_dir / 'bifori.txt', bifori_reverse)

        def bifprm_reverse(src, dst):
            content, count, omitted_columns = _bifprm_txt_content(src)
            _atomic_write(dst, content)
            return count, omitted_columns
        run(map_dir / 'bifprm.csv', map_dir / 'bifprm.txt', bifprm_reverse)

    for kind in ALLOCATION_SCHEMAS:
        source = map_dir / f'{kind}.txt' if txt_to_meta else map_dir / f'{kind}.csv'
        destination = map_dir / f'{kind}.csv' if txt_to_meta else map_dir / f'{kind}.txt'
        if txt_to_meta:
            def allocation_convert(src, dst, schema=kind):
                rows = _parse_allocation_txt(src, schema)
                def write_csv(temporary):
                    with temporary.open('w', newline='', encoding='utf-8') as stream:
                        writer = csv.DictWriter(stream, fieldnames=ALLOCATION_SCHEMAS[schema], lineterminator='\n')
                        writer.writeheader()
                        writer.writerows(rows)
                _atomic_table(dst, write_csv)
                return len(rows)
        else:
            def allocation_convert(src, dst, schema=kind):
                content, count = _allocation_csv_to_txt(src, schema)
                _atomic_write(dst, content)
                return count
        run(source, destination, allocation_convert)

    if failures:
        raise RuntimeError('\n'.join(failures))
    return conversions


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('direction', choices=('txt2meta', 'meta2txt'))
    parser.add_argument('map_dir', type=Path)
    args = parser.parse_args()
    map_dir = args.map_dir.resolve()
    if not map_dir.is_dir():
        parser.error(f'map directory does not exist: {map_dir}')
    try:
        conversions = _convert_families(map_dir, args.direction)
    except RuntimeError:
        return 1
    if not conversions:
        print('No matching metadata source files found; nothing converted.')
        return 0
    print(f'Converted {len(conversions)} metadata file(s):')
    for item in conversions:
        print(f'  {item.source.name} -> {item.destination.name}: {item.count} record(s)/field(s)')
        if item.omitted_columns:
            print(f'    omitted v5-only columns: {", ".join(item.omitted_columns)}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

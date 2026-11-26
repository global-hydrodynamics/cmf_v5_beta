#!/usr/bin/env python3
"""Restore little-endian high-resolution Binary tiles from distribution NetCDF.

The registry owns signed storage types and complete-plane record order.
Read raw stored values without masks/scaling so sentinels and floating-point
bit patterns are not silently reinterpreted during legacy-format restoration.
"""
from __future__ import annotations

import argparse
import array
from concurrent.futures import ProcessPoolExecutor, as_completed
import ctypes
import math
import os
from pathlib import Path
import re
import sys
import tempfile

try:
    from . import convert_highres_binary_to_netcdf as forward
except ImportError:
    import convert_highres_binary_to_netcdf as forward

ConversionError = forward.ConversionError
CHUNK_EDGE = forward.NETCDF_CHUNK_EDGE


def read_api():
    """Extend the existing NetCDF C interface; no automatic masking/scaling occurs."""
    lib = forward.netcdf_library()
    forward.configure_api(lib)
    ci, sz, cp = ctypes.c_int, ctypes.c_size_t, ctypes.c_char_p
    lib.nc_open.argtypes = [cp, ci, ctypes.POINTER(ci)]
    lib.nc_inq_varndims.argtypes = [ci, ci, ctypes.POINTER(ci)]
    lib.nc_inq_var.argtypes = [ci, ci, cp, ctypes.POINTER(ci), ctypes.POINTER(ci), ctypes.POINTER(ci), ctypes.POINTER(ci)]
    lib.nc_inq_dimlen.argtypes = [ci, ci, ctypes.POINTER(sz)]
    lib.nc_inq_dimname.argtypes = [ci, ci, cp]
    lib.nc_inq_nvars.argtypes = [ci, ctypes.POINTER(ci)]
    lib.nc_inq_attname.argtypes = [ci, ci, ci, cp]
    lib.nc_get_vara.argtypes = [ci, ci, ctypes.POINTER(sz), ctypes.POINTER(sz), ctypes.c_void_p]
    lib.nc_get_vara_double.argtypes = [ci, ci, ctypes.POINTER(sz), ctypes.POINTER(sz), ctypes.POINTER(ctypes.c_double)]
    return lib


def variable_info(lib, ncid, name):
    varid, ndims = ctypes.c_int(), ctypes.c_int()
    forward.check(lib, lib.nc_inq_varid(ncid, name.encode(), ctypes.byref(varid)), f'find variable {name}')
    forward.check(lib, lib.nc_inq_varndims(ncid, varid.value, ctypes.byref(ndims)), f'inspect dimensions of {name}')
    if ndims.value not in (1, 2):
        raise ConversionError(f'{name}: expected one-dimensional coordinate or two-dimensional raster')
    dims = (ctypes.c_int * ndims.value)()
    dtype, natts = ctypes.c_int(), ctypes.c_int()
    forward.check(lib, lib.nc_inq_var(ncid, varid.value, None, ctypes.byref(dtype), ctypes.byref(ndims), dims, ctypes.byref(natts)), f'inspect {name}')
    for index in range(natts.value):
        att = ctypes.create_string_buffer(257)
        forward.check(lib, lib.nc_inq_attname(ncid, varid.value, index, att), f'inspect {name} attributes')
        attribute = att.value.decode()
        if attribute in ('scale_factor', 'add_offset', '_Unsigned') or attribute.startswith('_Quantize'):
            raise ConversionError(f'{name}: unsupported packing/signedness/quantization attribute {attribute}')
    lengths = []
    for dim in dims:
        length = ctypes.c_size_t()
        forward.check(lib, lib.nc_inq_dimlen(ncid, dim, ctypes.byref(length)), f'inspect {name} dimension length')
        lengths.append(length.value)
    return varid.value, dtype.value, tuple(dims), tuple(lengths)


def validate_netcdf(lib, ncid, area, rows):
    """Check the forward writer's named dimensions, types and cell-center geometry."""
    axes = {}
    for name, size, origin, step in [
        ('lon', int(area['nx']), float(area['west']), float(area['resolution'])),
        ('lat', int(area['ny']), float(area['north']), -float(area['resolution'])),
    ]:
        varid, dtype, dims, lengths = variable_info(lib, ncid, name)
        if dtype not in (forward.NC_DOUBLE, forward.NC_FLOAT) or lengths != (size,):
            raise ConversionError(f'{name}: wrong coordinate type or length; location.txt requires {size}')
        # The forward writer uses float64 axes; accept float32 centers within their storage precision.
        tolerance = 2e-5 if dtype == forward.NC_FLOAT else max(abs(step) * 1e-8, 1e-9)
        for first in range(0, size, CHUNK_EDGE):
            count = min(CHUNK_EDGE, size - first)
            data = (ctypes.c_double * count)()
            start, shape = (ctypes.c_size_t * 1)(first), (ctypes.c_size_t * 1)(count)
            forward.check(lib, lib.nc_get_vara_double(ncid, varid, start, shape, data), f'read {name} coordinates')
            for index, actual in enumerate(data):
                expected = origin + (first + index + .5) * step
                if not math.isclose(actual, expected, rel_tol=0, abs_tol=tolerance):
                    raise ConversionError(f'{name}[{first+index}]={actual} conflicts with location.txt center {expected}')
        dim_name = ctypes.create_string_buffer(257)
        forward.check(lib, lib.nc_inq_dimname(ncid, dims[0], dim_name), f'inspect {name} dimension name')
        if dim_name.value.decode() != name:
            raise ConversionError(f'{name}: coordinate must use the dimension of the same name')
        axes[name] = dims[0]
    if axes['lat'] == axes['lon']:
        raise ConversionError('latitude and longitude must use distinct dimensions')
    result = []
    expected_names = {'lat', 'lon'}
    for row in rows:
        name = row.get('name', '').strip()
        if name in expected_names:
            raise ConversionError(f'duplicate/coordinate registry variable: {name}')
        expected_names.add(name)
        varid, dtype, dims, lengths = variable_info(lib, ncid, name)
        expected_type = forward.TYPE_INFO[row['dtype'].strip().lower()][3]
        if dtype != expected_type or dims != (axes['lat'], axes['lon']) or lengths != (int(area['ny']), int(area['nx'])):
            raise ConversionError(f'{name}: NetCDF type, dimensions or order differs from registry/location.txt')
        result.append(varid)
    nvars = ctypes.c_int()
    forward.check(lib, lib.nc_inq_nvars(ncid, ctypes.byref(nvars)), 'inspect variable count')
    if nvars.value != len(expected_names):
        raise ConversionError('unexpected NetCDF variables; expected only registry variables and lat/lon')
    return result


def tile_rows(rows, hires, area, variable):
    """Use existing registry patterns and the same record contract as the forward writer."""
    selected = sorted(forward.rows_for_tile(rows, hires, str(area['carea']), variable),
                      key=lambda row: int(row.get('record_index') or '1'))
    dtypes = {row.get('dtype', '').strip().lower() for row in selected}
    counts = {int(row.get('record_count') or '1') for row in selected}
    if len(dtypes) != 1 or not dtypes <= forward.TYPE_INFO.keys() or len(counts) != 1:
        raise ConversionError(f'{variable}: inconsistent/unsupported registered type or record count')
    count = next(iter(counts))
    if count < 1 or [int(row.get('record_index') or '1') for row in selected] != list(range(1, count + 1)):
        raise ConversionError(f'{variable}: record indices must cover 1..{count}')
    if any(row.get('dimensions', '').strip() != 'NX_HIRES,NY_HIRES' for row in selected):
        raise ConversionError(f'{variable}: unsupported registered dimensions')
    return selected


def restore_tile(task):
    source, output, area, rows, force = task
    lib, ncid = read_api(), ctypes.c_int()
    forward.check(lib, lib.nc_open(os.fsencode(source), 0, ctypes.byref(ncid)), f'open {source}')
    temporary = None
    try:
        varids = validate_netcdf(lib, ncid.value, area, rows)
        dtype = rows[0]['dtype'].strip().lower()
        itemsize, code, ctype, _, _ = forward.TYPE_INFO[dtype]
        nx, ny = int(area['nx']), int(area['ny'])
        record_bytes = nx * ny * itemsize
        expected_size = record_bytes * len(rows)
        fd, name = tempfile.mkstemp(prefix=f'.{output.name}.', suffix='.tmp', dir=output.parent)
        temporary = Path(name)
        with os.fdopen(fd, 'w+b') as stream:
            for record, varid in enumerate(varids):
                for y0 in range(0, ny, CHUNK_EDGE):
                    height = min(CHUNK_EDGE, ny - y0)
                    for x0 in range(0, nx, CHUNK_EDGE):
                        width = min(CHUNK_EDGE, nx - x0)
                        data = array.array(code, [0]) * (height * width)
                        if data.itemsize != itemsize:
                            raise RuntimeError(f'platform buffer size differs from {dtype}')
                        start = (ctypes.c_size_t * 2)(y0, x0)
                        shape = (ctypes.c_size_t * 2)(height, width)
                        # Generic typed-storage read avoids masks, arithmetic and value substitution.
                        forward.check(lib, lib.nc_get_vara(ncid.value, varid, start, shape,
                                      forward.array_pointer(data, ctype)), f'read {source.name} record {record+1}')
                        if itemsize > 1 and sys.byteorder != 'little':
                            data.byteswap()
                        raw = data.tobytes()
                        for row_index in range(height):
                            offset = record * record_bytes + ((y0 + row_index) * nx + x0) * itemsize
                            stream.seek(offset)
                            stream.write(raw[row_index*width*itemsize:(row_index+1)*width*itemsize])
            stream.flush()
            if os.fstat(stream.fileno()).st_size != expected_size:
                raise ConversionError(f'{source.name}: restored size differs from expected {expected_size}')
        forward.check(lib, lib.nc_close(ncid.value), f'close {source.name}')
        ncid.value = -1
        if force:
            os.replace(temporary, output)
        else:
            # Hard-link publication refuses a file created concurrently after the skip check.
            os.link(temporary, output)
            temporary.unlink()
        temporary = None
        return expected_size
    finally:
        if ncid.value >= 0:
            lib.nc_close(ncid.value)
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def same_geometry(left, right):
    if len(left) != len(right):
        return False
    for a, b in zip(left, right):
        for key in a:
            if isinstance(a[key], float):
                if not math.isclose(a[key], b[key], rel_tol=1e-10, abs_tol=1e-10):
                    return False
            elif a[key] != b[key]:
                return False
    return True


def restore_location(source, target, areas):
    if target.exists():
        if not same_geometry(areas, forward.read_location(target)):
            raise ConversionError(f'{target}: conflicting geometry; review it explicitly before restoring')
        return  # Preserve an existing geometrically equivalent metadata file verbatim.
    fd, name = tempfile.mkstemp(prefix='.location.', suffix='.tmp', dir=target.parent)
    temporary = Path(name)
    try:
        with os.fdopen(fd, 'wb') as stream:
            stream.write(source.read_bytes())
        os.link(temporary, target)
    finally:
        temporary.unlink(missing_ok=True)


def restore(map_dir, hires, variables, registry, jobs=1, force=True, areas_filter=None):
    if jobs < 1 or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]*', hires) or hires in ('.', '..'):
        raise ConversionError('jobs must be positive and hires must be a single directory tag')
    source_dir = map_dir / hires
    if not (source_dir / 'location.txt').is_file():
        source_dir = map_dir / f'{hires}_nc'  # legacy layout
    output_dir = map_dir / 'binary' / hires
    areas = forward.read_location(source_dir / 'location.txt')
    if not areas or not variables:
        raise ConversionError('location.txt and variable selection must be nonempty')
    # Keep names as single path components; location metadata must never redirect writes.
    for name in [hires, *variables, *(str(area['carea']) for area in areas)]:
        if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]*', name) or name in ('.', '..'):
            raise ConversionError(f'unsafe path component: {name!r}')
    if source_dir.resolve() == output_dir.resolve() or output_dir.is_symlink():
        raise ConversionError('source and output must be distinct directories; output symlinks are not supported')
    if (output_dir / 'location.txt').exists():
        if not same_geometry(areas, forward.read_location(output_dir / 'location.txt')):
            raise ConversionError('existing Binary location.txt conflicts with NetCDF geometry (even with --force)')
    selected_areas = areas
    if areas_filter:
        wanted = set(areas_filter)
        selected_areas = [area for area in areas if area['carea'] in wanted]
        if len(selected_areas) != len(wanted):
            raise ConversionError('one or more --areas names are absent from location.txt')
    rows = forward.registry_rows(registry)
    all_variables = variables == ['all']
    if all_variables:
        variables = forward.registered_variables(rows)
    tasks, skipped = [], 0
    lib = read_api()
    for area in selected_areas:
        for variable in variables:
            source = source_dir / f"{area['carea']}.{variable}.nc"
            if not source.is_file():
                if all_variables:
                    print(f'[SKIP missing optional input] {source}', flush=True)
                    continue
                raise ConversionError(f'missing input tile: {source}')
            selected = tile_rows(rows, hires, area, variable)
            # Preflight every selected input, including skipped outputs, before restoring metadata.
            ncid = ctypes.c_int()
            forward.check(lib, lib.nc_open(os.fsencode(source), 0, ctypes.byref(ncid)), f'open {source}')
            try:
                validate_netcdf(lib, ncid.value, area, selected)
            except (ValueError, RuntimeError) as error:
                raise ConversionError(f'{source.name}: {error}') from error
            finally:
                lib.nc_close(ncid.value)
            output = output_dir / f"{area['carea']}.{variable}.bin"
            if output.exists() and not force:
                skipped += 1
                print(f'[SKIP] {output}', flush=True)
            else:
                tasks.append((source, output, area, selected, force))
    output_dir.mkdir(parents=True, exist_ok=True)
    total, done, failed = len(tasks), 0, []
    if jobs == 1:
        for task in tasks:
            try:
                restore_tile(task)
                done += 1
                print(f'[{done}/{total}] SUCCESS {task[0].name}', flush=True)
            except Exception as error:
                failed.append(f'{task[0].name}: {error}')
                print(f'[FAILED] {failed[-1]}', file=sys.stderr, flush=True)
    elif tasks:
        with ProcessPoolExecutor(max_workers=jobs) as pool:
            futures = {pool.submit(restore_tile, task): task for task in tasks}
            for future in as_completed(futures):
                task = futures[future]
                try:
                    future.result()
                    done += 1
                    print(f'[{done}/{total}] SUCCESS {task[0].name}', flush=True)
                except Exception as error:
                    failed.append(f'{task[0].name}: {error}')
                    print(f'[FAILED] {failed[-1]}', file=sys.stderr, flush=True)
    if failed:
        raise ConversionError('; '.join(failed))
    # All selected coordinates were preflighted; preserve existing equivalent geometry verbatim.
    restore_location(source_dir / 'location.txt', output_dir / 'location.txt', areas)
    print(f'SUCCESS: restored {done}, skipped {skipped}; {output_dir}', flush=True)
    return done, skipped


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--map-dir', type=Path, required=True)
    parser.add_argument('--hires', required=True, help='space-separated high-resolution directory tags, e.g. 1min 3sec')
    parser.add_argument('--variables', required=True, help='all available registered products, or space-separated registered Binary file stems')
    parser.add_argument('--areas', help='optional space-separated carea names; default all location.txt areas')
    parser.add_argument('--registry', type=Path, default=Path(__file__).resolve().parents[3] / 'variable_table/map_variables.csv')
    parser.add_argument('--jobs', type=int, default=1)
    parser.add_argument('--force', action='store_true', default=True, help=argparse.SUPPRESS)
    parser.add_argument('--no-overwrite', dest='force', action='store_false', default=True,
                        help='keep existing Binary outputs')
    args = parser.parse_args()
    variables = list(dict.fromkeys(args.variables.split()))
    hires_tags = list(dict.fromkeys(args.hires.split()))
    if args.jobs < 1 or not variables or not hires_tags:
        parser.error('jobs must be positive; variables and hires must be nonempty')
    try:
        for hires in hires_tags:
            restore(args.map_dir.resolve(), hires, variables, args.registry.resolve(), args.jobs,
                    args.force, args.areas.split() if args.areas else None)
    except (OSError, ValueError, RuntimeError) as error:
        print(f'ERROR: {error}', file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print('ERROR: interrupted; completed files may remain (no whole-directory rollback)', file=sys.stderr)
        return 130
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

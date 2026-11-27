#!/usr/bin/env python3
"""Stream registered numeric map rasters to lossless, georeferenced COG caches.

Scientific NetCDF remains authoritative. Native pixels are verified byte-for-byte;
internal overviews alone are display representatives (float average / integer nearest).
"""
from __future__ import annotations

import argparse
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import dataclass
import itertools
import math
import os
from pathlib import Path
import sys
import tempfile

import netCDF4
import numpy as np
import rasterio
from rasterio.enums import Resampling
from rasterio.shutil import copy as raster_copy
from rasterio.transform import from_origin
from rasterio.windows import Window

try:
    from . import convert_map_binary_to_netcdf as base
    from . import convert_highres_binary_to_netcdf as hires
except ImportError:
    import convert_map_binary_to_netcdf as base
    import convert_highres_binary_to_netcdf as hires

DEFAULT_REGISTRY = Path(__file__).resolve().parents[3] / 'variable_table/map_variables.csv'
# These known non-target inputs coexist with individual numeric raster files.
EXCLUDED_INPUTS = {
    'bifprm.nc': 'bifurcation parameter table; not a geographic grid raster',
    'rivclim.nc': 'legacy consolidated map container; use individual map NetCDF rasters',
    'rivpar.nc': 'legacy consolidated parameter container; use individual map NetCDF rasters',
}
SUPPORTED_DTYPES = {'int8', 'uint8', 'int16', 'uint16', 'int32', 'uint32', 'float32', 'float64'}


class Unsupported(ValueError):
    """A registered product cannot be represented without changing its contract."""


def excluded_input_reason(source):
    if source.name in EXCLUDED_INPUTS:
        return EXCLUDED_INPUTS[source.name]
    if source.name.startswith('inpmat_'):
        return 'input-grid mapping matrix; not a geographic raster'
    if source.stem in {'subbsn-sample', 'subcol-sample'}:
        return 'sample Binary-to-NetCDF variant; not a registered map raster'
    return ''


@dataclass
class Task:
    source: Path
    target: Path
    rows: list
    geometry: dict
    skip_reason: str = ""


@dataclass
class Band:
    name: str
    indices: tuple
    tags: dict


def base_geometry(path):
    nx, ny, layers, step, west, east, south, north = base.read_params(path)
    if nx < 1 or ny < 1 or step <= 0 or layers < 1:
        raise ValueError(f'{path}: invalid map dimensions/resolution')
    return dict(nx=nx, ny=ny, layers=layers, resolution=step,
                west=west, east=east, south=south, north=north)


def resolve_resolutions(map_dir, requested):
    """Choose the first available standard NetCDF directory, coarse to fine."""
    if requested == ['auto']:
        selected = next((tag for tag in ('1min', '30sec', '15sec')
                         if (map_dir / tag / 'location.txt').is_file()), None)
        resolutions = ['base', selected] if selected else ['base']
        print('AUTO resolutions: ' + ' '.join(resolutions))
        return resolutions
    if not requested or any(x != 'base' and (not x.isalnum() or not x[0].isdigit()) for x in requested):
        raise ValueError('resolutions must be auto alone, or base and/or native tags such as 15sec, 1min, 3sec')
    return requested



def rows_for_base_variant(source, groups):
    """Resolve a standard MPI filename or a single canonical NetCDF variable.

    Single-variable variants carry their variable identity inside NetCDF; do not
    guess it from suffixes or infer a choice among multi-variable/alias groups.
    Metadata only is opened here. Full storage/geometry checks remain in inspect.
    """
    standard = base.standard_binary_filename(source.stem + '.bin')[:-4]
    if standard != source.stem:
        return groups.get(standard, [])
    if source.stem.startswith('mpireg-'):
        return []
    try:
        with netCDF4.Dataset(source, 'r') as ds:
            names = [name for name, var in ds.variables.items() if len(var.dimensions) >= 2]
    except (OSError, RuntimeError):
        # Keep malformed inputs as per-file conversion errors, not plan aborts.
        return []
    if len(names) != 1:
        return []
    selected = groups.get(names[0], [])
    if (len(selected) == 1 and selected[0]['name'] == names[0]
            and selected[0]['dimensions'] in ('NX,NY', 'NX,NY,NLFP')):
        return selected
    return []


def plan(map_dir, resolutions, variables, registry):
    """Use the canonical CSV for filenames, record order, types and scientific labels."""
    rows = hires.registry_rows(registry)
    tasks = []
    requested = None if variables == ['all'] else set(variables)
    found = set()
    for resolution in resolutions:
        if resolution == 'base':
            groups = {}
            for row in rows:
                if row.get('product_kind') not in {'binary_map', 'binary_mult'}:
                    continue
                for filename in row['filename'].split(';'):
                    filename = filename.strip()
                    if (not filename.startswith('inpmat_') and '/' not in filename
                            and filename.endswith('.nc') and '<' not in filename):
                        groups.setdefault(filename[:-4], []).append(row)
            directory = map_dir
            geometry = base_geometry(map_dir)
            matched = set()
            for stem, selected in groups.items():
                if requested is not None and stem not in requested:
                    continue
                found.add(stem)
                sources = set(directory.glob(stem + '.nc'))
                if stem == 'mpireg':
                    sources.update(source for source in directory.glob('mpireg-*.nc')
                                   if base.standard_binary_filename(source.stem + '.bin') == 'mpireg.bin')
                sources = sorted(sources)
                if not sources:
                    print(f'SKIP missing registered NetCDF: {directory / (stem + ".nc")}')
                for source in sources:
                    if source in matched:
                        continue
                    matched.add(source)
                    tasks.append(Task(source, map_dir / 'COG' / source.with_suffix('.tif').name,
                                      selected, geometry))
            # Known non-target tables/containers are normal skips, not failed conversions.
            for source in sorted(directory.glob('*.nc')):
                if source not in matched and (requested is None or source.stem in requested):
                    reason = excluded_input_reason(source)
                    selected = [] if reason else rows_for_base_variant(source, groups)
                    if reason or selected:
                        found.add(source.stem)
                    tasks.append(Task(source, map_dir / 'COG' / source.with_suffix('.tif').name,
                                      selected, geometry, skip_reason=reason))
        else:
            directory = map_dir / resolution
            if not directory.is_dir():
                print(f'SKIP missing NetCDF directory: {directory}')
                continue
            products = hires.registered_variables(rows)
            selected_products = products if requested is None else [x for x in products if x in requested]
            found.update(selected_products)
            for area in hires.read_location(directory / 'location.txt'):
                if Path(str(area['carea'])).name != area['carea'] or area['carea'] in ('.', '..'):
                    raise ValueError('location.txt carea must be a filename component')
                for product in selected_products:
                    source = directory / f'{area["carea"]}.{product}.nc'
                    if not source.is_file():
                        print(f'SKIP missing registered NetCDF: {source}')
                        continue
                    selected = hires.rows_for_tile(rows, resolution, str(area['carea']), product)
                    tasks.append(Task(source, map_dir / 'COG' / resolution / source.with_suffix('.tif').name,
                                      selected, area))
    if requested is not None and requested - found:
        raise ValueError(f'No registered product selected: {sorted(requested - found)}')
    return tasks


def axis(ds, candidates, size, origin, step):
    """Validate regular cell centers in bounded vector chunks; accept either direction."""
    name = next((x for x in candidates if x in ds.variables), None)
    if name is None:
        raise Unsupported(f'missing coordinate {candidates[0]}')
    var = ds[name]
    if var.ndim != 1 or len(var) != size or var.dtype.kind != 'f':
        raise Unsupported(f'{name}: expected floating 1-D coordinate of length {size}')
    for attr in ('scale_factor', 'add_offset', '_Unsigned'):
        if attr in var.ncattrs():
            raise Unsupported(f'{name}: packed coordinates are unsupported')
    units = str(getattr(var, 'units', '')).lower()
    allowed = ('degrees_east', 'degree_east', 'degrees_e', 'degree_e') if candidates[0] == 'lon' else (
        'degrees_north', 'degree_north', 'degrees_n', 'degree_n')
    # Some legacy auxiliary rasters have coordinate vectors without CF units.
    # Their values are still accepted only if every center matches the
    # authoritative map geometry below; an explicit incompatible unit fails.
    if units and units not in allowed:
        raise Unsupported(f'{name}: expected geographic degree coordinate units')
    first, last = float(var[0]), float(var[-1])
    reverse = size > 1 and (last - first) * step < 0
    # Derive the transform from source centers, not rounded metadata bounds.
    actual_step = ((first - last) if reverse else (last - first)) / (size - 1) if size > 1 else step
    if not math.isfinite(actual_step) or actual_step * step <= 0:
        raise Unsupported(f'{name}: invalid coordinate direction/spacing')
    tolerance = max(2e-5, abs(step) * 1e-4, np.finfo(var.dtype).eps * max(abs(first), abs(last), 1) * 4)
    for start in range(0, size, 4096):
        stop = min(size, start + 4096)
        values = np.asarray(var[start:stop])
        logical = size - 1 - np.arange(start, stop) if reverse else np.arange(start, stop)
        expected = origin + (logical + .5) * step
        regular = (last if reverse else first) + logical * actual_step
        if not np.all(np.isfinite(values)) or not np.allclose(values, expected, rtol=0, atol=tolerance):
            raise Unsupported(f'{name}: coordinates conflict with params.txt/location.txt')
        if not np.allclose(values, regular, rtol=0, atol=max(abs(step) * 1e-6, tolerance / 4)):
            raise Unsupported(f'{name}: irregular coordinate grid cannot use an affine GeoTIFF')
    edge = (last if reverse else first) - actual_step / 2
    return var.dimensions[0], reverse, edge, actual_step


def nodata_value(var, row):
    values = []
    for attr in ('_FillValue', 'missing_value'):
        if attr in var.ncattrs():
            raw = np.asarray(var.getncattr(attr))
            if raw.size != 1:
                raise Unsupported(f'{var.name}: multiple missing codes cannot use one GeoTIFF NoData')
            values.append(raw.item())
    if not values and row.get('missing_value'):
        values.append(float(row['missing_value']))
    if not values:
        return None
    cast = np.asarray(values, dtype=var.dtype)
    if not np.all((cast == cast[0]) | (np.isnan(cast) & np.isnan(cast[0]))):
        raise Unsupported(f'{var.name}: differing fill/missing codes need separate masks; unsupported')
    if any(not (float(a) == float(b) or (math.isnan(float(a)) and math.isnan(float(b))))
           for a, b in zip(values, cast)):
        raise Unsupported(f'{var.name}: NoData cannot be represented exactly in storage dtype')
    return cast[0].item()


def inspect(ds, task):
    """Resolve registered planes before allocating buffers; never silently drop a variable."""
    if not task.rows:
        raise Unsupported('no registered numeric raster mapping for this filename')
    g = task.geometry
    xdim, rx, west, dx = axis(ds, ('lon', 'longitude'), g['nx'], g['west'], g['resolution'])
    ydim, ry, north, dy = axis(ds, ('lat', 'latitude'), g['ny'], g['north'], -g['resolution'])
    transform = from_origin(west, north, dx, -dy)
    tolerance = max(2e-5, g['resolution'] * 1e-3)
    if abs((west + g['nx'] * dx) - g['east']) > tolerance or abs((north + g['ny'] * dy) - g['south']) > tolerance:
        raise Unsupported('NetCDF edges conflict with params.txt/location.txt bounds')
    rows = sorted(task.rows, key=lambda r: int(r['record_index'] or 1))
    bands, dtypes, fills, names = [], set(), [], set()
    for row in rows:
        if row['dimensions'] not in ('NX,NY', 'NX,NY,NLFP', 'NX_HIRES,NY_HIRES'):
            raise Unsupported(f'{row["name"]}: unsupported registered dimensions {row["dimensions"]}')
        name = row['name']
        if name not in ds.variables and name in ('nextx_noedge', 'nexty_noedge'):
            name = name.replace('_noedge', '')
        if name not in ds.variables and name in ('catmxx', 'catmyy'):
            name = {'catmxx': 'catmx', 'catmyy': 'catmy'}[name]
        if name not in ds.variables:
            raise Unsupported(f'missing registered variable {row["name"]}')
        var = ds[name]
        if var.dtype.name not in SUPPORTED_DTYPES or var.dtype.name != row['dtype']:
            raise Unsupported(f'{name}: unsupported or registry-conflicting storage dtype {var.dtype}')
        for attr in var.ncattrs():
            if attr in ('scale_factor', 'add_offset', '_Unsigned') or attr.startswith('_Quantize'):
                raise Unsupported(f'{name}: packing/signedness/quantization attribute {attr} unsupported')
        if var.dimensions.count(xdim) != 1 or var.dimensions.count(ydim) != 1:
            raise Unsupported(f'{name}: missing/duplicate spatial dimensions')
        extra = tuple(d for d in var.dimensions if d not in (ydim, xdim))
        if row['dimensions'] == 'NX,NY,NLFP' and (len(extra) != 1 or len(ds.dimensions[extra[0]]) != g['layers']):
            raise Unsupported(f'{name}: floodplain layer count conflicts with params.txt')
        if ds.data_model.startswith('NETCDF4'):
            var.set_var_chunk_cache(size=1024 * 1024, nelems=1009, preemption=.75)
        dtypes.add(var.dtype.name)
        fills.append(nodata_value(var, row))
        names.add(name)
        shape = tuple(len(ds.dimensions[d]) for d in extra)
        if len(bands) + math.prod(shape) > 65535:
            raise Unsupported('record/layer population exceeds GeoTIFF band limit65535')
        for indices in itertools.product(*(range(n) for n in shape)):
            tags = dict(source_variable=name, registry_name=row['name'], source_dtype=var.dtype.name,
                        source_dimensions=','.join(var.dimensions),
                        source_record_1based=row['record_index'] or '1',
                        source_indices_1based=','.join(f'{d}={i+1}' for d, i in zip(extra, indices)),
                        units=str(getattr(var, 'units', row.get('units', ''))),
                        long_name=str(getattr(var, 'long_name', row['long_name'])),
                        physical_description=row['physical_description'],
                        missing_value=repr(fills[-1]))
            bands.append(Band(name, indices, tags))
    unexpected = [n for n, v in ds.variables.items() if xdim in v.dimensions and ydim in v.dimensions and n not in names]
    if unexpected:
        raise Unsupported(f'unregistered/unmapped spatial variables: {unexpected}')
    if not bands or len(bands) > 65535 or len(dtypes) != 1:
        raise Unsupported('empty/excessive band count or mixed storage types in one GeoTIFF')
    first = fills[0]
    if any(not (v == first or (v is not None and first is not None and math.isnan(v) and math.isnan(first))) for v in fills):
        raise Unsupported('different per-band NoData values cannot share one GeoTIFF NoData')
    return bands, next(iter(dtypes)), first, transform, (ydim, xdim, ry, rx)


def windows(nx, ny, edge):
    for row in range(0, ny, edge):
        for col in range(0, nx, edge):
            yield Window(col, row, min(edge, nx-col), min(edge, ny-row))


def read_plane(ds, band, axes, window):
    """Native values, transposed/flipped only to north-to-south, west-to-east rows."""
    ydim, xdim, ry, rx = axes
    var = ds[band.name]
    ny, nx = len(ds.dimensions[ydim]), len(ds.dimensions[xdim])
    y, x, h, w = map(int, (window.row_off, window.col_off, window.height, window.width))
    slices = {ydim: slice(ny-y-h, ny-y) if ry else slice(y, y+h),
              xdim: slice(nx-x-w, nx-x) if rx else slice(x, x+w)}
    extra = iter(band.indices)
    key = tuple(slices[d] if d in slices else next(extra) for d in var.dimensions)
    data = np.asarray(var[key])
    if [d for d in var.dimensions if d in slices] != [ydim, xdim]:
        data = data.T
    if ry:
        data = data[::-1]
    if rx:
        data = data[:, ::-1]
    return np.ascontiguousarray(data)


def verify(ds, path, bands, dtype, fill, transform, axes, nx, ny, edge, levels):
    with rasterio.open(path) as dst:
        if dst.crs != rasterio.crs.CRS.from_epsg(4326) or dst.transform != transform:
            raise ValueError('COG CRS/transform verification failed')
        if dst.dtypes != (dtype,) * len(bands) or dst.count != len(bands) or not dst.is_tiled:
            raise ValueError('COG type/band/tile verification failed')
        if dst.tags(ns='IMAGE_STRUCTURE').get('LAYOUT') != 'COG':
            raise ValueError('GDAL did not produce COG layout')
        if dst.overviews(1) != levels:
            raise ValueError(f'COG overview factors differ: {dst.overviews(1)} vs {levels}')
        for index, band in enumerate(bands, 1):
            if dst.tags(index).get('source_variable') != band.name:
                raise ValueError('COG band metadata correspondence failed')
            for window in windows(nx, ny, edge):
                original = read_plane(ds, band, axes, window)
                actual = dst.read(index, window=window)
                if original.tobytes() != actual.tobytes():
                    raise ValueError(f'{band.name}: native pixel bytes differ at {window}')
                valid = np.ones(original.shape, bool) if fill is None else (
                    ~np.isnan(original) if math.isnan(fill) else original != fill)
                if not np.array_equal(dst.read_masks(index, window=window) != 0, valid):
                    raise ValueError(f'{band.name}: NoData mask differs at {window}')


def convert(task, blocksize=512, compression='DEFLATE', overviews=(2, 4, 8, 16, 32), force=True):
    """Stage tiled TIFF/overviews then COG, verify every native block, atomically publish."""
    if task.skip_reason:
        return f'SKIP excluded input: {task.source} ({task.skip_reason})'
    if task.target.exists() and not force:
        return f'SKIP existing COG: {task.target}'
    task.target.parent.mkdir(parents=True, exist_ok=True)
    netCDF4.set_chunk_cache(4 * 1024 * 1024, 1009, .75)
    with tempfile.TemporaryDirectory(prefix=f'.{task.target.stem}.', dir=task.target.parent) as temp:
        stage, final = Path(temp) / 'native.tif', Path(temp) / 'complete.tif'
        # Bound both block caching and overview work buffers, not only Python reads.
        with rasterio.Env(GDAL_CACHEMAX=16 * 1024 * 1024, GDAL_NUM_THREADS='1',
                          GDAL_OVR_CHUNK_MAX_SIZE='2097152', GDAL_TIFF_OVR_BLOCKSIZE='128'), netCDF4.Dataset(task.source) as ds:
            ds.set_auto_maskandscale(False)
            bands, dtype, fill, transform, axes = inspect(ds, task)
            nx, ny = task.geometry['nx'], task.geometry['ny']
            # Integer indices/codes always select the same original pixel across bands.
            method = 'nearest' if np.dtype(dtype).kind in 'iu' else 'average'
            levels = [n for n in overviews if math.ceil(nx/n) >= 1 and math.ceil(ny/n) >= 1 and n <= min(nx, ny)]
            # GDAL reports effective width-based factors after integer rounding.
            unique = {}
            for n in levels:
                unique.setdefault(round(nx / math.ceil(nx/n)), n)
            levels = list(unique.values())
            profile = dict(driver='GTiff', width=nx, height=ny, count=len(bands), dtype=dtype,
                           crs='EPSG:4326', transform=transform, nodata=fill, tiled=True,
                           blockxsize=blocksize, blockysize=blocksize, compress=compression,
                           BIGTIFF='IF_SAFER')
            with rasterio.open(stage, 'w', **profile) as dst:
                dst.update_tags(source_file=task.source.name, overview_resampling=method,
                                purpose='numeric visualization cache; overviews are display representatives',
                                native_verification='byte-for-byte all pixels; no scaling or quantization')
                for index, band in enumerate(bands, 1):
                    dst.set_band_description(index, band.name + (' ' + band.tags['source_indices_1based'] if band.indices else ''))
                    dst.update_tags(index, **band.tags)
                    if band.tags['units']:
                        dst.set_band_unit(index, band.tags['units'])
                    for window in windows(nx, ny, blocksize):
                        dst.write(read_plane(ds, band, axes, window), index, window=window)
                dst.build_overviews(levels, getattr(Resampling, method))
            raster_copy(stage, final, driver='COG', BLOCKSIZE=blocksize, COMPRESS=compression,
                        OVERVIEWS='FORCE_USE_EXISTING', BIGTIFF='IF_SAFER', NUM_THREADS='1')
            effective = [round(nx / math.ceil(nx/n)) for n in levels]
            verify(ds, final, bands, dtype, fill, transform, axes, nx, ny, blocksize, effective)
        if force:
            os.replace(final, task.target)
        else:
            # Atomic no-clobber publication, including another writer finishing mid-conversion.
            try:
                os.link(final, task.target)
            except FileExistsError:
                return f'SKIP concurrently created COG: {task.target}'
        return f'PASS {task.source} -> {task.target} ({len(bands)} bands; {dtype}; {method}; native bytes verified)'


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--map-dir', type=Path)
    parser.add_argument('--resolutions', default='auto',
                        help='auto: base plus first available 1min, 30sec, 15sec; '
                             'or explicit tags, e.g. "base 1min"')
    parser.add_argument('--variables', default='all', help='registered or resolved variant file stems separated by spaces; mpireg selects its numbered family')
    parser.add_argument('--registry', type=Path, default=DEFAULT_REGISTRY)
    parser.add_argument('--blocksize', type=int, default=512)
    parser.add_argument('--compression', choices=['DEFLATE', 'LZW', 'ZSTD', 'NONE'], default='DEFLATE')
    parser.add_argument('--overviews', default='2 4 8 16 32')
    parser.add_argument('--jobs', type=int, default=4)
    parser.add_argument('--force', action='store_true', default=True, help=argparse.SUPPRESS)
    parser.add_argument('--no-overwrite', dest='force', action='store_false',
                        help='keep existing COG outputs')
    args = parser.parse_args(argv)
    try:
        levels = [int(n) for n in args.overviews.split()]
        if not 128 <= args.blocksize <= 4096 or args.blocksize % 16 or args.jobs < 1:
            raise ValueError('blocksize must be128..4096 and divisible by16; jobs must be positive')
        if levels != sorted(set(levels)) or any(n < 2 or n & (n-1) for n in levels):
            raise ValueError('overview factors must be increasing unique powers of two >=2')
        map_dir = args.map_dir
        if map_dir is None:
            cwd = Path.cwd()
            if cwd.name != 'script_format_conv' or cwd.parent.name == 'tools':
                raise ValueError('run from <map>/script_format_conv/ or pass --map-dir PATH')
            map_dir = cwd.parent
        resolutions = resolve_resolutions(map_dir, args.resolutions.split())
        tasks = plan(map_dir.resolve(), resolutions, args.variables.split(), args.registry)
        print(f'COG tasks: {len(tasks)}; workers: {args.jobs}; GDAL block cache <=16MiB per worker; full native verification')
        failed, unsupported, passed, skipped = 0, 0, 0, 0
        options = (args.blocksize, args.compression, levels, args.force)
        def report(task, result=None, error=None):
            nonlocal failed, unsupported, passed, skipped
            if isinstance(error, Unsupported):
                unsupported += 1
                print(f'UNSUPPORTED {task.source}: {error}', file=sys.stderr)
            elif error:
                failed += 1
                print(f'FAIL {task.source}: {error}', file=sys.stderr)
            else:
                skipped += result.startswith('SKIP')
                passed += result.startswith('PASS')
                print(result)
        if args.jobs == 1:
            for task in tasks:
                try:
                    result = convert(task, *options)
                except Exception as exc:
                    report(task, error=exc)
                else:
                    report(task, result=result)
        else:
            with ProcessPoolExecutor(max_workers=args.jobs) as pool:
                futures = {pool.submit(convert, task, *options): task for task in tasks}
                for future in as_completed(futures):
                    try:
                        result = future.result()
                    except Exception as exc:
                        report(futures[future], error=exc)
                    else:
                        report(futures[future], result=result)
        print(f'Summary: {passed} PASS; {skipped} SKIP; {unsupported} UNSUPPORTED; {failed} FAIL')
        return 1 if failed or unsupported else 0
    except (OSError, ValueError) as exc:
        print(f'ERROR: {exc}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())

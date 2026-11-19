#!/usr/bin/env python3
"""Extract daily regional runoff from annual ELSE_GPCC NetCDF without aggregation.

Cell-edge alignment preserves the original grid rather than interpolating it.
Monthly/yearly files retain calendar-period record positions; unrequested dates
are missing-value slots, not averages or additional source-data extraction.
"""

import argparse
import calendar
from contextlib import ExitStack
from datetime import date, timedelta
from pathlib import Path
import os
import sys
import tempfile

import numpy as np
from netCDF4 import Dataset, num2date


def aligned_index(value, origin, spacing, label):
    """Retain the original extractor's requirement for cell-edge alignment."""
    index = round((value - origin) / spacing)
    if not np.isclose(origin + index * spacing, value, rtol=0, atol=1e-6):
        raise ValueError(f"{label}={value} is not aligned with a source cell edge")
    return index


def days(start, end):
    while start <= end:
        yield start
        start += timedelta(days=1)


def group_limits(day, unit):
    if unit == 'day':
        return day, day, day.strftime('%Y%m%d')
    if unit == 'month':
        return day.replace(day=1), day.replace(day=calendar.monthrange(day.year, day.month)[1]), day.strftime('%Y%m')
    return date(day.year, 1, 1), date(day.year, 12, 31), day.strftime('%Y')


def source_grid(ds, args):
    """Map cell edges to indices; normalize 0–360 longitude to the requested branch."""
    lon = np.asarray(ds['longitude'][:], dtype='f8')
    lat = np.asarray(ds['latitude'][:], dtype='f8')
    if lon.ndim != 1 or lat.ndim != 1 or min(lon.size, lat.size) < 2:
        raise ValueError('longitude/latitude must be one-dimensional regular cell-center axes')
    if not np.all(np.isfinite(lon)) or not np.all(np.isfinite(lat)):
        raise ValueError('non-finite coordinates')
    dx, dy = abs(lon[1] - lon[0]), abs(lat[1] - lat[0])
    if not np.allclose(abs(np.diff(lon)), dx) or not np.allclose(abs(np.diff(lat)), dy):
        raise ValueError('source grid must be regular and monotonic')
    if not (np.all(np.diff(lon) > 0) or np.all(np.diff(lon) < 0)):
        raise ValueError('longitude must be monotonic')
    if not (np.all(np.diff(lat) > 0) or np.all(np.diff(lat) < 0)):
        raise ValueError('latitude must be monotonic')
    if not np.isclose(dx * lon.size, 360):
        raise ValueError('expected a global longitude grid without a duplicate seam column')
    unwrapped = (lon - args.west) % 360 + args.west
    order = np.argsort(unwrapped)
    sorted_lon = unwrapped[order]
    aligned_index(args.west, sorted_lon[0] - dx / 2, dx, 'west')
    nx = aligned_index(args.east, args.west, dx, 'east')
    xs = order[sorted_lon < args.east]
    top, bottom = max(lat) + dy / 2, min(lat) - dy / 2
    if args.north > top + 1e-6 or args.south < bottom - 1e-6:
        raise ValueError('latitude bounds lie outside the source grid')
    y0 = aligned_index(top - args.north, 0, dy, 'north')
    y1 = aligned_index(top - args.south, 0, dy, 'south')
    ys = np.argsort(-lat)[y0:y1]
    if len(xs) != nx or len(ys) != y1 - y0 or nx < 1 or len(ys) < 1:
        raise ValueError('empty or incomplete geographic selection')
    return xs, ys, sorted_lon[:nx], lat[ys]


def inspect_source(ds):
    var = ds['runoff']
    if var.dimensions != ('time', 'latitude', 'longitude') or var.dtype != np.dtype('float32'):
        raise ValueError('expected float32 runoff(time, latitude, longitude)')
    if hasattr(var, 'scale_factor') or hasattr(var, 'add_offset'):
        raise ValueError('packed runoff is unsupported; expected unpacked float32')
    missing = float(getattr(var, 'missing_value', getattr(var, '_FillValue', -999)))
    if not np.isfinite(missing):
        raise ValueError('a finite missing-value sentinel is required for Binary output')
    if hasattr(var, '_FillValue') and float(var._FillValue) != missing:
        raise ValueError('different _FillValue and missing_value sentinels are unsupported')
    if getattr(var, 'units', '') not in ('mm day-1', 'mm/day'):
        raise ValueError('expected daily runoff units mm day-1 or mm/day')
    tv = ds['time']
    cal = getattr(tv, 'calendar', 'standard')
    if cal not in ('standard', 'gregorian', 'proleptic_gregorian'):
        raise ValueError(f'unsupported calendar: {cal}')
    stamps = num2date(tv[:], tv.units, calendar=cal)
    mapping = {}
    for index, stamp in enumerate(stamps):
        key = date(stamp.year, stamp.month, stamp.day)
        if key in mapping:
            raise ValueError(f'duplicate daily time record: {key}')
        mapping[key] = index
    # Daily interval bounds establish that each named day represents a full daily record.
    bounds = ds[getattr(tv, 'bounds', 'time_bounds')]
    decoded = num2date(bounds[:], tv.units, calendar=cal)
    for index, stamp in enumerate(stamps):
        lo, hi = decoded[index]
        if (lo.year, lo.month, lo.day, lo.hour, lo.minute, lo.second) != (stamp.year, stamp.month, stamp.day, 0, 0, 0) or (hi - lo).total_seconds() != 86400:
            raise ValueError('expected midnight-to-midnight daily CF time bounds')
    return var, mapping, missing


def write_netcdf(path, first, last, lon, lat, var, missing, get_field):
    """Write one daily slice at a time; preserve units, cell meaning and CF bounds."""
    count = (last - first).days + 1
    with Dataset(path, 'w', format='NETCDF4') as out:
        for name, size in [('time', count), ('bounds', 2), ('latitude', len(lat)), ('longitude', len(lon))]:
            out.createDimension(name, size)
        for name, data, units, axis in [('longitude', lon, 'degrees_east', 'X'), ('latitude', lat, 'degrees_north', 'Y')]:
            coord = out.createVariable(name, 'f4', (name,))
            coord[:] = data
            coord.setncatts(dict(standard_name=name, units=units, axis=axis))
        tv = out.createVariable('time', 'f8', ('time',))
        tv.setncatts(dict(standard_name='time', units=f'days since {first.isoformat()} 00:00:00', calendar='proleptic_gregorian', bounds='time_bounds'))
        tv[:] = np.arange(count) + 0.5
        bounds = out.createVariable('time_bounds', 'f8', ('time', 'bounds'))
        bounds[:] = np.column_stack((np.arange(count), np.arange(count) + 1))
        rv = out.createVariable('runoff', 'f4', ('time', 'latitude', 'longitude'), fill_value=missing, zlib=True, complevel=3, shuffle=True)
        attrs = {key: var.getncattr(key) for key in var.ncattrs() if key in ('units', 'long_name', 'standard_name', 'cell_methods', 'missing_value')}
        rv.setncatts(attrs)
        for index, day in enumerate(days(first, last)):
            rv[index] = get_field(day)
        out.Conventions = 'CF-1.8'
        out.history = 'Regional extraction from annual ELSE_GPCC NetCDF; no averaging or precision reduction'
        out.selection_padding = 'Daily slots outside requested dates contain the source missing-value sentinel'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input-dir', type=Path, required=True)
    parser.add_argument('--output-dir', type=Path, required=True)
    for name in ('west', 'east', 'south', 'north'):
        parser.add_argument('--' + name, type=float, required=True)
    parser.add_argument('--start-date', type=date.fromisoformat, required=True)
    parser.add_argument('--end-date', type=date.fromisoformat, required=True)
    parser.add_argument('--format', choices=['netcdf', 'binary'], required=True)
    parser.add_argument('--file-unit', choices=['day', 'month', 'year'], required=True)
    args = parser.parse_args()
    if not all(np.isfinite(v) for v in (args.west, args.east, args.south, args.north)) or not (0 < args.east - args.west <= 360 and -90 <= args.south < args.north <= 90):
        parser.error('require west < east <= west+360 and -90 <= south < north <= 90')
    if args.start_date > args.end_date:
        parser.error('start-date must not follow end-date')
    source, target = args.input_dir.resolve(), args.output_dir.resolve()
    if target == source or source in target.parents:
        parser.error('output must be outside the read-only input directory')
    groups = {}
    for day in days(args.start_date, args.end_date):
        first, last, tag = group_limits(day, args.file_unit)
        groups[tag] = (first, last)
    prefix, suffix = ('runoff', '.nc') if args.format == 'netcdf' else ('Roff____', '.one')
    for tag in groups:
        if (target / (prefix + tag + suffix)).exists():
            raise FileExistsError(f'refusing to overwrite {target / (prefix + tag + suffix)}')
    with ExitStack() as stack:
        sources = {}
        reference = None
        for year in range(args.start_date.year, args.end_date.year + 1):
            ds = stack.enter_context(Dataset(source / f'runoff{year}.nc'))
            xs, ys, lon, lat = source_grid(ds, args)
            var, mapping, missing = inspect_source(ds)
            if reference is not None and (not np.array_equal(lon, reference[0]) or not np.array_equal(lat, reference[1]) or missing != reference[2] or var.units != reference[3]):
                raise ValueError('source coordinates, missing values or units differ between years')
            reference = (lon, lat, missing, var.units)
            sources[year] = (var, mapping, xs, ys)
        for day in days(args.start_date, args.end_date):
            if day not in sources[day.year][1]:
                raise ValueError(f'missing daily source record: {day}')
        lon, lat, missing, _ = reference

        def get_field(day):
            if not args.start_date <= day <= args.end_date:
                return np.full((len(lat), len(lon)), missing, dtype='f4')
            var, mapping, xs, ys = sources[day.year]
            field = np.ma.filled(var[mapping[day], ys, xs], missing).astype('f4')
            if not np.all(np.isfinite(field)):
                raise ValueError(f'{day}: unexpected NaN or infinity')
            return field

        target.mkdir(parents=True, exist_ok=True)
        for tag, (first, last) in groups.items():
            destination = target / (prefix + tag + suffix)
            fd, temporary = tempfile.mkstemp(prefix='.runoff-', dir=target)
            os.close(fd)
            try:
                if args.format == 'binary':
                    with open(temporary, 'wb') as stream:
                        for day in days(first, last):
                            stream.write(get_field(day).astype('<f4').tobytes(order='C'))
                else:
                    write_netcdf(temporary, first, last, lon, lat, sources[max(first.year, args.start_date.year)][0], missing, get_field)
                # Publish without replacing any existing file, including a concurrent writer's output.
                os.link(temporary, destination)
            finally:
                os.unlink(temporary)
            print(f'[SUCCESS] {destination} ({(last-first).days+1} daily slots; {len(lon)} x {len(lat)})')
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except (OSError, ValueError, KeyError, RuntimeError) as error:
        print(f'[ERROR] {error}', file=sys.stderr)
        sys.exit(1)

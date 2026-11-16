#!/usr/bin/env python3
"""Runoff-grid daily climatology and mm/s exports, independent of river maps.

One native-grid preset can support many river maps: map-specific assignment belongs
only to downstream s01-channel_params.sh, not to this product's climatology.
"""
from __future__ import annotations

import argparse
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timedelta
import glob
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile

from netCDF4 import Dataset, num2date
import numpy as np

OUTPUT = Path(__file__).resolve().parents[1] / 'script_runoff_preset' / 'output'
MISSING = np.float32(-999)
SECONDS_PER_DAY = 86400


@dataclass
class Grid:
    """Unchanged runoff cell centers; arrays are always indexed (latitude, longitude)."""
    longitude: np.ndarray
    latitude: np.ndarray
    lon_name: str
    lat_name: str

    @property
    def shape(self):
        return len(self.latitude), len(self.longitude)


def checked_grid(ds, variable):
    """Identify regular rectilinear coordinates from names/CF metadata; preserve direction."""
    coordinates = {}
    for role, names, axis in [('lon', ('longitude', 'lon'), 'X'), ('lat', ('latitude', 'lat'), 'Y')]:
        found = [name for name, v in ds.variables.items() if v.ndim == 1 and v.dimensions[0] in variable.dimensions
                 and (name in names or getattr(v, 'standard_name', '') == names[0] or getattr(v, 'axis', '') == axis)]
        if len(found) != 1:
            raise ValueError(f'{ds.filepath()}: cannot uniquely identify {role} coordinate')
        name = found[0]
        allowed_units = ('degrees_east', 'degree_east') if role == 'lon' else ('degrees_north', 'degree_north')
        if getattr(ds[name], 'units', '') not in allowed_units:
            raise ValueError(f'{ds.filepath()}: {role} requires explicit geographic degree units')
        values = np.asarray(ds[name][:])
        if len(values) < 2 or not np.isfinite(values).all():
            raise ValueError(f'{ds.filepath()}: {role} needs at least two finite centers')
        delta = np.diff(values.astype('f8'))
        precision = np.finfo(values.dtype).eps if np.issubdtype(values.dtype, np.floating) else 0
        tolerance = max(1e-6, 4*precision*float(np.max(abs(values))))
        spacing = (float(values[-1])-float(values[0]))/(len(values)-1)
        if not (np.all(delta > 0) or np.all(delta < 0)) or not np.allclose(delta, spacing, rtol=1e-5, atol=tolerance):
            raise ValueError(f'{ds.filepath()}: {role} must be monotonic and regularly spaced')
        coordinates[role] = (name, values)
    return Grid(coordinates['lon'][1], coordinates['lat'][1], coordinates['lon'][0], coordinates['lat'][0])


def same_grid(a, b):
    return (a.lon_name == b.lon_name and a.lat_name == b.lat_name
            and np.array_equal(a.longitude, b.longitude) and np.array_equal(a.latitude, b.latitude))


def unit_definition(units):
    """Return mm conversion and rate/interval-depth meaning; never infer unknown units."""
    key = units.lower().replace(' ', '').replace('**', '^').replace('^', '')
    definitions = {'mm/day': (1., 'day_rate'), 'mmday-1': (1., 'day_rate'), 'mmd-1': (1., 'day_rate'),
                   'mm/s': (1., 'second_rate'), 'mms-1': (1., 'second_rate'),
                   'm/s': (1000., 'second_rate'), 'ms-1': (1000., 'second_rate'),
                   'mm/h': (1., 'hour_rate'), 'mmh-1': (1., 'hour_rate'),
                   'mm': (1., 'interval_depth'), 'm': (1000., 'interval_depth')}
    if key not in definitions:
        raise ValueError(f'Unknown runoff units {units!r}; use --input-units with a documented supported interpretation')
    return definitions[key]


def daily_depth(values, units, seconds):
    """Convert an interval mean rate or interval depth to mm over that interval.

    Negative, masked and nonfinite values are missing (NaN). Cumulative forecast
    accumulations must be differenced upstream, not reinterpreted as interval depths.
    """
    data = np.ma.asarray(values, dtype='f4').filled(np.nan)
    data = np.where(np.isfinite(data) & (data >= 0), data, np.float32(np.nan))
    factor, meaning = unit_definition(units)
    if meaning == 'day_rate':
        factor *= seconds / SECONDS_PER_DAY
    elif meaning == 'hour_rate':
        factor *= seconds / 3600
    elif meaning == 'second_rate':
        factor *= seconds
    return data * np.float32(factor)


def as_datetime(value):
    return datetime(value.year, value.month, value.day, value.hour, value.minute, value.second, value.microsecond)


def index_inputs(args):
    """Read only coordinates/time metadata; index complete Gregorian/noleap intervals.

    CF bounds are authoritative. Without bounds, an explicit interval is needed,
    or a uniform rate series whose spacing defines the interval. Depth in mm/m
    without bounds requires --interval-hours as an explicit interpretation.
    """
    pattern = args.input_pattern
    for token in ('YYYY', 'MM', 'DD', '%Y', '%m', '%d'):
        pattern = pattern.replace(token, '*')
    paths = sorted(glob.glob(str(Path(args.input_dir) / pattern)))
    if not paths:
        raise ValueError(f'No input NetCDF files: {args.input_dir}/{args.input_pattern}')
    entries, grid, calendars = [], None, set()
    for path in paths:
        with Dataset(path) as ds:
            if args.runoff_variable not in ds.variables or 'time' not in ds.variables:
                raise ValueError(f'{path}: expected {args.runoff_variable!r} and time')
            var, time = ds[args.runoff_variable], ds['time']
            cal = getattr(time, 'calendar', 'standard')
            if cal not in ('standard', 'gregorian', 'proleptic_gregorian', 'noleap', '365_day'):
                raise ValueError(f'{path}: unsupported calendar {cal!r}; normalize upstream')
            dates = num2date(time[:], time.units, calendar=cal)
            if not any(args.start_year <= d.year <= args.end_year for d in dates):
                continue
            calendars.add('noleap' if cal in ('noleap', '365_day') else 'gregorian')
            current = checked_grid(ds, var)
            if grid is not None and not same_grid(grid, current):
                raise ValueError(f'{path}: runoff coordinates/order changed within the requested period')
            grid = current
            units = getattr(var, 'units', '') if args.input_units == 'auto' else args.input_units
            _, meaning = unit_definition(units)
            if getattr(var, 'GRIB_stepType', '') == 'accum':
                raise ValueError(f'{path}: cumulative GRIB runoff must be converted to interval values first')
            bounds_name = getattr(time, 'bounds', '')
            if bounds_name:
                bounds = ds[bounds_name][:]
                if bounds.shape != (len(dates), 2) or np.ma.is_masked(bounds):
                    raise ValueError(f'{path}: invalid time bounds')
                bounds = num2date(bounds, time.units, calendar=cal)
            else:
                hours = args.interval_hours
                if hours is None:
                    if meaning == 'interval_depth' or len(dates) < 2:
                        raise ValueError(f'{path}: missing time bounds; specify --interval-hours and interval meaning')
                    spacings = [(dates[i+1]-dates[i]).total_seconds()/3600 for i in range(len(dates)-1)]
                    if not np.allclose(spacings, spacings[0]) or spacings[0] <= 0:
                        raise ValueError(f'{path}: cannot infer a uniform time interval')
                    hours = spacings[0]
                if not (0 < hours <= 24):
                    raise ValueError(f'{path}: intervals must be positive and no longer than one day')
            for i, label in enumerate(dates):
                if bounds_name:
                    start, end = bounds[i]
                    seconds = (end-start).total_seconds()
                    start, end = as_datetime(start), as_datetime(end)
                else:
                    # Daily rates without CF bounds use the named calendar day;
                    # subdaily/explicit depth labels are interpreted as interval starts.
                    start = as_datetime(label)
                    if hours == 24:
                        start = datetime(label.year, label.month, label.day)
                    end = start + timedelta(hours=hours)
                    seconds = hours*3600
                if not args.start_year <= start.year <= args.end_year:
                    continue
                if seconds <= 0 or seconds > SECONDS_PER_DAY:
                    raise ValueError(f'{path}: invalid interval duration at record {i}')
                day_end = datetime(start.year, start.month, start.day)+timedelta(days=1)
                if cal in ('noleap', '365_day') and (day_end.month, day_end.day) == (2, 29):
                    day_end += timedelta(days=1)
                if end > day_end:
                    raise ValueError(f'{path}: interval crosses a calendar-day boundary; normalize upstream')
                if len(var.dimensions) != 3 or set(var.dimensions) != {'time', grid.lat_name, grid.lon_name}:
                    raise ValueError(f'{path}: runoff must have time and the two coordinate dimensions only')
                entries.append((start, end, path, i, units, seconds))
    if grid is None or len(calendars) != 1:
        raise ValueError('No requested records, or mixed calendars')
    return grid, sorted(entries), next(iter(calendars))


def iter_daily(args, grid, entries, calendar):
    """Yield one complete day of interval depths [mm] on the original (lat,lon) grid.

    Require consecutive full days/years, never interpolate missing dates. A missing
    subinterval makes that cell's whole day missing. Only one source record and
    one day's total are held in memory, in addition to the 365 climatology sums.
    """
    expected = datetime(args.start_year, 1, 1)
    final = datetime(args.end_year+1, 1, 1)
    ds, opened, day, seconds = None, None, None, 0
    try:
        for start, end, path, i, units, duration in entries:
            if calendar == 'noleap' and expected.month == 2 and expected.day == 29:
                expected += timedelta(days=1)
            if start != expected:
                raise ValueError(f'Incomplete/overlapping time series: expected {expected}, found {start} in {path}')
            if path != opened:
                if ds is not None:
                    ds.close()
                ds, opened = Dataset(path), path
            var = ds[args.runoff_variable]
            selector = tuple(i if dim == 'time' else slice(None) for dim in var.dimensions)
            values = var[selector]
            dims = [dim for dim in var.dimensions if dim != 'time']
            if dims != [grid.lat_name, grid.lon_name]:
                values = values.T
            if day is None:
                day = np.zeros(grid.shape, dtype='f4')
            day += daily_depth(values, units, duration)
            seconds += duration
            expected = end
            if end.hour == end.minute == end.second == end.microsecond == 0:
                if seconds != SECONDS_PER_DAY:
                    raise ValueError(f'Incomplete day ending {end}: {seconds} seconds')
                yield start.date(), day
                day, seconds = None, 0
        if calendar == 'noleap' and expected.month == 2 and expected.day == 29:
            expected += timedelta(days=1)
        if expected != final or day is not None:
            raise ValueError(f'Incomplete years: stopped at {expected}, expected {final}')
    finally:
        if ds is not None:
            ds.close()


def climatology(args, modifier=None, expected_grid=None):
    """Equal-year daily climatology [mm/day]; exclude Feb 29, preserve float32 year order.

    Valid years contribute per calendar day/cell. Counts are saved; no available
    year means missing. Annual means require all 365 daily climatologies valid.
    This explicit missing policy replaces legacy summation of numeric sentinels.
    """
    grid, entries, calendar = index_inputs(args)
    if expected_grid is not None and not same_grid(grid, expected_grid):
        raise ValueError('Raw runoff grid differs from the uncorrected mean; rerun calculate')
    sums = np.zeros((365, *grid.shape), dtype='f4')
    counts = np.zeros(sums.shape, dtype='u4')
    previous_year = None
    for date, runoff_mm in iter_daily(args, grid, entries, calendar):
        if date.year != previous_year:
            print(f'[INFO] Processing runoff year {date.year}', flush=True)
            previous_year = date.year
        if (date.month, date.day) == (2, 29):
            continue
        slot = (datetime(2001, date.month, date.day)-datetime(2001, 1, 1)).days
        if modifier is not None:
            runoff_mm = modifier(runoff_mm)
        valid = np.isfinite(runoff_mm)
        sums[slot] += np.where(valid, runoff_mm, np.float32(0))
        counts[slot] += valid
    daily = np.full(sums.shape, np.nan, dtype='f4')
    np.divide(sums, counts.astype('f4'), out=daily, where=counts > 0)
    return grid, daily, counts


def annual_mean(daily):
    """Long-term rate [mm/s]: chronological float32 sum / (365 * 86400).

    This drives mean discharge for channel width/depth estimation. Requiring all
    365 climatological days prevents an undocumented change in seasonal weights.
    """
    if daily.shape[0] != 365:
        raise ValueError('Annual mean requires exactly 365 climatological days')
    total = np.zeros(daily.shape[1:], dtype='f4')
    for field in daily:
        total += field
    return total / np.float32(365*SECONDS_PER_DAY)


@contextmanager
def atomic_output(path, overwrite=False):
    """Stage one output next to its destination; never replace without explicit permission."""
    path = Path(path)
    if path.exists() and not overwrite:
        raise FileExistsError(f'{path} exists; use --overwrite explicitly')
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix='.'+path.name+'.', dir=path.parent)
    os.close(fd)
    try:
        yield Path(temporary)
        if path.exists() and not overwrite:
            raise FileExistsError(f'{path} appeared while writing')
        os.replace(temporary, path)
    finally:
        Path(temporary).unlink(missing_ok=True)


def metadata(args):
    return {'dataset': args.dataset, 'start_year': args.start_year, 'end_year': args.end_year,
            'source_pattern': args.input_pattern, 'source_variable': args.runoff_variable,
            'input_units_override': args.input_units, 'interval_hours_override': str(args.interval_hours),
            'leap_day_policy': 'exclude February 29; equal weight for 365 calendar days',
            'missing_policy': 'negative/masked/nonfinite invalid; valid years per day; all 365 days required for annual mean',
            'precision': 'float32 chronological sums and output',
            'scientific_limit': 'No independent validation of minimum-neighbor physical optimality; no actual coastline identified'}


def save_netcdf(path, grid, data, units, attrs, counts=None, overwrite=False):
    """Lossless NetCDF-4 float32 field(s), original coordinate values/order, fill=-999."""
    with atomic_output(path, overwrite) as tmp, Dataset(tmp, 'w', format='NETCDF4') as ds:
        ds.setncatts(attrs)
        for name, values, standard, unit in [(grid.lat_name, grid.latitude, 'latitude', 'degrees_north'),
                                              (grid.lon_name, grid.longitude, 'longitude', 'degrees_east')]:
            ds.createDimension(name, len(values))
            v = ds.createVariable(name, values.dtype, (name,))
            v[:] = values
            v.setncatts({'standard_name': standard, 'units': unit})
        dims = (grid.lat_name, grid.lon_name)
        if data.ndim == 3:
            ds.createDimension('time', 365)
            ds.createDimension('bounds', 2)
            t = ds.createVariable('time', 'f8', ('time',))
            t[:] = np.arange(365)+.5
            t.setncatts({'units': 'days since 2001-01-01 00:00:00', 'calendar': 'noleap', 'bounds': 'time_bounds',
                        'long_name': 'representative calendar day of the daily climatology'})
            ds.createVariable('time_bounds', 'f8', ('time', 'bounds'))[:] = np.column_stack((np.arange(365), np.arange(1,366)))
            dims = ('time', *dims)
        v = ds.createVariable('runoff', 'f4', dims, fill_value=MISSING, zlib=True, complevel=3, shuffle=True)
        v[:] = np.where(np.isfinite(data), data, MISSING).astype('f4')
        v.setncatts({'units': units, 'long_name': 'runoff climatology', 'missing_value': MISSING,
                    'cell_methods': 'time: mean over years' if data.ndim == 3 else 'time: mean'})
        if counts is not None:
            n = ds.createVariable('valid_year_count', 'u4', dims, zlib=True, complevel=3, shuffle=True)
            n[:] = counts
            n.long_name = 'valid source years contributing to each calendar day and cell'


def read_product(path):
    with Dataset(path) as ds:
        var = ds['runoff']
        return checked_grid(ds, var), np.ma.asarray(var[:], dtype='f4').filled(np.nan), {k:ds.getncattr(k) for k in ds.ncattrs()}


def product_paths(args):
    prefix = f'{args.output_prefix}'
    if not prefix or Path(prefix).name != prefix or prefix in ('.', '..'):
        raise ValueError('output-prefix must be a single name')
    root = Path(args.output_dir)
    stem = f'{prefix}_clm-{args.start_year}-{args.end_year}'
    return {key:root/(stem+suffix) for key,suffix in {
        'daily_before':'.daily_before.nc', 'mean_before':'.mean_before.nc',
        'daily_after':'.daily_coastmod.nc', 'mean_after':'.mean_coastmod.nc',
        'nc':'.nc', 'binary':'.one', 'comparison':'.comparison.json', 'difference':'.difference.nc'}.items()}


def require_new(paths, overwrite):
    for path in paths:
        if path.exists() and not overwrite:
            raise FileExistsError(f'{path} exists; select another prefix or use --overwrite')


def export(args):
    """Export the selected mm/s field with exactly identical float32 Binary/NetCDF values."""
    paths = product_paths(args)
    source = paths['mean_after'] if args.coast_modification == 'yes' else paths['mean_before']
    grid, mean_mm_s, attrs = read_product(source)
    if (attrs['start_year'], attrs['end_year'], attrs['dataset']) != (args.start_year, args.end_year, args.dataset):
        raise ValueError(f'{source}: period/dataset mismatch')
    outputs = [paths['nc'], paths['binary']]
    if args.compare_reference:
        outputs += [paths['comparison'], paths['difference']]
    require_new(outputs, args.overwrite)
    # Keep the uncorrected mean separately so the grid-only correction is independently auditable.
    save_netcdf(paths['nc'], grid, mean_mm_s, 'mm s-1', attrs, overwrite=args.overwrite)
    encoded = np.where(np.isfinite(mean_mm_s), mean_mm_s, MISSING).astype('<f4')
    with atomic_output(paths['binary'], args.overwrite) as tmp:
        encoded.tofile(tmp)  # (lat,lon) C order is x fastest, the Fortran-compatible single record.
    if args.compare_reference:
        reference = np.fromfile(args.compare_reference, dtype='<f4')
        if reference.size != encoded.size:
            raise ValueError('Reference Binary has wrong cell count')
        reference = reference.reshape(grid.shape)
        valid = np.isfinite(mean_mm_s) & np.isfinite(reference) & (reference >= 0)
        if not valid.any():
            raise ValueError('No jointly valid cells for comparison')
        difference = mean_mm_s.astype('f8')-reference.astype('f8')
        before_grid, before, _ = read_product(paths['mean_before'])
        if not same_grid(grid, before_grid):
            raise ValueError('Before/after coordinate mismatch')
        exact = (encoded == reference) & valid
        maximum = np.unravel_index(np.argmax(np.where(valid, abs(difference), -1)), grid.shape)
        counts = lambda a: {'zero_cells': int(np.sum(a == 0)), 'missing_cells': int(np.sum(~np.isfinite(a))),
                            'negative_cells': int(np.sum(a < 0))}
        positive_source = valid & np.isfinite(before) & (before > 0)
        positive_reference = valid & (reference > 0)
        band_statistics = []
        for south in range(-90, 90, 30):
            band = valid & (grid.latitude[:, None] >= south) & (grid.latitude[:, None] < south+30)
            if band.any():
                band_statistics.append({'south':south, 'north':south+30, 'cells':int(band.sum()),
                    'nonexact_cells':int(np.sum((~exact) & band)),
                    'max_abs_difference':float(np.max(abs(difference[band])))})
        report = {'grid_nx':grid.shape[1], 'grid_ny':grid.shape[0], 'dtype':'little-endian float32',
                  'binary_bytes':paths['binary'].stat().st_size, 'netcdf_bytes':paths['nc'].stat().st_size,
                  'units':'mm s-1', 'before':counts(before), 'after':counts(mean_mm_s),
                  'changed_mean_cells':int(np.sum(~np.isclose(before, mean_mm_s, rtol=0, atol=0, equal_nan=True))),
                  'filled_target_cells':int(attrs.get('filled_target_cells', 0)),
                  'reference_zero_became_positive_cells':int(np.sum((reference == 0) & (mean_mm_s > 0))),
                  'original_positive_max_abs_difference':float(np.max(abs(difference[positive_source]))) if positive_source.any() else None,
                  'reference_positive_max_abs_difference':float(np.max(abs(difference[positive_reference]))) if positive_reference.any() else None,
                  'latitude_band_statistics':band_statistics,
                  'jointly_valid_cells':int(valid.sum()), 'exact_equal_cells':int(exact.sum()),
                  'exact_equal_fraction':float(exact.sum()/valid.sum()),
                  'max_absolute_difference':float(np.max(abs(difference[valid]))),
                  'rmse':float(np.sqrt(np.mean(difference[valid]**2))), 'mean_difference':float(np.mean(difference[valid])),
                  'max_difference_location':{'latitude':float(grid.latitude[maximum[0]]), 'longitude':float(grid.longitude[maximum[1]])},
                  'reference_sha256':hashlib.sha256(Path(args.compare_reference).read_bytes()).hexdigest(),
                  'output_sha256':hashlib.sha256(paths['binary'].read_bytes()).hexdigest(),
                  'interpretation':('Grid-only target mask differs intentionally from old Input-Matrix-limited mask; '
                                    'provenance/precision/missing policy may also differ. '
                                    'Differences are not automatically implementation errors.')}
        save_netcdf(paths['difference'], grid, np.where(valid, difference, np.nan).astype('f4'), 'mm s-1',
                    {'operation':'generated minus historical reference; runoff variable stores a signed difference',
                     'reference':Path(args.compare_reference).name}, overwrite=args.overwrite)
        with atomic_output(paths['comparison'], args.overwrite) as tmp:
            tmp.write_text(json.dumps(report, indent=2)+'\n')
        print(json.dumps(report, indent=2), flush=True)
    print(f'[SUCCESS] Exported {paths["nc"]} and {paths["binary"]}', flush=True)


def generated_directory(value):
    path = Path(value).resolve()
    if not path.is_relative_to(OUTPUT.resolve()):
        raise argparse.ArgumentTypeError(f'Generated outputs must stay under {OUTPUT}')
    return path


def parser(include_stage=True):
    p = argparse.ArgumentParser(description=__doc__)
    if include_stage:
        p.add_argument('stage', choices=['calculate', 'export'])
    p.add_argument('--dataset', default='ELSE_GPCC')
    p.add_argument('--input-dir', type=Path, default=Path(__file__).resolve().parents[3]/'inp/ELSE_GPCC')
    p.add_argument('--input-pattern', default='runoffYYYY.nc')
    p.add_argument('--runoff-variable', default='runoff')
    p.add_argument('--start-year', type=int, default=1981)
    p.add_argument('--end-year', type=int, default=2010)
    p.add_argument('--input-units', default='auto')
    p.add_argument('--interval-hours', type=float)
    p.add_argument('--output-dir', type=generated_directory, default=OUTPUT)
    p.add_argument('--output-prefix', default='ELSE_GPCC')
    p.add_argument('--coast-modification', choices=['yes','no'], default='yes')
    p.add_argument('--compare-reference', type=Path)
    p.add_argument('--overwrite', action='store_true')
    return p


def calculate(args):
    if args.end_year < args.start_year:
        raise ValueError('end-year precedes start-year')
    paths = product_paths(args)
    require_new([paths['daily_before'], paths['mean_before']], args.overwrite)
    # A 365-day cycle preserves legacy seasonality without retaining the multi-year time series.
    grid, daily_mm_day, counts = climatology(args)
    # Width/depth estimation needs mean discharge, hence a mean depth rate, not the legacy annual sum.
    mean_mm_s = annual_mean(daily_mm_day)
    attrs = metadata(args)
    attrs['coastal_method'] = 'none; uncorrected reference'
    # Preserve both unmodified products to isolate the later coastal fill's effect.
    save_netcdf(paths['daily_before'], grid, daily_mm_day, 'mm day-1', attrs, counts, args.overwrite)
    save_netcdf(paths['mean_before'], grid, mean_mm_s, 'mm s-1', attrs, overwrite=args.overwrite)
    print(f'[SUCCESS] Saved {paths["daily_before"]} and {paths["mean_before"]}', flush=True)


if __name__ == '__main__':
    try:
        arguments = parser().parse_args()
        (calculate if arguments.stage == 'calculate' else export)(arguments)
    except (ValueError, OSError, KeyError) as error:
        print(f'[ERROR] {error}', file=sys.stderr)
        sys.exit(1)

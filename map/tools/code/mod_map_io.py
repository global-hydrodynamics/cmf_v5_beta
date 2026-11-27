# SPDX-License-Identifier: Apache-2.0
"""NetCDF-first map I/O shared by maintained Python map tools.

Arrays are (record, north-to-south row, west-to-east column), x fastest.
Direct-access records have no markers; map integers/reals are little-endian
int32/float32 unless the caller explicitly requests int16 high-resolution data.
Shell workflows invoke these Python tools directly; output products are replaced on rerun.
"""
from __future__ import annotations

import argparse
import csv
import sys
from dataclasses import dataclass
from pathlib import Path

import numpy as np

try:
    from .map_metadata import has_map_geometry, read_map_geometry
except ImportError:  # Direct execution from the map-local Shell workflows.
    from map_metadata import has_map_geometry, read_map_geometry

# Direct helper calls retain the old Binary behavior. Maintained CLIs set this
# explicitly through --map-format, whose production default is NetCDF.
_MAP_FORMAT = 'binary'
_MAP_ROOT = None
_REGISTRY = None


@dataclass(frozen=True)
class Grid:
    nx: int
    ny: int
    nlfp: int
    size: np.float32
    west: np.float32
    east: np.float32
    south: np.float32
    north: np.float32

    @classmethod
    def read(cls, path):
        """Read authoritative map geometry and initialize shared map I/O state."""
        grid = cls.from_file(path)
        global _MAP_ROOT
        target = Path(path).resolve()
        _MAP_ROOT = target if target.is_dir() else target.parent
        return grid

    @classmethod
    def from_file(cls, path):
        """Read map geometry without changing shared I/O state."""
        geometry = read_map_geometry(path)
        return cls(geometry.nx, geometry.ny, geometry.nlfp,
                   *(np.float32(value) for value in geometry.values()[3:]))

    def raster(self, path, dtype='<f4', records=1):
        """Map complete records without loading another full-array copy."""
        path = _input_path(Path(path))
        if path.suffix == '.nc':
            return _read_netcdf(path, self, dtype, records)
        shape = (records, self.ny, self.nx)
        if Path(path).stat().st_size < int(np.prod(shape)) * np.dtype(dtype).itemsize:
            raise ValueError(f'{path}: incomplete {shape} {dtype} map')
        result = np.memmap(path, dtype=dtype, mode='r', shape=shape)
        return result[0] if records == 1 else result


def write_raster(path, values, dtype, grid=None):
    """Write a map product in the selected format, replacing only its output."""
    path = Path(path)
    if _MAP_FORMAT == 'netcdf' and path.suffix in {'.bin', '.nc'}:
        if path.suffix == '.bin':
            path = _netcdf_path(path)
        if grid is None:
            grid = _output_grid(path)
        _write_netcdf(path, np.asarray(values), dtype, grid=grid)
        return
    if _MAP_FORMAT == 'binary' and _MAP_ROOT is not None and path.suffix == '.bin':
        path = _binary_path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('wb') as stream:
        np.asarray(values, dtype=dtype).tofile(stream)


def parser(description, map_default='..', *, map_binary_flag=False):
    """Keep positional Fortran arguments, with explicit parallel-tool I/O roots."""
    class MapArgumentParser(argparse.ArgumentParser):
        def parse_args(self, args=None, namespace=None):
            parsed = super().parse_args(args, namespace)
            global _MAP_FORMAT, _MAP_ROOT
            parsed.map_format = 'binary' if getattr(parsed, 'map_binary', False) else getattr(parsed, 'map_format', 'netcdf')
            _MAP_FORMAT = parsed.map_format
            _MAP_ROOT = parsed.map_dir.resolve()
            return parsed

    result = MapArgumentParser(description=description)
    result.add_argument('--map-dir', type=Path, default=Path(map_default), help='Read-only input map root; default follows Fortran CWD contract')
    result.add_argument('--output-dir', type=Path, help='Explicit output destination; default follows the Fortran CWD convention; existing outputs are replaced')
    if map_binary_flag:
        result.add_argument('--map-binary', action='store_true', help='Use legacy Binary map input/output instead of the default NetCDF maps.')
    else:
        result.add_argument('--map-format', choices=('netcdf', 'binary'), default='netcdf', help='Map input/output format (default: netcdf; binary is the legacy-compatible mode)')
    return result


def output_root(args):
    """Return the selected output directory without modifying the source map."""
    root = args.output_dir if args.output_dir is not None else args.map_dir
    return root / 'binary' if args.map_format == 'binary' and args.output_dir is None else root


def _input_path(path):
    if path.suffix != '.bin':
        return path
    if _MAP_FORMAT == 'binary':
        return _binary_path(path)
    netcdf = _netcdf_path(path)
    if netcdf.is_file():
        return netcdf
    # Explicit input paths outside the selected map root, such as runoff files,
    # remain literal rather than being silently redirected.
    if _MAP_ROOT is None:
        return path
    if _relative_map_path(path).is_absolute():
        if has_map_geometry(path.parent) or (path.parent / 'location.csv').is_file() or (path.parent / 'location.txt').is_file():
            raise FileNotFoundError(f'NetCDF map input not found: {netcdf}; use --map-format binary for legacy Binary maps')
        return path
    raise FileNotFoundError(f'NetCDF map input not found: {netcdf}; use --map-format binary for legacy Binary maps')


def _relative_map_path(path):
    if _MAP_ROOT is None:
        return path
    resolved = path.resolve()
    try:
        return resolved.relative_to(_MAP_ROOT)
    except ValueError:
        # A caller may provide a relative source outside --map-dir (for
        # example, a regional map cropped from ../../glb_15min). Keep that
        # path anchored to the working directory instead of re-rooting it
        # beneath --map-dir.
        return resolved


def _netcdf_path(path):
    relative = _relative_map_path(path)
    parts = list(relative.parts)
    if parts and parts[0] == 'binary':
        parts = parts[1:]
    return (_MAP_ROOT.joinpath(*parts).with_suffix('.nc') if _MAP_ROOT is not None else path.with_suffix('.nc'))


def _binary_path(path):
    relative = _relative_map_path(path)
    parts = list(relative.parts)
    if parts and parts[0] == 'binary':
        return path
    if _MAP_ROOT is not None and not relative.is_absolute():
        return _MAP_ROOT.joinpath('binary', *parts)
    if path.is_absolute() and ((path.parent / 'location.txt').is_file() or (path.parent / 'location.csv').is_file()):
        return path.parent.parent / 'binary' / path.parent.name / path.name
    if path.is_absolute() and has_map_geometry(path.parent):
        return path.parent / 'binary' / path.name
    if (path.parent / 'location.txt').is_file() or (path.parent / 'location.csv').is_file():
        candidate = path.parent.parent / 'binary' / path.parent.name / path.name
        if candidate.is_file():
            return candidate
    if has_map_geometry(path.parent):
        candidate = path.parent / 'binary' / path.name
        if candidate.is_file():
            return candidate
    return path


def _variable_rows(stem, highres=False):
    global _REGISTRY
    if _REGISTRY is None:
        registry = Path(__file__).resolve().parents[3] / 'variable_table/map_variables.csv'
        with registry.open(newline='', encoding='utf-8-sig') as stream:
            _REGISTRY = list(csv.DictReader(stream))
    base = _registry_stem(stem.rsplit('.', 1)[-1])
    normalized = f'{base}.nc'
    if base.startswith('mpireg-'):
        normalized = 'mpireg.nc'
    rows = []
    for row in _REGISTRY:
        filenames = [item.strip() for item in row.get('filename', '').split(';')]
        is_highres = any('<HIRES>' in item or '<AREA>' in item for item in filenames)
        if is_highres != highres:
            continue
        if any(item.rsplit('/', 1)[-1].endswith(normalized) for item in filenames):
            rows.append(row)
    if not rows:
        return [{'name': stem, 'record_index': '1'}]
    rows.sort(key=lambda row: int(row.get('record_index') or 1))
    return rows


def _registry_stem(stem):
    """Resolve aliases and suffixed output names to a registered map variable."""
    if stem == 'bifbsn_mpi':
        return 'bifbsn'
    for row in _REGISTRY or []:
        for filename in row.get('filename', '').split(';'):
            filename = filename.strip()
            if not filename.endswith('.nc'):
                continue
            candidate = Path(filename).name[:-3]
            if stem == candidate or stem.startswith(f'{candidate}-'):
                return candidate
    return stem


def _variable_definitions(stem, highres=False):
    return [(row['name'], int(row.get('record_index') or 1))
            for row in _variable_rows(stem, highres=highres)]


def _netcdf_module():
    try:
        from netCDF4 import Dataset
    except ImportError as error:
        raise RuntimeError('NetCDF map tools require netCDF4; install it in the map-processing environment') from error
    return Dataset


def _read_netcdf(path, grid, dtype, records):
    return _read_netcdf_shape(path, dtype, records, grid.ny, grid.nx)


def input_path(path):
    """Resolve a logical legacy .bin name to the selected standard representation."""
    return _input_path(Path(path))


def read_array(path, dtype, shape, records=None):
    """Read an explicitly shaped map or high-resolution raster in the selected format."""
    path = _input_path(Path(path))
    if records is None:
        records = shape[0] if len(shape) == 3 else 1
    if path.suffix == '.nc':
        ny, nx = shape[-2:]
        return _read_netcdf_shape(path, dtype, records, ny, nx)
    full_shape = (records, *shape[-2:])
    data = np.memmap(path, dtype=dtype, mode='r', shape=full_shape)
    return data[0] if records == 1 else data


class RasterTile:
    """Read a map tile in contiguous row windows without loading it in full."""

    def __init__(self, path, dtype, records, shape, optional=False):
        logical_path = Path(path)
        self.dataset = None
        self.values = None
        self.records = records
        try:
            self.path = _input_path(logical_path)
        except FileNotFoundError:
            if optional:
                self.path = None
                return
            raise
        if not self.path.is_file():
            if optional:
                self.path = None
                return
            raise FileNotFoundError(self.path)
        if self.path.suffix == '.nc':
            Dataset = _netcdf_module()
            self.dataset = Dataset(self.path)
            self.variables = []
            highres = ((self.path.parent / 'location.csv').is_file() if _MAP_FORMAT == 'netcdf'
                       else (self.path.parent / 'location.txt').is_file())
            for name, _ in _variable_definitions(self.path.stem, highres=highres):
                if name in self.dataset.variables:
                    variable = self.dataset.variables[name]
                    variable.set_auto_maskandscale(False)
                    self.variables.append(variable)
            self.layered = (len(self.variables) == 1 and self.variables[0].ndim == 3
                            and self.variables[0].shape[0] == records)
            if not self.layered and len(self.variables) != records:
                self.close()
                raise ValueError(f'{self.path}: expected {records} registered variable(s)')
        else:
            ny, nx = shape
            expected = records * ny * nx * np.dtype(dtype).itemsize
            if self.path.stat().st_size != expected:
                raise ValueError(f'{self.path}: expected {expected} bytes, found {self.path.stat().st_size}')
            self.values = np.memmap(self.path, dtype=dtype, mode='r', shape=(records, ny, nx))

    def read(self, row_start, row_stop, col_start, col_stop, dtype):
        if self.path is None:
            return None
        if self.dataset is None:
            return np.asarray(self.values[:, row_start:row_stop, col_start:col_stop])
        if self.layered:
            return np.asarray(self.variables[0][:, row_start:row_stop, col_start:col_stop], dtype=dtype)
        return np.stack([np.asarray(variable[row_start:row_stop, col_start:col_stop], dtype=dtype)
                         for variable in self.variables])

    def close(self):
        if self.dataset is not None:
            self.dataset.close()
            self.dataset = None


def read_inpmat(path, nx, ny, slots):
    """Read the dedicated sparse input-matrix NetCDF variables or legacy records."""
    path = _input_path(Path(path))
    if path.suffix == '.nc':
        Dataset = _netcdf_module()
        with Dataset(path) as dataset:
            result = []
            for name in ('inpx', 'inpy', 'inpa'):
                variable = dataset.variables[name]
                variable.set_auto_maskandscale(False)
                result.append(np.asarray(variable[:]))
            result = tuple(result)
        if any(value.shape != (slots, ny, nx) for value in result):
            raise ValueError(f'{path}: INPMAT arrays do not match DIMINFO dimensions')
        return result
    raw = np.memmap(path, mode='r', dtype='<i4', shape=(3, slots, ny, nx))
    return raw[0], raw[1], raw[2].view('<f4')


def write_inpmat(path, inpx, inpy, inpa, metadata):
    """Write the dedicated NetCDF INPMAT schema without changing sparse order."""
    Dataset = _netcdf_module()
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    nx, ny, slots = int(metadata['nx']), int(metadata['ny']), int(metadata['inpn'])
    temporary = path.with_name(path.name + '.tmp')
    try:
        with Dataset(temporary, 'w', format='NETCDF4') as dataset:
            dataset.createDimension('inpn', slots)
            dataset.createDimension('lat', ny)
            dataset.createDimension('lon', nx)
            for name, values, dtype in (('inpx', inpx, 'i4'), ('inpy', inpy, 'i4'), ('inpa', inpa, 'f4')):
                var = dataset.createVariable(name, dtype, ('inpn', 'lat', 'lon'), zlib=True)
                var[:] = values
            for key, value in metadata.items():
                dataset.setncattr(key.upper(), value)
            dataset.setncattr('Conventions', 'CF-1.8')
        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)


def _read_netcdf_shape(path, dtype, records, ny, nx):
    Dataset = _netcdf_module()
    highres = (Path(path).parent / 'location.csv').is_file()
    names = _variable_definitions(_registry_stem(Path(path).stem), highres=highres)
    target_dtype = np.dtype(dtype)
    with Dataset(path) as dataset:
        variables = []
        for name, _ in names:
            if name not in dataset.variables:
                continue
            variable = dataset.variables[name]
            variable.set_auto_maskandscale(False)
            data = np.asarray(variable[:])
            if data.ndim == 3:
                data = np.moveaxis(data, 0, 0)
            variables.append(np.asarray(data, dtype=target_dtype))
        if not variables:
            # A few legacy NetCDF products use record names not present in the
            # registry; accept the filename stem as their variable name.
            variable = dataset.variables[path.stem]
            variable.set_auto_maskandscale(False)
            variables = [np.asarray(np.ma.filled(variable[:], getattr(variable, '_FillValue', 0)), dtype=target_dtype)]
    if records == 1:
        result = variables[0]
        return result[0] if result.ndim == 3 and result.shape[0] == 1 else result
    result = (variables[0] if len(variables) == 1 and variables[0].ndim == 3
              else np.stack(variables, axis=0))
    if result.shape[-2:] != (ny, nx):
        raise ValueError(f'{path}: NetCDF raster shape {result.shape[-2:]} does not match expected {(ny, nx)}')
    if result.shape[0] != records:
        raise ValueError(f'{path}: expected {records} record(s), found {result.shape[0]}')
    return result


def _write_netcdf(path, values, dtype, grid):
    Dataset = _netcdf_module()
    values = np.asarray(values, dtype=dtype)
    raw_stem = path.stem.rsplit('.', 1)[-1]
    rows = _variable_rows(raw_stem)
    stem = _registry_stem(raw_stem)
    layered = values.ndim == 3 and len(rows) == 1 and values.shape[0] > 1
    records = values if values.ndim == 3 else values[None, ...]
    if records.shape[-2:] != (grid.ny, grid.nx):
        raise ValueError(f'{path}: output shape {records.shape[-2:]} differs from map geometry {(grid.ny, grid.nx)}')
    names = rows[:1] if layered else rows
    if len(names) < records.shape[0]:
        names.extend({'name': f'{stem}_{index+1}', 'record_index': str(index+1)}
                     for index in range(len(names), records.shape[0]))
    names = names[:1] if layered else names[:records.shape[0]]
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + '.tmp')
    try:
        with Dataset(temporary, 'w', format='NETCDF4') as dataset:
            dataset.createDimension('lat', grid.ny)
            dataset.createDimension('lon', grid.nx)
            if layered:
                dataset.createDimension('layer', records.shape[0])
            lon = dataset.createVariable('lon', 'f8', ('lon',))
            lat = dataset.createVariable('lat', 'f8', ('lat',))
            lon[:] = float(grid.west) + (np.arange(grid.nx) + .5) * float(grid.size)
            lat[:] = float(grid.north) - (np.arange(grid.ny) + .5) * float(grid.size)
            for index, row in enumerate(names):
                name = row['name']
                array = records if layered else records[index]
                dimensions = ('layer', 'lat', 'lon') if layered else ('lat', 'lon')
                raw_fill = (row.get('missing_value') or '').strip()
                fill = np.asarray(raw_fill, dtype=dtype).item() if raw_fill else None
                variable = dataset.createVariable(name, 'i4' if np.dtype(dtype).kind in 'iu' else 'f4', dimensions, zlib=True, fill_value=fill)
                for attribute in ('long_name', 'units', 'special_values'):
                    value = (row.get(attribute) or '').strip()
                    if value:
                        variable.setncattr(attribute, value)
                if raw_fill:
                    variable.setncattr('missing_value', fill)
                variable[:] = array
            dataset.setncattr('Conventions', 'CF-1.8')
        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)


def write_highres_raster(path, values, dtype, bounds, chunk_rows=64):
    """Write one tile as registry-named NetCDF variables in bounded row blocks."""
    path = Path(path)
    values = values if values.ndim == 3 else values[None, ...]
    ny, nx = values.shape[-2:]
    if _MAP_FORMAT == 'binary':
        path = _binary_path(path.with_suffix('.bin'))
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open('wb') as stream:
            values.tofile(stream)
        return path
    path = path.with_suffix('.nc')
    Dataset = _netcdf_module()
    rows = _variable_rows(path.stem, highres=True)
    if len(rows) < values.shape[0]:
        raise ValueError(f'{path}: registry defines fewer records than the tile contains')
    west, east, south, north = bounds
    temporary = path.with_name(path.name + '.tmp')
    try:
        with Dataset(temporary, 'w', format='NETCDF4') as dataset:
            dataset.createDimension('lat', ny)
            dataset.createDimension('lon', nx)
            lon = dataset.createVariable('lon', 'f8', ('lon',))
            lat = dataset.createVariable('lat', 'f8', ('lat',))
            lon[:] = west + (np.arange(nx) + .5) * ((east - west) / nx)
            lat[:] = north - (np.arange(ny) + .5) * ((north - south) / ny)
            variables = []
            for index, row in enumerate(rows[:values.shape[0]]):
                name = row['name']
                raw_fill = (row.get('missing_value') or '').strip()
                fill = np.asarray(raw_fill, dtype=dtype).item() if raw_fill else None
                variable = dataset.createVariable(name, np.dtype(dtype), ('lat', 'lon'),
                                                  zlib=True, fill_value=fill)
                for attribute in ('long_name', 'units', 'special_values'):
                    value = (row.get(attribute) or '').strip()
                    if value:
                        variable.setncattr(attribute, value)
                if raw_fill:
                    variable.setncattr('missing_value', fill)
                variables.append(variable)
            for start in range(0, ny, chunk_rows):
                stop = min(ny, start + chunk_rows)
                for index, variable in enumerate(variables):
                    variable[start:stop, :] = values[index, start:stop, :]
            dataset.setncattr('Conventions', 'CF-1.8')
        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)
    return path


def _output_grid(path):
    if has_map_geometry(path.parent):
        return Grid.from_file(path.parent)
    raise FileNotFoundError(f'{path}: NetCDF output grid requires params.nml or params.txt beside the output, or an explicit grid argument to write_raster')

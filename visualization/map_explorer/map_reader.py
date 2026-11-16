"""Read coarse CaMa-Flood maps without preprocessing or modifying source data."""
from __future__ import annotations

from collections import OrderedDict
from dataclasses import dataclass
from functools import cached_property
from pathlib import Path

import numpy as np
from netCDF4 import Dataset


@dataclass(frozen=True)
class Geometry:
    nx: int
    ny: int
    layers: int
    resolution: float
    west: float
    east: float
    south: float
    north: float

    @classmethod
    def read(cls, path):
        try:
            values = [float(line.split()[0]) for line in Path(path).read_text().splitlines()
                      if line.strip() and not line.lstrip().startswith(('#', '!'))]
        except (OSError, ValueError) as exc:
            raise ValueError(f'{path}: cannot parse params.txt: {exc}') from exc
        if len(values) != 8 or not np.isfinite(values).all():
            raise ValueError(f'{path}: expected eight finite numeric parameter lines')
        if any(v < 1 or v != int(v) for v in values[:3]):
            raise ValueError(f'{path}: NX, NY and NLFP must be positive integers')
        g = cls(*(int(v) for v in values[:3]), *values[3:])
        # Parameter writers print rounded decimal degrees. Permit only tiny
        # edge-rounding error, not a whole missing/extra cell.
        tol = max(1e-5, g.resolution * 1e-4)
        if (g.resolution <= 0 or g.west >= g.east or g.south >= g.north
                or g.south < -90 or g.north > 90 or g.east - g.west > 360 + tol
                or abs(g.east-g.west-g.nx*g.resolution) > tol
                or abs(g.north-g.south-g.ny*g.resolution) > tol):
            raise ValueError(f'{path}: bounds, dimensions and spacing disagree')
        return g

    @cached_property
    def lon(self):
        return self.west + (np.arange(self.nx) + .5) * self.resolution

    @cached_property
    def lat(self):
        return self.north - (np.arange(self.ny) + .5) * self.resolution

    @property
    def extent(self):
        return self.west, self.east, self.south, self.north

    @property
    def periodic(self):
        return abs(self.east-self.west-360) < 1e-5

    def cell(self, lon, lat):
        """Return zero-based row/column; outer east/south edges are outside."""
        if not (self.west <= lon < self.east and self.south < lat <= self.north):
            return None
        return (min(self.ny-1, int((self.north-lat)/self.resolution)),
                min(self.nx-1, int((lon-self.west)/self.resolution)))

    def validate_extent(self, extent):
        w, e, s, n = extent
        if not np.isfinite(extent).all() or not (self.west <= w < e <= self.east and self.south <= s < n <= self.north):
            raise ValueError('Extent must be finite, ordered, and within map bounds')


@dataclass(frozen=True)
class Variable:
    title: str
    units: str
    dtype: str = '<f4'
    factor: float = 1
    display_units: str = 'm'
    categorical: bool = False
    logarithmic: bool = False


# A deliberately small format contract, verified against map_variables.csv.
# Size validates this contract; it never determines the dtype or record layout.
SCHEMA = {
    'uparea': Variable('Upstream drainage area', 'm2', factor=1e-6, display_units='km²', logarithmic=True),
    'basin': Variable('Basin ID', '1', '<i4', display_units='ID', categorical=True),
    'bsncol': Variable('Basin display color (not basin ID)', '1', '<i4', display_units='category', categorical=True),
    'subcol': Variable('Subbasin display color (not subbasin ID)', '1', '<i4', display_units='category', categorical=True),
    'elevtn': Variable('Channel-top elevation (EGM96)', 'm'),
    'ctmare': Variable('Unit-catchment area', 'm2', factor=1e-6, display_units='km²'),
    'rivlen': Variable('River-channel length', 'm'),
    'rivwth': Variable('River-channel width', 'm'),
    'rivhgt': Variable('River-channel depth parameter', 'm'),
    'nxtdst': Variable('Distance to downstream catchment', 'm'),
    'grdare': Variable('Grid-cell area', 'm2', factor=1e-6, display_units='km²'),
    'rivman': Variable('Manning roughness (source units unspecified)', '', display_units='unspecified'),
}


@dataclass(frozen=True)
class Source:
    path: Path
    netcdf: bool
    names: tuple[str, ...]


def canonical_units(value):
    return str(value).strip().replace('²', '2').replace('**', '').replace('^', '').replace(' ', '')


class MapReader:
    """Discover readable products by metadata; load only requested fields.

    Arrays use (row,column), north-to-south / west-to-east. Returned masked
    values preserve legitimate zero/negative values, including below-sea elevation.
    """
    def __init__(self, map_dir, cache_size=4):
        self.path = Path(map_dir).expanduser().resolve()
        self.geometry = Geometry.read(self.path / 'params.txt')
        self.sources = {}
        self.network_sources = {}
        self.messages = []
        self._cache = OrderedDict()
        self.cache_size = cache_size
        for key, spec in SCHEMA.items():
            source = self._discover(key, (key,), spec.dtype, spec.units)
            if source is None and key=='subcol':
                source=self._discover('subcol-sample',('subcol',),spec.dtype,spec.units)
            if source:
                self.sources[key] = source
        for key in ('nextxy', 'nextxy_noedge'):
            source = self._discover(key, ('nextx', 'nexty'), '<i4', '1')
            if source:
                self.network_sources[key] = source
        known = set(SCHEMA) | {'nextxy', 'nextxy_noedge','subcol-sample','lonlat'}
        unknown = sorted(p.name for p in self.path.glob('*.bin') if p.stem not in known)
        if unknown:
            self.messages.append('Unsupported Binary products skipped (no dtype guessing): ' + ', '.join(unknown))

    def _discover(self, key, names, dtype, units):
        for path in (self.path/'netcdf'/f'{key}.nc', self.path/f'{key}.nc', self.path/f'{key}.bin'):
            if not path.is_file():
                continue
            source = Source(path, path.suffix == '.nc', names)
            try:
                if source.netcdf:
                    with Dataset(path, 'r') as ds:
                        self._nc_layout(ds)
                        for name in names:
                            var = ds.variables[name]
                            self._nc_variable(ds, var, dtype, units)
                elif path.stat().st_size != self.geometry.nx*self.geometry.ny*len(names)*4:
                    raise ValueError('incorrect Binary size for declared dtype/record count')
            except (OSError, ValueError, KeyError, IndexError) as exc:
                self.messages.append(f'Skipped {path.name}: {exc}')
                continue
            return source
        return None

    def _nc_layout(self, ds):
        g = self.geometry
        axes = []
        for key, expected in [('lon', g.lon), ('lat', g.lat)]:
            var = ds.variables[key]
            units = getattr(var, 'units', 'degrees_east' if key == 'lon' else 'degrees_north')
            if units not in (('degrees_east', 'degree_east', 'degrees_E') if key == 'lon' else ('degrees_north', 'degree_north', 'degrees_N')):
                raise ValueError(f'{key}: coordinates must be geographic degrees')
            if var.ndim != 1 or len(var) != len(expected):
                raise ValueError(f'{key}: wrong coordinate dimension')
            raw = np.ma.asarray(var[:])
            if np.ma.getmaskarray(raw).any():
                raise ValueError(f'{key}: masked coordinate')
            coords = np.asarray(raw, dtype=float)
            tol = max(1e-5, g.resolution*1e-4)
            if np.allclose(coords, expected, rtol=0, atol=tol):
                reverse = False
            elif np.allclose(coords[::-1], expected, rtol=0, atol=tol):
                reverse = True
            else:
                raise ValueError(f'{key}: cell centers disagree with params.txt')
            axes.append((var.dimensions[0], reverse))
        if axes[0][0] == axes[1][0]:
            raise ValueError('lon and lat must have separate dimensions')
        return axes

    def _nc_variable(self, ds, var, dtype, units):
        axes = self._nc_layout(ds)
        dims = [axis[0] for axis in axes]
        if var.ndim != 2 or set(var.dimensions) != set(dims):
            raise ValueError(f'{var.name}: expected exactly the lon and lat dimensions')
        expected = np.dtype(dtype)
        if var.dtype.kind != expected.kind or var.dtype.itemsize != 4:
            raise ValueError(f'{var.name}: expected {expected}, found {var.dtype}')
        if any(hasattr(var, key) for key in ('scale_factor', 'add_offset')):
            raise ValueError(f'{var.name}: packed/scaled maps are unsupported')
        # CaMa-Flood's converter leaves nextxy units absent. Indices remain
        # dimensionless by the explicit file contract, never by size inference.
        actual = getattr(var, 'units', '1' if var.name in ('nextx', 'nexty') else '')
        if canonical_units(actual) != canonical_units(units):
            raise ValueError(f'{var.name}: expected units {units!r}, found {actual!r}')
        return axes

    def _load(self, source, name, record):
        g = self.geometry
        if source.netcdf:
            with Dataset(source.path, 'r') as ds:
                axes = self._nc_layout(ds)
                var = ds.variables[name]
                raw = np.ma.asarray(var[:])
                # Normalize axes before flipping. Square grids must not hide
                # a transpose: dimensions, not shape, identify the spatial axes.
                if var.dimensions == (axes[0][0], axes[1][0]):
                    raw = raw.T
                if axes[1][1]:
                    raw = raw[::-1, :]
                if axes[0][1]:
                    raw = raw[:, ::-1]
                raw = raw.copy()
        else:
            dtype = SCHEMA[name].dtype if name in SCHEMA else '<i4'
            raw = np.memmap(source.path, dtype=dtype, mode='r',
                            shape=(len(source.names), g.ny, g.nx))[record]
        # Attribute fills and contract sentinel both matter: some legacy files
        # declare 1e20 yet actually contain -9999. No universal <=0 masking.
        mask = np.ma.getmaskarray(raw) | ~np.isfinite(raw) | (np.asarray(raw) == -9999)
        result = np.ma.array(raw, mask=mask, copy=False)
        result.data.flags.writeable = False
        return result

    def read(self, name):
        if name not in self.sources:
            raise ValueError(f'No supported readable raster: {name}')
        if name not in self._cache:
            self._cache[name] = self._load(self.sources[name], name, 0)
            while len(self._cache) > self.cache_size:
                self._cache.popitem(last=False)
        self._cache.move_to_end(name)
        return self._cache[name]

    def read_network(self, name='nextxy'):
        source = self.network_sources[name]
        return tuple(self._load(source, field, i) for i, field in enumerate(source.names))

    def read_cell(self, name, row, col):
        """Inspect uncached attributes by scalar I/O rather than loading each map."""
        if name in self._cache:
            return self._cache[name][row, col]
        source = self.sources[name]
        if source.netcdf:
            with Dataset(source.path, 'r') as ds:
                axes = self._nc_layout(ds)
                x = self.geometry.nx-1-col if axes[0][1] else col
                y = self.geometry.ny-1-row if axes[1][1] else row
                var = ds.variables[name]
                value = var[x, y] if var.dimensions == (axes[0][0], axes[1][0]) else var[y, x]
        else:
            with source.path.open('rb') as stream:
                stream.seek((row*self.geometry.nx+col)*4)
                value = np.frombuffer(stream.read(4), dtype=SCHEMA[name].dtype)[0]
        if np.ma.is_masked(value) or not np.isfinite(value) or value == -9999:
            return np.ma.masked
        return value

    def inspect(self, lon, lat, network='nextxy'):
        cell = self.geometry.cell(lon, lat)
        if cell is None:
            raise ValueError('Click is outside the map')
        row, col = cell
        result = {'ix (1-based)': col+1, 'iy (1-based)': row+1,
                  'longitude': float(self.geometry.lon[col]), 'latitude': float(self.geometry.lat[row])}
        for name, spec in SCHEMA.items():
            if name in self.sources:
                value = self.read_cell(name, row, col)
                result[f'{name} [{spec.units}]'] = None if np.ma.is_masked(value) else value.item()
        # Network is supplied by the controller, which caches it separately;
        # this method deliberately only inspects scalar attributes.
        return result

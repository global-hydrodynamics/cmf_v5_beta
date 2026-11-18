"""Read-only native COG windows and explicit display overviews.

No overview category is ever used for a scientific click. Cache values, not colors;
all geographic windows and output sampling are part of the bounded cache identity.
"""
from collections import OrderedDict
from dataclasses import dataclass
from pathlib import Path
import math

import numpy as np

try:
    import rasterio
    from rasterio.enums import Resampling
    from rasterio.windows import Window, from_bounds
except ImportError:
    rasterio = None

from map_reader import canonical_units


class RasterCache:
    def __init__(self, max_bytes=64 * 1024**2):
        self.max_bytes, self.bytes = max_bytes, 0
        self.values = OrderedDict()
        self.hits = self.misses = 0

    def get(self, key):
        if key not in self.values:
            self.misses += 1
            return None
        self.hits += 1
        self.values.move_to_end(key)
        return self.values[key]

    def put(self, key, value):
        value.flags.writeable = False
        if value.nbytes > self.max_bytes:
            return value
        if key in self.values:
            self.bytes -= self.values.pop(key).nbytes
        self.values[key] = value
        self.bytes += value.nbytes
        while self.bytes > self.max_bytes:
            self.bytes -= self.values.popitem(last=False)[1].nbytes
        return value

    def clear(self):
        self.values.clear()
        self.bytes = 0


def signature(path):
    stat = Path(path).stat()
    return str(Path(path).resolve()), stat.st_size, stat.st_mtime_ns, stat.st_ino


@dataclass(frozen=True)
class Sampling:
    edges: tuple
    native_window: tuple  # row start/stop, column start/stop
    shape: tuple
    factor: int
    native: bool
    pixel_screen: tuple


def sampling(geometry, extent, screen, factors):
    g = geometry
    w, e, s, n = extent
    c0, c1 = max(0, math.floor((w-g.west)/g.resolution+1e-8)), min(g.nx, math.ceil((e-g.west)/g.resolution-1e-8))
    r0, r1 = max(0, math.floor((g.north-n)/g.resolution+1e-8)), min(g.ny, math.ceil((g.north-s)/g.resolution-1e-8))
    if c1 <= c0 or r1 <= r0:
        return None
    # Actual Bokeh frame already fits longitude*cos(mid-latitude)/latitude aspect.
    # These two independent screen scales include that allocation and clipping.
    px = g.resolution * screen[0] / (e-w)
    py = g.resolution * screen[1] / (n-s)
    h, width = r1-r0, c1-c0
    native = px >= 1-1e-8 and py >= 1-1e-8
    shape = (h if native else max(1, min(h, math.ceil(h*py))),
             width if native else max(1, min(width, math.ceil(width*px))))
    if shape[0]*shape[1] > 2_000_000:
        reduction = math.sqrt(2_000_000/(shape[0]*shape[1]))
        shape = (max(1,int(shape[0]*reduction)),max(1,int(shape[1]*reduction)))
    native = native and shape == (h,width)
    ratio = min(width/shape[1], h/shape[0])
    factor = min((1, *factors), key=lambda f: abs(math.log(f/max(1,ratio))))
    if native:
        factor = 1
    edges = (g.west+c0*g.resolution, g.west+c1*g.resolution,
             g.north-r1*g.resolution, g.north-r0*g.resolution)
    return Sampling(edges, (r0,r1,c0,c1), shape, factor, native and factor == 1, (px,py))


class COGSource:
    @classmethod
    def open(cls, path, name, geometry, cache=None, netcdf_path=None):
        if rasterio is None:
            raise ValueError('Rasterio is required for COG; install Explorer requirements')
        self = cls()
        self.path, self.name, self.geometry = Path(path), name, geometry
        self.cache = cache if cache is not None else RasterCache()
        self.netcdf_path = Path(netcdf_path) if netcdf_path else None
        with rasterio.open(path) as ds:
            g = geometry
            if ds.crs is None or ds.crs.to_epsg() != 4326 or ds.tags(ns='IMAGE_STRUCTURE').get('LAYOUT') != 'COG':
                raise ValueError('expected numeric EPSG:4326 COG')
            t = ds.transform
            tolerance = max(1e-5, g.resolution*1e-4)
            if (ds.width != g.nx or ds.height != g.ny or t.b != 0 or t.d != 0 or t.a <= 0 or t.e >= 0
                    or abs(t.c-g.west) > tolerance or abs(t.f-g.north) > tolerance
                    or abs(t.a-g.resolution) > tolerance/g.nx or abs(t.e+g.resolution) > tolerance/g.ny):
                raise ValueError('COG dimensions/edges/spacing disagree with location.txt')
            if self.netcdf_path and ds.tags().get('source_file') != self.netcdf_path.name:
                raise ValueError('COG provenance source_file disagrees with selected tile/product')
            names = [ds.tags(i).get('source_variable', '') for i in range(1,ds.count+1)]
            expected = ('catmxx','catmyy') if name == 'catmxy' else (name,)
            if name == 'catmxy' and names == ['catmx','catmy']:
                expected = ('catmx','catmy')
            if tuple(names) != expected:
                raise ValueError(f'COG band mapping must be {expected}; found {names}')
            dtype = np.dtype('int16' if name == 'catmxy' else 'int8' if name in ('visual','catmz100') else 'float32')
            if any(np.dtype(d) != dtype for d in ds.dtypes):
                raise ValueError(f'COG expected native {dtype}, found {ds.dtypes}')
            self.factor = 1.0
            for index in range(1,ds.count+1):
                units = canonical_units(ds.tags(index).get('units', ds.units[index-1] or ''))
                wanted = '1' if dtype.kind == 'i' else 'km2' if name == 'uparea' else 'm'
                if name == 'uparea' and units == 'm2':
                    self.factor = 1e-6
                elif units != wanted and not (name == 'visual' and units == 'code'):
                    raise ValueError(f'COG {name}: units {units!r} incompatible with {wanted}')
            self.count, self.dtype = ds.count, dtype
            self.overviews = tuple(ds.overviews(1))
            if any(tuple(ds.overviews(i)) != self.overviews for i in range(1,ds.count+1)):
                raise ValueError('COG bands have inconsistent overview levels')
            self.nodata = ds.nodatavals
        self._identity = (signature(self.path), signature(self.netcdf_path) if self.netcdf_path and self.netcdf_path.is_file() else None)
        self.io_reads = 0
        return self

    @property
    def identity(self):
        current = (signature(self.path), signature(self.netcdf_path) if self.netcdf_path and self.netcdf_path.is_file() else None)
        if current != self._identity:
            fresh = type(self).open(self.path,self.name,self.geometry,self.cache,self.netcdf_path)
            self.__dict__.update(fresh.__dict__)
        return current

    def _read(self, window, shape, factor, cache_limit=None):
        identity = self.identity
        key = (identity,self.name,tuple(window),tuple(shape),factor)
        cached = self.cache.get(key)
        if cached is not None:
            return cached
        options = {} if factor == 1 else {'OVERVIEW_LEVEL':str(self.overviews.index(factor))}
        with rasterio.Env(GDAL_CACHEMAX=16*1024**2, GDAL_NUM_THREADS='1'), rasterio.open(self.path, **options) as ds:
            if factor > 1 and ds.width >= self.geometry.nx:
                raise ValueError('GDAL did not open the requested overview')
            r0,r1,c0,c1 = window
            g = self.geometry
            # A fractional overview window preserves exact native geographic edges.
            win = from_bounds(g.west+c0*g.resolution,g.north-r1*g.resolution,
                              g.west+c1*g.resolution,g.north-r0*g.resolution,ds.transform)
            raw = ds.read(window=win,out_shape=(self.count,*shape),resampling=Resampling.nearest)
            self.io_reads += 1
        if self.dtype.kind == 'f':
            raw = raw.astype(float)
            for i, code in enumerate(self.nodata):
                bad = ~np.isfinite(raw[i]) | (raw[i] == -9999)
                if code is not None:
                    bad |= raw[i] == code
                raw[i][bad] = np.nan
            raw *= self.factor
        if cache_limit is not None and raw.nbytes > cache_limit:
            return raw
        return self.cache.put(key,raw)

    def read(self, rows, cols):
        rows, cols = np.asarray(rows,dtype=int), np.asarray(cols,dtype=int)
        if not len(rows) or not len(cols):
            return np.empty((self.count,len(rows),len(cols)),dtype=self.dtype)
        r0,r1,c0,c1 = int(rows.min()),int(rows.max())+1,int(cols.min()),int(cols.max())+1
        if (r1-r0)*(c1-c0) > 2_100_000:
            raise ValueError('Native COG read exceeds bounded window; use display overviews')
        data = self._read((r0,r1,c0,c1),(r1-r0,c1-c0),1,cache_limit=1024**2)
        return data[:,rows[:,None]-r0,cols[None,:]-c0]

    def display(self, plan):
        factor = min((1,*self.overviews),key=lambda value:abs(math.log(value/plan.factor)))
        return self._read(plan.native_window,plan.shape,factor)

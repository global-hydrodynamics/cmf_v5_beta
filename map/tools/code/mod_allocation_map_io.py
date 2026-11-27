# SPDX-License-Identifier: Apache-2.0
# Parallel port of mod_allocation_map_io.F90; original Fortran authors and license retained.
"""Shared binary readers and network matching for parallel allocation tools.

Retain the one-area high-resolution restriction, km2 area units, 7x7 search,
row-major tie breaking, upstream ranking and stored relative downxy offsets.
No geographic nearest-cell substitution is made for invalid catmxy.
"""
import csv
import shlex

import numpy as np

from mod_map_io import Grid
try:
    from .hires_metadata import read_location_csv, read_location_txt
except ImportError:  # Direct execution from the map-local Shell wrappers.
    from hires_metadata import read_location_csv, read_location_txt


def read_allocation_base(root, extra=()):
    grid = Grid.read(root)
    fields = {'uparea': np.array(grid.raster(root/'uparea.bin'), copy=True),
              'nextxy': grid.raster(root/'nextxy.bin', '<i4', 2)}
    fields['uparea'][fields['uparea'] > 0] *= np.float32(1e-6)
    for name in extra:
        fields[name] = grid.raster(root/(name+'.bin'))
    return grid, fields


def read_allocation_hires(root, tag, elevation=False, map_format='netcdf'):
    directory = root/tag
    if map_format == 'netcdf':
        areas = read_location_csv(directory/'location.csv')
    else:
        directory = root/'binary'/tag
        areas = read_location_txt(directory/'location.txt')
    if len(areas) != 1:
        raise ValueError('Allocation supports exactly one high-resolution area')
    area = areas[0]
    west, east, south, north = (np.float32(value) for value in
                                (area.west, area.east, area.south, area.north))
    nx, ny = area.nx, area.ny
    grid = Grid(nx, ny, 0, np.float32(float(east-west)/nx), west, east, south, north)
    fields = {'uparea': grid.raster(directory/(tag+'.uparea.bin')),
              'catmxy': grid.raster(directory/(tag+'.catmxy.bin'), '<i2', 2),
              'downxy': grid.raster(directory/(tag+'.downxy.bin'), '<i2', 2)}
    if elevation:
        fields['elevtn'] = grid.raster(directory/(tag+'.elevtn.bin'))
    return grid, fields


def link_distance(lon1, lat1, lon2, lat2):
    """Reference ellipsoidal chord/arc approximation, returned in metres."""
    pi = np.float32(3.141592)
    eccentricity = float(np.float32(.006694470))
    def xyz(lon, lat):
        lat = np.asarray(lat, dtype='f4')*pi/np.float32(180)
        lon = np.asarray(lon, dtype='f4')*pi/np.float32(180)
        slat, clat = np.sin(lat.astype('f8')).astype('f4').astype('f8'), np.cos(lat.astype('f8')).astype('f4').astype('f8')
        slon, clon = np.sin(lon.astype('f8')).astype('f4').astype('f8'), np.cos(lon.astype('f8')).astype('f4').astype('f8')
        radius = 6378137./np.sqrt(1-eccentricity*slat*slat)
        return radius*clat*clon, radius*clat*slon, radius*(1-eccentricity)*slat
    first, second = xyz(lon1, lat1), xyz(lon2, lat2)
    chord = np.sqrt(sum((x-y)**2 for x, y in zip(first, second)))
    return (np.arcsin(np.asarray(chord/2/6378137., dtype='f4')).astype('f8')*2*6378137.).astype('f4')


class AllocationMap:
    """Read one network and derive ranked upstream cells and native outlets."""
    def __init__(self, root, tag, extra=(), elevation=False, map_format='netcdf'):
        self.grid, self.base = read_allocation_base(root, extra)
        self.hgrid, self.hires = read_allocation_hires(root, tag, elevation, map_format)
        nx, ny = self.grid.nx, self.grid.ny
        hx, hy = self.hgrid.nx, self.hgrid.ny
        self.assignment = self.hires['catmxy']
        self.down = self.hires['downxy']
        self.upstreams = [[] for _ in range(nx*ny)]
        nextx, nexty = self.base['nextxy']
        for y, x in zip(*np.nonzero(nextx > 0)):
            self.upstreams[(int(nexty[y, x])-1)*nx+int(nextx[y, x])-1].append((int(y), int(x)))
        for candidates in self.upstreams:
            candidates.sort(key=lambda cell: -self.base['uparea'][cell])
            candidates[:] = [cell for cell in candidates[:8] if self.base['uparea'][cell] > 0]
        self.outlets = np.full((ny, nx, 2), -9999, dtype='i4')
        maximum = np.zeros((ny, nx), dtype='f4')
        for start in range(0, hy, 64):
            stop = min(hy, start+64)
            yy, xx = np.indices((stop-start, hx))
            yy += start
            cx, cy = self.assignment[:, start:stop]
            valid = cx > 0
            if np.any(valid & ((cx > nx) | (cy < 1) | (cy > ny))):
                raise ValueError('Native assignment outside allocation base map')
            terminal = self.down[0, start:stop] <= -900
            tx = (xx+self.down[0, start:stop].astype('i4')) % hx
            ty = yy+self.down[1, start:stop].astype('i4')
            inside = (ty >= 0) & (ty < hy)
            safe_y = np.clip(ty, 0, hy-1)
            changed = ((self.assignment[0, safe_y, tx] != cx) | (self.assignment[1, safe_y, tx] != cy))
            candidates = valid & (terminal | (inside & changed))
            for row, col in zip(*np.nonzero(candidates)):
                cell = int(cy[row, col])-1, int(cx[row, col])-1
                downstream_area = self.hires['uparea'][safe_y[row, col], tx[row, col]]
                if terminal[row, col]:
                    self.outlets[cell] = (start+row, col)
                elif self.outlets[cell][0] == -9999:
                    self.outlets[cell] = (start+row, col)
                elif downstream_area > maximum[cell]:
                    maximum[cell] = downstream_area
                    self.outlets[cell] = (start+row, col)

    def next_pixel(self, pixel):
        y, x = pixel
        return int(y+self.down[1, y, x]), int((x+self.down[0, y, x]) % self.hgrid.nx)

    def assigned_cell(self, pixel):
        y, x = pixel
        cx, cy = self.assignment[:, y, x]
        if not (1 <= cx <= self.grid.nx and 1 <= cy <= self.grid.ny):
            return None
        return int(cy)-1, int(cx)-1

    def best_pixel(self, lat, lon, area):
        """Reference area/distance score; ties retain the first row-major pixel."""
        h = self.hgrid
        ix, iy = int(np.float32(lon-h.west)/h.size), int(np.float32(h.north-lat)/h.size)
        best, rate_min = None, np.float32(1e20)
        if area <= 0:
            return None
        for dy in range(-3, 4):
            for dx in range(-3, 4):
                x, y = ix+dx, iy+dy
                if self.grid.east-self.grid.west == 360:
                    x %= h.nx
                if not (0 <= x < h.nx and 0 <= y < h.ny):
                    continue
                upstream = self.hires['uparea'][y, x]
                if upstream <= area*np.float32(.05):
                    continue
                error = np.float32((upstream-area)/area)
                distance = np.sqrt(np.float32((x-ix)**2+(y-iy)**2))
                adjusted = np.float32(error+np.sign(error)*np.float32(.02)*distance)
                rate = (np.float32(1)+adjusted if adjusted >= 0 else
                        min(np.float32(1)/(np.float32(1)+adjusted), np.float32(1000)) if adjusted > -1 else np.float32(1000))
                if rate < rate_min:
                    rate_min, best = rate, (y, x)
        return best

    def trace(self, pixel, cell):
        """Yield in-catchment nonterminal pixels, guarding undefined cyclic inputs."""
        for _ in range(self.hgrid.nx*self.hgrid.ny+1):
            y, x = pixel
            if not (0 <= y < self.hgrid.ny and 0 <= x < self.hgrid.nx):
                return
            if self.assigned_cell(pixel) != cell or self.down[0, y, x] <= -900:
                return
            yield pixel
            pixel = self.next_pixel(pixel)
        raise ValueError('Cyclic high-resolution network')

    def upstream_matches(self, cell, pixel):
        for upstream in self.upstreams[cell[0]*self.grid.nx+cell[1]]:
            outlet = tuple(self.outlets[upstream])
            if outlet[0] < 0:
                raise ValueError('Missing upstream native outlet; reference indexing would be undefined')
            if pixel in self.trace(self.next_pixel(outlet), cell):
                yield upstream

    def distance(self, first, second):
        h = self.hgrid
        y, x = first
        yy, xx = second
        lon1 = h.west+(np.float32(x)+np.float32(.5))*h.size
        lat1 = h.north-(np.float32(y)+np.float32(.5))*h.size
        lon2 = h.west+(np.float32(xx)+np.float32(.5))*h.size
        lat2 = h.north-(np.float32(yy)+np.float32(.5))*h.size
        return np.float32(link_distance(lon1, lat1, lon2, lat2)*np.float32(.001))


def station_rows(path):
    """Read list-directed comma or whitespace records, preserving quoted names."""
    for line in path.read_text(encoding='utf-8-sig').splitlines()[1:]:
        if line.strip():
            yield next(csv.reader([line])) if ',' in line else shlex.split(line)

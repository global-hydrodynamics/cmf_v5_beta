# SPDX-License-Identifier: Apache-2.0
# Parallel port of analysis_river_point_info.F90; original Fortran authors and license retained.
"""Inspect one river cell using the same xy/latlon selection as Fortran.

Read standard NetCDF maps, stored outlet coordinates and basin attributes.
latlon prefers a 15sec assignment map, then 1min, then geographic containment.
All reported IX/IY are explicitly one-based; Python indices are also printed.
"""
import numpy as np

from mod_map_io import Grid, parser, read_array
try:
    from .hires_metadata import read_location_csv, read_location_txt
except ImportError:  # Direct execution from the map-local Shell workflows.
    from hires_metadata import read_location_csv, read_location_txt


def main():
    p = parser(__doc__)
    p.add_argument('mode', choices=['xy', 'latlon'])
    p.add_argument('first', type=np.float32)
    p.add_argument('second', type=np.float32)
    args = p.parse_args()
    grid = Grid.read(args.map_dir)
    suffix = '.nc' if args.map_format == 'netcdf' else '.bin'
    nextxy = grid.raster(args.map_dir / f'nextxy{suffix}', '<i4', 2)
    basin = grid.raster(args.map_dir / f'basin{suffix}', '<i4')
    upgrid = grid.raster(args.map_dir / f'upgrid{suffix}', '<i4')
    uparea = grid.raster(args.map_dir / f'uparea{suffix}')
    ctmare = grid.raster(args.map_dir / f'ctmare{suffix}')
    elevation = grid.raster(args.map_dir / f'elevtn{suffix}')
    outlets = grid.raster(args.map_dir / f'lonlat{suffix}', '<f4', 2)
    if args.mode == 'xy':
        ix, iy = int(args.first), int(args.second)
        lon = np.float32(grid.west + grid.size * np.float32(ix - .5))
        lat = np.float32(grid.north - grid.size * np.float32(iy - .5))
    else:
        lat, lon = args.first, args.second
        ix = iy = None
        for tag in ('15sec', '1min'):
            if args.map_format == 'netcdf':
                location = args.map_dir / tag / 'location.csv'
                areas = read_location_csv(location) if location.is_file() else []
            else:
                location = args.map_dir / 'binary' / tag / 'location.txt'
                areas = read_location_txt(location) if location.is_file() else []
            if not areas:
                continue
            area = areas[0]
            if area.carea != tag:
                continue
            nx, ny, size = area.nx, area.ny, np.float32(area.csize)
            x = int(np.float32((lon - grid.west) / size))
            y = int(np.float32((grid.north - lat) / size))
            if not (0 <= x < nx and 0 <= y < ny):
                p.error('ix,iy cannot be defined')
            assignment = read_array(
                args.map_dir / tag / f'{tag}.catmxy{suffix}', '<i2', (2, ny, nx),
            )
            ix, iy = (int(v) for v in assignment[:, y, x])
            break
        if ix is None:
            ix = int(np.float32((lon - grid.west) / grid.size)) + 1
            iy = int(np.float32((grid.north - lat) / grid.size)) + 1
    if not (1 <= ix <= grid.nx and 1 <= iy <= grid.ny):
        p.error('grid indices are outside map or unassigned')
    r, c = iy - 1, ix - 1
    glon = np.float32(grid.west + grid.size * np.float32(ix - .5))
    glat = np.float32(grid.north - grid.size * np.float32(iy - .5))
    print('Point Information')
    print('Fortran IX,IY:', ix, iy)
    print('Python  IX,IY:', ix - 1, iy - 1)
    print('Lat, Lon  (Point):', lat, lon)
    print('Lat, Lon  (Grid Center):', glat, glon)
    print('Lat, Lon  (Catchment Outler):', outlets[1,r,c], outlets[0,r,c])
    print('River Basin ID:', basin[r,c])
    print('Drainage Area [km2]:', np.float32(uparea[r,c] * np.float32(1e-6)))
    print('Upstream Grids:', upgrid[r,c])
    print('Elevation (Catchment Outler) [m]:', elevation[r,c])
    print('Unit Catchment Area [km2]:', np.float32(ctmare[r,c] * np.float32(1e-6)))
    if nextxy[0,r,c] < 0 and nextxy[0,r,c] != -9999:
        print('RIVER MOUTH GRID')
    else:
        x, y = nextxy[:,r,c]
        print('Downstream IX,IY,AREA:', x, y, np.float32(uparea[y-1,x-1] * np.float32(1e-6)))
    for y, x in np.argwhere((nextxy[0] == ix) & (nextxy[1] == iy) & (nextxy[0] > 0)):
        print('Upstream   IX,IY,AREA:', x+1, y+1, np.float32(uparea[y,x] * np.float32(1e-6)))


if __name__ == '__main__':
    main()

# SPDX-License-Identifier: Apache-2.0
# Parallel port of param_water_calc_prmwat.F90; original Fortran authors and license retained.
"""Aggregate permanent-water area using the current reference criteria.

Read catchment assignments, rivwth, flddif and pixel areas; accumulate
float32 areas in native pixel order and cap at ctmare. Preserve flddif <= 5 m,
including the documented legacy inclusion of flddif=-9999. No scientific
reinterpretation of that sentinel is made in this parallel implementation.
"""
import numpy as np

from mod_map_io import Grid, input_path, output_root, parser, read_array, write_raster
try:
    from .hires_metadata import read_location_csv, read_location_txt
except ImportError:  # Direct execution from the map-local Shell wrappers.
    from hires_metadata import read_location_csv, read_location_txt
from region_combine_hires import PIXELS_PER_DEGREE


def exact_array(path, dtype, shape):
    """Read the declared raster from standard NetCDF or explicit legacy Binary."""
    resolved = input_path(path)
    if resolved.suffix == '.bin' and resolved.stat().st_size != np.prod(shape)*np.dtype(dtype).itemsize:
        raise ValueError(f'Wrong binary size: {resolved}')
    return read_array(path, dtype, shape)


def fallback_area(north, rows, size):
    """Legacy double geometry with the explicit float32 area cast, in km2."""
    latitude = north-(np.arange(rows, dtype='f4')+np.float32(.5)).astype('f8')*size
    sine_north = np.sin(np.clip(latitude+5*size, -90, 90)*float(np.float32(np.pi))/180.)
    sine_south = np.sin(np.clip(latitude-5*size, -90, 90)*float(np.float32(np.pi))/180.)
    e = np.sqrt(.00669447)
    first = sine_north*(1+(e*sine_north)**2/2)
    second = sine_south*(1+(e*sine_south)**2/2)
    area = (np.pi*6378136.**2*(1-e**2)/180.*(first-second)).astype('f4').astype('f8')
    return (np.abs(area*(10*size))*float(np.float32(.01))*float(np.float32(1e-6))).astype('f4')


def main():
    p = parser(__doc__, map_default='.')
    p.add_argument('hires_tag', choices=list(PIXELS_PER_DEGREE))
    args = p.parse_args()
    grid = Grid.read(args.map_dir)
    if grid.nx <= 0 or grid.ny <= 0 or grid.nlfp < 0 or not np.isfinite(grid.size) or grid.size <= 0:
        raise ValueError('Invalid map geometry')
    if not np.isfinite([grid.west, grid.east, grid.south, grid.north]).all():
        raise ValueError('Nonfinite map bounds')
    nextx = exact_array(args.map_dir/'nextxy.bin', '<i4', (2, grid.ny, grid.nx))[0]
    area = exact_array(args.map_dir/'ctmare.bin', '<f4', (grid.ny, grid.nx))
    valid = nextx != -9999
    if np.any(valid & (~np.isfinite(area) | (area <= 0))):
        raise ValueError('Invalid ctmare in river domain')
    result = np.where(valid, np.float32(0), np.float32(-9999))
    root = args.map_dir/args.hires_tag
    areas = (read_location_csv(root/'location.csv') if args.map_format == 'netcdf'
             else read_location_txt(args.map_dir/'binary'/args.hires_tag/'location.txt'))
    selected_count = missing_count = 0
    used_fallback = False
    size = 1./PIXELS_PER_DEGREE[args.hires_tag]
    for tile in areas:
        name = tile.carea
        if name in ('.', '..') or '/' in name or chr(92) in name:
            raise ValueError('Unsafe area name')
        west, east, south, north = tile.west, tile.east, tile.south, tile.north
        nx, ny = tile.nx, tile.ny
        if abs(tile.csize-size) > 1e-8:
            raise ValueError('Invalid high-resolution geometry or tag resolution')
        assignment = exact_array(root/(name+'.catmxy.bin'), '<i2', (2, ny, nx))
        width = exact_array(root/(name+'.rivwth.bin'), '<f4', (ny, nx))
        height = exact_array(root/(name+'.flddif.bin'), '<f4', (ny, nx))
        pixel_path = root/(name+'.grdare.bin')
        resolved_pixel = input_path(pixel_path)
        pixel = exact_array(pixel_path, '<f4', (ny, nx)) if resolved_pixel.exists() else None
        fallback = fallback_area(north, ny, size) if pixel is None else None
        if pixel is None:
            used_fallback = True
            print(f'WARNING: missing {pixel_path}; using the legacy scaled rgetarea fallback.')
        for start in range(0, ny, 64):
            mx, my = assignment[:, start:start+64]
            assigned = mx > 0
            invalid = assigned & ((mx > grid.nx) | (my < 1) | (my > grid.ny))
            if np.any(invalid):
                raise ValueError('catmxy assignment outside base map')
            row, col = np.nonzero(assigned)
            if np.any(nextx[my[row, col]-1, mx[row, col]-1] == -9999):
                raise ValueError('catmxy assignment outside river network')
            w, h = width[start:start+64], height[start:start+64]
            if np.any(assigned & (~np.isfinite(w) | ~np.isfinite(h))):
                raise ValueError('Nonfinite water field')
            selected = assigned & ((w > 0) | (w == -1)) & (h <= 5)
            row, col = np.nonzero(selected)
            weights = pixel[start+row, col] if pixel is not None else fallback[start+row]
            if np.any(~np.isfinite(weights) | (weights <= 0)):
                raise ValueError('Invalid area for selected water pixel')
            cells = (my[row, col].astype('i8')-1)*grid.nx+mx[row, col]-1
            np.add.at(result.ravel(), cells, weights*np.float32(1e6))
            if not np.isfinite(result).all():
                raise ValueError('Nonfinite accumulated water area')
            selected_count += len(row)
            missing_count += int(np.count_nonzero(selected & (h == -9999)))
    capped = valid & (result > area)
    result[capped] = area[capped]
    if missing_count:
        print(f'WARNING: {missing_count} selected pixels have flddif=-9999; legacy flddif<=5 selection is preserved.')
    write_raster(output_root(args)/'prmwat.bin', result, '<f4', grid=grid)
    print(f'Processed high-resolution areas: {count}')
    print(f'Valid unit catchments: {np.count_nonzero(valid)}')
    print(f'Selected permanent-water pixels: {selected_count}')
    print(f'Catchments capped at ctmare: {np.count_nonzero(capped)}')
    print(f'Used grdare fallback: {"T" if used_fallback else "F"}')
    filename = 'prmwat.nc' if args.map_format == 'netcdf' else 'prmwat.bin'
    print(f'Wrote {filename} (float32, one NX x NY record, units m2).')


if __name__ == '__main__':
    main()

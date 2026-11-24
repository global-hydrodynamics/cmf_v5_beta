# SPDX-License-Identifier: Apache-2.0
# Parallel port of param_channel_calc_rivwth.F90; original Fortran authors and license retained.
"""Calculate channel depth, width and roughness from annual mean discharge.

Read the existing DIMINFO and binary topology/discharge, apply the reference
float32 power laws, and write the four independent binary parameter products.
The optional cdf mode also writes the reference rivpar.nc interface.
"""
from pathlib import Path

import numpy as np

from mod_map_io import Grid, output_root, parser, write_raster


def main():
    p = parser(__doc__, map_default='.')
    p.add_argument('type', nargs='?', default='bin', choices=['bin', 'cdf'])
    p.add_argument('diminfo', nargs='?', type=Path, default=Path('diminfo_test-1deg.txt'))
    for name, default in [('hc', .1), ('hp', .5), ('ho', 0), ('hmin', 1),
                          ('wc', .4), ('wp', .75), ('wo', 0), ('wmin', 10)]:
        p.add_argument(name, nargs='?', type=np.float32, default=np.float32(default))
    args = p.parse_args()
    lines = args.diminfo.read_text().splitlines()
    nx, ny = (int(lines[i].split()[0]) for i in (0, 1))
    west, east, north, south = (np.float32(lines[i].split()[0]) for i in (7, 8, 9, 10))
    grid = Grid(nx, ny, 0, np.float32((east-west)/nx), west, east, south, north)
    valid = grid.raster(args.map_dir/'nextxy.bin', '<i4', 2)[0] != -9999
    discharge = grid.raster(args.map_dir/'outclm.bin')
    fields = {
        'rivhgt': np.where(valid, np.maximum(args.hmin, args.hc*discharge**args.hp+args.ho), -9999),
        'rivwth': np.where(valid, np.maximum(args.wmin, args.wc*discharge**args.wp+args.wo), -9999),
        'rivman': np.where(valid, np.float32(.03), np.float32(-9999)),
        'rivhgt_inf': np.full((ny, nx), 100000, dtype='<f4'),
    }
    out = output_root(args)
    # Import before producing outputs so an unavailable optional interface fails cleanly.
    if args.type == 'cdf':
        from netCDF4 import Dataset
    for name, values in fields.items():
        write_raster(out/(name+'.bin'), values, '<f4')
    if args.type == 'cdf':
        destination = out/'rivpar.nc'
        with Dataset(destination, 'w', format='NETCDF3_64BIT_OFFSET') as dataset:
            dataset.createDimension('lon', nx)
            dataset.createDimension('lat', ny)
            for name, count, origin, sign, units in [
                ('lon', nx, west, 1, 'degrees_east'), ('lat', ny, north, -1, 'degrees_north')]:
                var = dataset.createVariable(name, 'f4', (name,))
                var[:] = origin+np.float32(sign)*(np.arange(count, dtype='f4')+np.float32(.5))*grid.size
                var.long_name = 'Longitude' if name == 'lon' else 'Latitude'
                var.units = units
            for name in ['rivhgt', 'rivwth']:
                var = dataset.createVariable(name, 'f4', ('lat', 'lon'))
                var.long_name = 'river bank height' if name == 'rivhgt' else 'river channel width'
                var.units = 'm'
                var.missing_value = np.float32(1e20)
                var[:] = fields[name]


if __name__ == '__main__':
    main()

# SPDX-License-Identifier: Apache-2.0
# Parallel port of param_channel_calc_rivwth.F90; original Fortran authors and license retained.
"""Calculate channel depth, width and roughness from annual mean discharge.

Read DIMINFO and map-root discharge, apply the reference float32 power laws,
and write the parameter rasters plus the standard NetCDF parameter interface.
"""
from pathlib import Path

import numpy as np

from mod_map_io import Grid, output_root, parser, write_raster


def main():
    p = parser(__doc__, map_default='.', map_binary_flag=True)
    p.add_argument('diminfo', type=Path)
    for name in ('hc', 'hp', 'ho', 'hmin', 'wc', 'wp', 'wo', 'wmin'):
        p.add_argument(name, type=np.float32)
    p.add_argument('--no-rivpar-netcdf', action='store_true', help='Do not write the supplementary rivpar.nc interface.')
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
    output_grid = Grid.from_file(args.map_dir/'params.txt')
    # Import before producing outputs so an unavailable NetCDF interface fails cleanly.
    if not args.no_rivpar_netcdf:
        from netCDF4 import Dataset
    for name, values in fields.items():
        write_raster(out/(name+'.bin'), values, '<f4', grid=output_grid)
    if not args.no_rivpar_netcdf:
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

# SPDX-License-Identifier: Apache-2.0
# Parallel port of param_channel_calc_rivwth.F90; original Fortran authors and license retained.
"""Calculate channel depth, width and roughness from annual mean discharge.

Read DIMINFO and map-root discharge, apply the reference float32 power laws,
and write the parameter rasters plus the standard NetCDF parameter interface.
"""
from pathlib import Path

import numpy as np

from mod_map_io import Grid, input_path, output_root, parser, write_raster
try:
    from .map_metadata import read_diminfo_nml
except ImportError:  # Direct execution from map-local Shell workflows.
    from map_metadata import read_diminfo_nml


def calculate_channel_fields(discharge, valid, args):
    """Apply the reference power laws only to mapped cells with valid discharge."""
    valid_discharge = discharge[valid]
    invalid_discharge = ~np.isfinite(valid_discharge) | (valid_discharge < 0)
    if np.any(invalid_discharge):
        invalid_values = valid_discharge[invalid_discharge]
        examples = ', '.join(str(float(value)) for value in invalid_values[:5])
        raise ValueError(
            f'{invalid_values.size} mapped river cells have negative or non-finite '
            f'annual-mean discharge; sample values: {examples}'
        )

    missing = np.float32(-9999)
    rivhgt = np.full(discharge.shape, missing, dtype='f4')
    rivwth = np.full(discharge.shape, missing, dtype='f4')
    # Zero discharge is valid; the existing minimum depth/width then applies.
    rivhgt[valid] = np.maximum(args.hmin, args.hc*valid_discharge**args.hp+args.ho)
    rivwth[valid] = np.maximum(args.wmin, args.wc*valid_discharge**args.wp+args.wo)
    rivman = np.where(valid, np.float32(.03), missing)
    return {
        'rivhgt': rivhgt,
        'rivwth': rivwth,
        'rivman': rivman,
        'rivhgt_inf': np.full(discharge.shape, 100000, dtype='<f4'),
    }


def main():
    p = parser(__doc__, map_default='.', map_binary_flag=True)
    p.add_argument('diminfo', type=Path)
    for name in ('hc', 'hp', 'ho', 'hmin', 'wc', 'wp', 'wo', 'wmin'):
        p.add_argument(name, type=np.float32)
    p.add_argument('--no-rivpar-netcdf', action='store_true', help='Do not write the supplementary rivpar.nc interface.')
    args = p.parse_args()

    #*** 1. Read map geometry, topology, and annual-mean discharge
    diminfo_path = args.diminfo.resolve()
    info = read_diminfo_nml(diminfo_path)
    nx, ny = info.nx, info.ny
    west, east, north, south = (np.float32(info.west), np.float32(info.east),
                                np.float32(info.north), np.float32(info.south))
    grid = Grid(nx, ny, 0, np.float32((east-west)/nx), west, east, south, north)
    nextxy_path = input_path(args.map_dir/'nextxy.bin')
    discharge_path = input_path(args.map_dir/'outclm.bin')
    valid = grid.raster(nextxy_path, '<i4', 2)[0] != -9999
    discharge = grid.raster(discharge_path)
    print('Inputs:')
    print(f'  DIMINFO: {diminfo_path}')
    print(f'  River topology: {nextxy_path.resolve()}')
    print(f'  Annual-mean discharge: {discharge_path.resolve()}')

    #*** 2. Calculate channel depth, width, and roughness
    print('Channel depth [m]:')
    print(f'  rivhgt = max({args.hmin:g}, {args.hc:g} * Q^{args.hp:g} + {args.ho:g})')
    print('Channel width [m]:')
    print(f'  rivwth = max({args.wmin:g}, {args.wc:g} * Q^{args.wp:g} + {args.wo:g})')
    print('Manning roughness: rivman = 0.03 on mapped river cells')
    print('Outside-network cells retain -9999; zero discharge is valid and uses the minimum dimensions.')
    fields = calculate_channel_fields(discharge, valid, args)

    #*** 3. Write channel parameter products
    out = output_root(args)
    output_grid = Grid.from_file(args.map_dir)
    # Import before producing outputs so an unavailable NetCDF interface fails cleanly.
    if not args.no_rivpar_netcdf:
        from netCDF4 import Dataset
    written = []
    for name, values in fields.items():
        written.append(write_raster(out/(name+'.bin'), values, '<f4', grid=output_grid))
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
        written.append(destination)
    print('Output files:')
    for path in written:
        print(f'  {path.resolve()}')


if __name__ == '__main__':
    main()

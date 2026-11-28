# SPDX-License-Identifier: Apache-2.0
# Parallel port of region_default_inpmat.F90; original Fortran authors and license retained.
"""Build the reference regional default global 1-degree input matrix.

Use the same sparse matrix representation as param_inpmat_generate while
retaining this program's one-pixel area approximation and fixed grid settings.
NetCDF is the default; explicit Binary mode remains available.
"""
import numpy as np

from mod_map_io import Grid, output_root, parser
from param_inpmat_generate import generate


def main():
    p = parser(__doc__)
    p.add_argument('hires_tag')
    args = p.parse_args()
    #*** 1. Read selected high-resolution source geometry
    grid = Grid.read(args.map_dir)
    source = args.map_dir/args.hires_tag
    location_path = source/'location.csv'
    print(f'Inputs: map geometry and products from {args.map_dir.resolve()}; high-resolution metadata: {location_path.resolve()}')
    print(f'Parameters: tag={args.hires_tag}; standard global runoff grid=1 degree, west/east=-180/180, south/north=-90/90, latitude order=NtoS.')
    print('Calculation: create the reference default INPMAT from high-resolution assignments; use native grdare when available and the legacy area approximation when it is missing.')

    #*** 2. Generate the fixed-name global default matrix
    matrix_path, descriptors = generate(grid, source, output_root(args), np.float32(1),
                                        np.float32(-180), np.float32(180), np.float32(90),
                                        np.float32(-90), 'NtoS', 'diminfo_test-1deg.nml',
                                        'inpmat_test-1deg.bin', legacy_default=True,
                                        map_format=args.map_format)
    print('Output files:')
    for path in [matrix_path, *descriptors]:
        print(f'  {path.resolve()}')


if __name__ == '__main__':
    main()

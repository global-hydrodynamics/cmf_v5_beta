# SPDX-License-Identifier: Apache-2.0
# Parallel port of region_default_inpmat.F90; original Fortran authors and license retained.
"""Build the reference regional default global 1-degree input matrix.

Use the same sparse binary layout as param_inpmat_generate but retain this
program's one-pixel area approximation and fixed filenames/grid settings.
"""
import numpy as np

from mod_map_io import Grid, output_root, parser
from param_inpmat_generate import generate


def main():
    p = parser(__doc__)
    p.add_argument('hires_tag')
    args = p.parse_args()
    generate(Grid.read(args.map_dir/'params.txt'), args.map_dir/args.hires_tag,
             output_root(args), np.float32(1), np.float32(-180), np.float32(180),
             np.float32(90), np.float32(-90), 'NtoS', 'diminfo_test-1deg.txt',
             'inpmat_test-1deg.bin', legacy_default=True)


if __name__ == '__main__':
    main()

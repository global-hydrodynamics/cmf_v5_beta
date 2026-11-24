# SPDX-License-Identifier: Apache-2.0
# Parallel port of analysis_mpi_region_color.F90; original Fortran authors and license retained.
"""Experimental Python equivalent of the MPI region display-color utility.

Read params and mpireg-N.bin, apply the unchanged legacy coloring policy,
and create bsncol_mpi-N.bin in the selected isolated output directory.
"""
import re
from pathlib import Path

import numpy as np

from mod_map_color import color_map
from mod_map_io import Grid, output_root, parser, write_raster


def main():
    args_parser = parser(__doc__, '.')
    args_parser.add_argument('region_file', type=Path)
    args = args_parser.parse_args()
    match = re.fullmatch(r'mpireg-([1-9][0-9]*)\.bin', args.region_file.name)
    if match is None:
        args_parser.error('input filename must be mpireg-N.bin with positive N')
    grid = Grid.read(args.map_dir / 'params.txt')
    regions = grid.raster(args.region_file, '<i4')
    if not 1 <= regions.max() <= int(match[1]):
        args_parser.error('region IDs do not match MPI count')
    colors = color_map(regions, grid.west, grid.east)
    destination = (args.output_dir or args.region_file.parent) / f'bsncol_mpi-{int(match[1])}.bin'
    write_raster(destination, colors, '<i4')
    print(f'Created {destination} (visualization only)')


if __name__ == '__main__':
    main()

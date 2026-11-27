# SPDX-License-Identifier: Apache-2.0
# Parallel port of param_channel_set_merit_width.F90; original Fortran authors and license retained.
"""Merge MERIT and power-law widths with the inherited piecewise limits.

Read nextxy/rivwth/width, preserve the distinct below-50 and below-half branches,
and write one float32 rivwth_merit.bin record; outside network is -9999.
"""
from pathlib import Path

import numpy as np

from mod_map_io import Grid, input_path, output_root, parser, write_raster
try:
    from .map_metadata import read_diminfo_nml
except ImportError:  # Direct execution from map-local Shell workflows.
    from map_metadata import read_diminfo_nml


def merge_widths(nextx, width, merit):
    """Preserve branch order: the 10,000m cap belongs ONLY to the final branch."""
    result = np.array(merit, dtype=np.float32)
    small = result < np.float32(50)
    half = (~small) & (result < width * np.float32(.5))
    other = ~(small | half)
    result[small] = np.maximum(result[small], width[small])
    result[half] = width[half] * np.float32(.5)
    result[other] = np.minimum(np.minimum(result[other], width[other] * np.float32(5)), np.float32(10000))
    result[nextx == -9999] = -9999
    return result


def main():
    p = parser(__doc__, '.', map_binary_flag=True)
    p.add_argument('diminfo', type=Path)
    args = p.parse_args()
    #*** 1. Read geometry and width inputs
    diminfo_path = args.diminfo.resolve()
    info = read_diminfo_nml(diminfo_path)
    grid = Grid(info.nx, info.ny, 0, *[np.float32(0)] * 5)
    paths = {name: input_path(args.map_dir / f'{name}.bin')
             for name in ('nextxy', 'rivwth', 'width')}
    nextxy = grid.raster(paths['nextxy'], '<i4', 2)
    width = grid.raster(paths['rivwth'])
    merit = grid.raster(paths['width'])
    print('Inputs:')
    print(f'  DIMINFO: {diminfo_path}')
    for name, path in paths.items():
        print(f'  {name}: {path.resolve()}')

    #*** 2. Merge MERIT Hydro and power-law channel width
    print('Calculation: if MERIT width < 50 m, use max(MERIT width, power-law width); else use 0.5*power-law width when MERIT width < 0.5*power-law width; otherwise cap MERIT width at min(5*power-law width, 10,000 m).')
    result = merge_widths(nextxy[0], width, merit)

    #*** 3. Write merged channel width
    output_grid = Grid.from_file(args.map_dir)
    destination = write_raster(output_root(args) / 'rivwth_merit.bin', result, '<f4', grid=output_grid)
    print(f'Output: {destination.resolve()}')


if __name__ == '__main__':
    main()

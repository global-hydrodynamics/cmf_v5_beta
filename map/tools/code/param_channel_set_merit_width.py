# SPDX-License-Identifier: Apache-2.0
# Parallel port of param_channel_set_merit_width.F90; original Fortran authors and license retained.
"""Merge MERIT and power-law widths with the inherited piecewise limits.

Read nextxy/rivwth/width, preserve the distinct below-50 and below-half branches,
and write one float32 rivwth_merit.bin record; outside network is -9999.
"""
from pathlib import Path

import numpy as np

from mod_map_io import Grid, output_root, parser, write_raster


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
    p = parser(__doc__, '.')
    p.add_argument('diminfo', type=Path)
    args = p.parse_args()
    dims = [int(line.split()[0]) for line in args.diminfo.read_text().splitlines()[:2]]
    grid = Grid(*dims, 0, *[np.float32(0)] * 5)
    nextxy = grid.raster(args.map_dir / 'nextxy.bin', '<i4', 2)
    width = grid.raster(args.map_dir / 'rivwth.bin')
    merit = grid.raster(args.map_dir / 'width.bin')
    result = merge_widths(nextxy[0], width, merit)
    output_grid = Grid.from_file(args.map_dir/'params.txt')
    write_raster(output_root(args) / 'rivwth_merit.bin', result, '<f4', grid=output_grid)


if __name__ == '__main__':
    main()

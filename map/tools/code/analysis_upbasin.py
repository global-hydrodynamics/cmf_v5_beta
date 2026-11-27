# SPDX-License-Identifier: Apache-2.0
# Parallel port of analysis_upbasin.F90; original Fortran authors and license retained.
"""Create the Fortran-compatible selected upstream catchment mask.

Read nextxy, upgrid and uparea; memoize downstream labels in row-major order.
Output int32: 1 reaches selected cell, 0 other river, -9999 outside network.
One-based positional IX/IY and the terminal codes retain the reference meaning.
"""
from pathlib import Path

import numpy as np

from mod_map_io import Grid, input_path, output_root, parser, write_raster


def upstream_mask(nextxy, ix, iy):
    """Label downstream paths; reject cycles rather than hanging on invalid maps."""
    ny, nx = nextxy.shape[1:]
    if not (1 <= ix <= nx and 1 <= iy <= ny):
        raise ValueError('grid indices outside map')
    if nextxy[0, iy - 1, ix - 1] == -9999:
        return None
    labels = np.full((ny, nx), -9999, dtype=np.int32)
    labels[(nextxy[0] != -9999) & (nextxy[0] <= 0)] = 0
    labels[iy - 1, ix - 1] = 1
    for row, col in np.argwhere((nextxy[0] != -9999) & (labels == -9999)):
        if labels[row, col] != -9999:
            continue
        path = []
        r, c = int(row), int(col)
        while labels[r, c] == -9999:
            path.append((r, c))
            if len(path) > nx * ny:
                raise ValueError('cyclic downstream path')
            c, r = int(nextxy[0, r, c]) - 1, int(nextxy[1, r, c]) - 1
            if not (0 <= c < nx and 0 <= r < ny):
                raise ValueError('unresolved downstream index')
        value = labels[r, c]
        for r, c in path:
            labels[r, c] = value
    return labels


def main():
    p = parser(__doc__)
    p.add_argument('ix', type=int)
    p.add_argument('iy', type=int)
    p.add_argument('output', nargs='?', type=Path)
    args = p.parse_args()
    #*** 1. Read river network and upstream attributes
    grid = Grid.read(args.map_dir)
    paths = {name: input_path(args.map_dir/(name+'.bin'))
             for name in ('nextxy', 'upgrid', 'uparea')}
    nextxy = grid.raster(paths['nextxy'], '<i4', 2)
    # The reference requires these inputs even though only nextxy determines labels.
    upgrid = grid.raster(paths['upgrid'], '<i4')
    uparea = grid.raster(paths['uparea'])
    print('Inputs:')
    for name, path in paths.items():
        print(f'  {name}: {path.resolve()}')
    print(f'Parameters: selected river-map cell=(ix={args.ix}, iy={args.iy}) (1-based Fortran indexing).')

    #*** 2. Label upstream cells and report selected-cell attributes
    labels = upstream_mask(nextxy, args.ix, args.iy)
    if labels is None:
        print('error: [ix,iy] is not land')
        return
    print('Upstream Grid #:', upgrid[args.iy - 1, args.ix - 1])
    print('Upstream Area [km2]:', np.float32(uparea[args.iy - 1, args.ix - 1] * np.float32(1e-6)))
    output = args.output or output_root(args) / f'analysis_upbasin_{args.ix}_{args.iy}.bin'
    #*** 3. Write selected upstream mask
    destination = write_raster(output, labels, '<i4', grid=grid)
    print(f'Output: {destination.resolve()}')


if __name__ == '__main__':
    main()

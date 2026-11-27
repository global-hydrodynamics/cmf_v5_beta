# SPDX-License-Identifier: Apache-2.0
# Parallel port of region_cut_bifway.F90; original Fortran authors and license retained.
"""Crop original bifurcation paths using the existing dim_change contract.

Translate endpoints, retain the reference strict interior-cell condition and
edge-masked river domain, then write regional bifori.txt in source path order.
The last row/column exclusion is intentional reference behavior.
"""
from pathlib import Path

import numpy as np

from mod_map_io import Grid, output_root, parser


def main():
    p = parser(__doc__)
    p.add_argument('--change-info', type=Path, default=Path('dim_change.txt'))
    args = p.parse_args()
    lines = args.change_info.read_text().splitlines()
    source = Path(lines[0].strip())
    nx, ny, dx, dy = (int(lines[i].split()[0]) for i in (9, 10, 11, 12))
    nextx = Grid.read(args.map_dir).raster(args.map_dir/'nextxy_noedge.bin', '<i4', 2)[0]
    records = (source/'bifori.txt').read_text().splitlines()
    npath, nlev = map(int, records[0].split()[:2])
    selected = []
    for record in records[1:npath+1]:
        fields = record.split()
        ix, iy, jx, jy = map(int, fields[:4])
        ix, iy, jx, jy = ix-dx, iy-dy, jx-dx, jy-dy
        if not (0 < ix < nx and 0 < jx < nx and 0 < iy < ny and 0 < jy < ny):
            continue
        if nextx[iy-1, ix-1] == -9999 or nextx[jy-1, jx-1] == -9999:
            continue
        values = [np.float32(value) for value in fields[4:]]
        selected.append(''.join(f'{i:8d}' for i in (ix, iy, jx, jy))
                        + ''.join(f'{v:12.2f}' for v in values[:2+nlev])
                        + ''.join(f'{v:10.3f}' for v in values[2+nlev:4+nlev]))
    out = output_root(args)
    out.mkdir(parents=True, exist_ok=True)
    with (out/'bifori.txt').open('w') as stream:
        stream.write(f'{len(selected):8d}{nlev:8d}   npath, nlev, (ix,iy), (jx,jy), length, elevtn, (width1, width2, ... wodth_nlev), (lon,lat)\n')
        for row in selected:
            stream.write(row+'\n')


if __name__ == '__main__':
    main()

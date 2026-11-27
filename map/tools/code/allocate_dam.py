# SPDX-License-Identifier: Apache-2.0
# Parallel port of allocate_dam.F90; original Fortran authors and license retained.
"""Allocate dams to reference river cells or classify them as subgrid dams.

Use native high-resolution matching, upstream single-cell substitution, and
the original 0.3*ctmare small-dam rule. Write separate river/small/error lists.
"""
from contextlib import ExitStack
from pathlib import Path

import numpy as np

from mod_allocation_map_io import AllocationMap, station_rows
from mod_map_io import parser


def main():
    p = parser(__doc__)
    p.add_argument('dam_list', type=Path)
    p.add_argument('hires_tag')
    args = p.parse_args()
    maps = AllocationMap(args.map_dir, args.hires_tag, extra=('ctmare',), map_format=args.map_format)
    catchment_area = np.array(maps.base['ctmare'], copy=True)
    catchment_area[catchment_area > 0] *= np.float32(1e-6)
    out = args.output_dir or Path('.')
    out.mkdir(parents=True, exist_ok=True)
    with ExitStack() as stack:
        streams = {kind: stack.enter_context((out/f'dam_alloc_{kind}.txt').open('w')) for kind in ('river', 'small', 'error')}
        for stream in streams.values():
            stream.write('        ID       lat       lon   area_CaMa  area_Input       error        diff      ix      iy     cap_mcm  year  damname                         rivname\n')
        for f in station_rows(args.dam_list):
            if not f:
                continue
            identifier = int(f[0])
            lat, lon, area = map(np.float32, f[1:4])
            damname, rivname = f[4:6]
            capacity, year = np.float32(f[6]), int(f[7])
            g = maps.grid
            if capacity < 0 or lon < g.west or lon > g.east or lat < g.south or lat > g.north:
                continue
            pixel = maps.best_pixel(lat, lon, area)
            cell = maps.assigned_cell(pixel) if pixel is not None else None
            kind, total, error, difference, ix, iy = 'error', -999., -999., -999., -999, -999
            if cell is not None:
                chosen = cell
                total = maps.base['uparea'][cell]
                error = np.float32((total-area)/area)
                if area >= catchment_area[cell]*np.float32(.3) and abs(error) > np.float32(.2):
                    for upstream in maps.upstream_matches(cell, pixel):
                        candidate = maps.base['uparea'][upstream]
                        if candidate < area*np.float32(.1):
                            break
                        mismatch = np.float32((candidate-area)/area)
                        if abs(mismatch) < abs(error):
                            error, total, chosen = mismatch, candidate, upstream
                            if abs(error) < np.float32(.1):
                                break
                kind = 'river'
                ix, iy = chosen[1]+1, chosen[0]+1
                difference = np.float32(total-area)
                error = np.float32(difference/area)
                if area < catchment_area[cell]*np.float32(.3) or error > 1:
                    kind, total, difference, error = 'small', -888., -888., -8.
                    ix, iy = cell[1]+1, cell[0]+1
            streams[kind].write(f'{identifier:10d}{lat:10.3f}{lon:10.3f}'
                                + ''.join(f'{v:12.1f}' for v in [total, area, error, difference])
                                + f'{ix:8d}{iy:8d}{capacity:12.1f}{year:6d}  {damname[:30]:<30}  {rivname[:30]:<30}\n')


if __name__ == '__main__':
    main()

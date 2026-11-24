# SPDX-License-Identifier: Apache-2.0
# Parallel port of allocate_flow_gauge.F90; original Fortran authors and license retained.
"""Allocate flow gauges to one or two reference river-map cells.

Load the selected binary map, rank upstream candidates, match the native
7x7 area/location window, then write gauge_alloc.txt. Preserve the reference
5%/10% area rules and the maximum two-cell representation.
"""
from pathlib import Path

import numpy as np

from mod_allocation_map_io import AllocationMap, station_rows
from mod_map_io import parser


def main():
    p = parser(__doc__)
    p.add_argument('gauge_list', type=Path)
    p.add_argument('mode', choices=['multi', 'single'])
    p.add_argument('hires_tag')
    args = p.parse_args()
    maps = AllocationMap(args.map_dir, args.hires_tag)
    out = args.output_dir or Path('.')
    out.mkdir(parents=True, exist_ok=True)
    with (out/'gauge_alloc.txt').open('w') as stream:
        stream.write('        ID       lat       lon  area_Input   area_CaMa       error        diff    Type     ix1   iy1     ix2   iy2       area1       area2\n')
        for f in station_rows(args.gauge_list):
            if not f:
                continue
            identifier = int(f[0])
            lat, lon, area = map(np.float32, f[1:4])
            g = maps.grid
            if lon < g.west or lon > g.east or lat < g.south or lat > g.north:
                continue
            pixel = maps.best_pixel(lat, lon, area)
            cell = maps.assigned_cell(pixel) if pixel is not None else None
            selected, total, snum = [], np.float32(-999), -9
            if cell is not None:
                selected = [cell]
                total = maps.base['uparea'][cell]
                error = np.float32((total-area)/area)
                accumulated = np.float32(0)
                snum = 0
                if abs(error) > np.float32(.05):
                    for upstream in maps.upstream_matches(cell, pixel):
                        candidate = maps.base['uparea'][upstream]
                        if candidate < area*np.float32(.1):
                            break
                        value = np.float32(accumulated+candidate)
                        mismatch = np.float32((value-area)/area)
                        if abs(mismatch) < abs(error):
                            if snum == 0:
                                selected = []
                            selected.append(upstream)
                            snum += 1
                            error, accumulated = mismatch, value
                            if snum == 2 or args.mode == 'single' or abs(error) < np.float32(.1):
                                break
                if snum:
                    total = accumulated
                if snum == 0 and (total-area)/area > 1:
                    selected, snum = [], -9
            if not selected:
                values = [-999., -999., -999.]
                indices = [-999]*4
                areas = [-999., -999.]
            else:
                values = [total, np.float32((total-area)/area), np.float32(total-area)]
                indices = [selected[0][1]+1, selected[0][0]+1, -999, -999]
                areas = [maps.base['uparea'][selected[0]], -999.]
                if len(selected) == 2:
                    indices[2:] = [selected[1][1]+1, selected[1][0]+1]
                    areas[1] = maps.base['uparea'][selected[1]]
            stream.write(f'{identifier:10d}{lat:10.3f}{lon:10.3f}'
                         + ''.join(f'{v:12.2f}' for v in [area, *values])+f'{snum:8d}'
                         + f'{indices[0]:8d}{indices[1]:6d}{indices[2]:8d}{indices[3]:6d}'
                         + ''.join(f'{v:12.1f}' for v in areas)+'\n')


if __name__ == '__main__':
    main()

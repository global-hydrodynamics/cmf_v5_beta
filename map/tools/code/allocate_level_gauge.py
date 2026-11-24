# SPDX-License-Identifier: Apache-2.0
# Parallel port of allocate_level_gauge.F90; original Fortran authors and license retained.
"""Allocate level gauges and describe native channel position and distances.

Match the reference 7x7 area/location window, trace the selected outlet and
ranked upstream channels, and write gauge_alloc.txt with elevations and km.
"""
from pathlib import Path

import numpy as np

from mod_allocation_map_io import AllocationMap, station_rows
from mod_map_io import parser


def main():
    p = parser(__doc__)
    p.add_argument('gauge_list', type=Path)
    p.add_argument('hires_tag')
    args = p.parse_args()
    maps = AllocationMap(args.map_dir, args.hires_tag, extra=('elevtn',), elevation=True)
    out = args.output_dir or Path('.')
    out.mkdir(parents=True, exist_ok=True)
    with (out/'gauge_alloc.txt').open('x') as stream:
        stream.write('        ID       lat       lon        area    Type     ix1   iy1     ix2   iy2  elv_outlet   elv_gauge    elv_upst  dst_outlet    dst_upst     upa_outlet\n')
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
            kind, indices, values, upstream_area = -9, [-999]*4, [-999.]*5, -999.
            if cell is not None:
                kind = 3
                indices = [cell[1]+1, cell[0]+1, -999, -999]
                outlet = tuple(maps.outlets[cell])
                if outlet[0] < 0:
                    raise ValueError('Selected cell has no native outlet')
                distance = np.float32(0)
                current = pixel
                for current in maps.trace(pixel, cell):
                    if current == outlet:
                        break
                    following = maps.next_pixel(current)
                    distance = np.float32(distance+maps.distance(current, following))
                values = [maps.base['elevtn'][cell], maps.hires['elevtn'][pixel], -999., distance, -999.]
                for rank, upstream in enumerate(maps.upstreams[cell[0]*g.nx+cell[1]]):
                    previous = tuple(maps.outlets[upstream])
                    current = maps.next_pixel(previous)
                    distance = maps.distance(previous, current)
                    found = False
                    for current in maps.trace(current, cell):
                        if current == pixel:
                            found = True
                            break
                        following = maps.next_pixel(current)
                        distance = np.float32(distance+maps.distance(current, following))
                    if found:
                        kind = 1 if rank == 0 else 2
                        indices[2:] = [upstream[1]+1, upstream[0]+1]
                        values[2], values[4] = maps.base['elevtn'][upstream], distance
                        break
                upstream_area = maps.base['uparea'][cell]
            stream.write(f'{identifier:10d}{lat:10.3f}{lon:10.3f}{area:12.1f}{kind:8d}'
                         + f'{indices[0]:8d}{indices[1]:6d}{indices[2]:8d}{indices[3]:6d}'
                         + ''.join(f'{v:12.2f}' for v in values)+f'{upstream_area:15.2f}\n')


if __name__ == '__main__':
    main()

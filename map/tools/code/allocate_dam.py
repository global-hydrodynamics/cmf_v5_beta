# SPDX-License-Identifier: Apache-2.0
# Parallel port of allocate_dam.F90; original Fortran authors and license retained.
"""Allocate dams to reference river cells or classify them as subgrid dams.

Use native high-resolution matching, upstream single-cell substitution, and
the original 0.3*ctmare small-dam rule. Write separate river/small/error lists.
"""
import csv
from contextlib import ExitStack
from pathlib import Path

import numpy as np

from mod_allocation_map_io import AllocationMap, station_rows
from mod_map_io import input_path, parser


def main():
    p = parser(__doc__)
    p.add_argument('dam_list', type=Path)
    p.add_argument('hires_tag')
    args = p.parse_args()
    #*** 1. Read dam records and reference/high-resolution map data
    input_path_resolved = args.dam_list.resolve()
    maps = AllocationMap(args.map_dir, args.hires_tag, extra=('ctmare',), map_format=args.map_format)
    print('Inputs:')
    print(f'  Dam records: {input_path_resolved}')
    names = ('nextxy', 'uparea', 'ctmare')
    for name in names:
        print(f'  Base {name}: {input_path(args.map_dir/(name + ".bin")).resolve()}')
    highres_dir = args.map_dir/'binary'/args.hires_tag if args.map_format == 'binary' else args.map_dir/args.hires_tag
    location = highres_dir/('location.txt' if args.map_format == 'binary' else 'location.csv')
    print(f'  High-resolution metadata: {location.resolve()}')
    for name in ('uparea', 'catmxy', 'downxy'):
        source = highres_dir/(args.hires_tag+'.'+name+'.bin')
        print(f'  High-resolution {name}: {input_path(source).resolve()}')
    print(f'Parameters: high-resolution map={args.hires_tag}; native match window=7x7; small-dam threshold=0.3*unit-catchment area; area tolerance=20%.')

    #*** 2. Allocate dams to river, small-dam, or error records
    catchment_area = np.array(maps.base['ctmare'], copy=True)
    catchment_area[catchment_area > 0] *= np.float32(1e-6)
    out = args.output_dir or Path('.')
    out.mkdir(parents=True, exist_ok=True)
    destinations = [out/f'GRanD_{kind}.csv' for kind in ('river', 'small', 'error')]
    with ExitStack() as stack:
        writers = {}
        for kind, destination in zip(('river', 'small', 'error'), destinations):
            stream = stack.enter_context(destination.open(
                'w', newline='', encoding='utf-8'))
            writer = csv.writer(stream, lineterminator='\n')
            writer.writerow(('ID', 'lat', 'lon', 'area_CaMa', 'area_Input', 'error', 'diff',
                             'ix', 'iy', 'cap_mcm', 'year', 'damname', 'rivname'))
            writers[kind] = writer
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
            writers[kind].writerow([identifier, f'{lat:.3f}', f'{lon:.3f}',
                                    *(f'{value:.1f}' for value in
                                      [total, area, error, difference]), ix, iy,
                                    f'{capacity:.1f}', year, damname[:30].strip(),
                                    rivname[:30].strip()])
    print('Output files:')
    for destination in destinations:
        print(f'  {destination.resolve()}')


if __name__ == '__main__':
    main()

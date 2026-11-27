# SPDX-License-Identifier: Apache-2.0
# Parallel port of region_cut_bifway.F90; original Fortran authors and license retained.
"""Crop original bifurcation paths using the existing dim_change contract.

Translate endpoints, retain the reference strict interior-cell condition and
edge-masked river domain, then write regional bifori.csv in source path order.
Source path IDs and optional FLOW columns are preserved. The last row/column
exclusion is intentional reference behavior.
"""
from pathlib import Path

try:
    from .mod_map_io import Grid, input_path, output_root, parser
    from .mod_bifori_csv import crop_bifori_records, read_bifori_csv, write_bifori_csv
except ImportError:  # Direct execution from maintained Shell workflows.
    from mod_map_io import Grid, input_path, output_root, parser
    from mod_bifori_csv import crop_bifori_records, read_bifori_csv, write_bifori_csv


def main():
    p = parser(__doc__)
    p.add_argument('--change-info', type=Path, default=Path('dim_change.txt'))
    args = p.parse_args()
    #*** 1. Read regional crop contract and source bifurcation pathways
    change_path = args.change_info.resolve()
    lines = change_path.read_text().splitlines()
    source = Path(lines[0].strip())
    nx, ny, dx, dy = (int(lines[i].split()[0]) for i in (9, 10, 11, 12))
    grid = Grid.read(args.map_dir)
    nextxy_path = input_path(args.map_dir/'nextxy_noedge.bin')
    source_path = source/'bifori.csv'
    nextx = grid.raster(nextxy_path, '<i4', 2)[0]
    bifori = read_bifori_csv(source_path)
    print('Inputs:')
    print(f'  Regional crop contract: {change_path}')
    print(f'  Edge-masked topology: {nextxy_path.resolve()}')
    print(f'  Source bifurcation pathways: {source_path.resolve()}')
    print(f'Parameters: crop offset=({dx}, {dy}); dimensions={nx} x {ny}; endpoints on the strict outer boundary are excluded by the reference rule.')

    #*** 2. Filter and translate pathways for the regional map
    selected = crop_bifori_records(bifori.rows, nextx, nx, ny, dx, dy)
    out = output_root(args)
    destination = out/'bifori.csv'
    write_bifori_csv(destination, bifori.fields, selected)
    print(f'Bifurcation pathways retained: {len(selected)} of {len(bifori.rows)}')
    print(f'Output: {destination.resolve()}')


if __name__ == '__main__':
    main()

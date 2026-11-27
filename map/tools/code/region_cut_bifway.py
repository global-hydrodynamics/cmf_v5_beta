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
    from .mod_map_io import Grid, output_root, parser
    from .mod_bifori_csv import crop_bifori_records, read_bifori_csv, write_bifori_csv
except ImportError:  # Direct execution from maintained Shell workflows.
    from mod_map_io import Grid, output_root, parser
    from mod_bifori_csv import crop_bifori_records, read_bifori_csv, write_bifori_csv


def main():
    p = parser(__doc__)
    p.add_argument('--change-info', type=Path, default=Path('dim_change.txt'))
    args = p.parse_args()
    lines = args.change_info.read_text().splitlines()
    source = Path(lines[0].strip())
    nx, ny, dx, dy = (int(lines[i].split()[0]) for i in (9, 10, 11, 12))
    nextx = Grid.read(args.map_dir).raster(args.map_dir/'nextxy_noedge.bin', '<i4', 2)[0]
    bifori = read_bifori_csv(source/'bifori.csv')
    selected = crop_bifori_records(bifori.rows, nextx, nx, ny, dx, dy)
    out = output_root(args)
    write_bifori_csv(out/'bifori.csv', bifori.fields, selected)


if __name__ == '__main__':
    main()

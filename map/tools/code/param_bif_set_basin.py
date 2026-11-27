# SPDX-License-Identifier: Apache-2.0
# Parallel port of param_bif_set_basin.F90; original Fortran authors and license retained.
"""Merge every potential inter-basin channel/overland link, as in Fortran.

Unlike MPI-specific aggregation there is no size threshold and no path sort.
Channel commits ascend in basin ID; overland commits descend. Output basin IDs
retain the smallest numeric representative, not the hydrologically largest basin.
"""
from mod_bifprm_csv import read_bifprm_csv
from mod_map_color import color_map
from mod_map_io import Grid, input_path, output_root, parser, write_raster
from param_mpi_set_basin import diagnostic, merge_basins


def main():
    p = parser(__doc__)
    p.add_argument(
        '--check-map',
        action='store_true',
        help='Generate optional diagnostic maps.',
    )
    args = p.parse_args()
    #*** 1. Read basin and bifurcation input
    grid = Grid.read(args.map_dir)
    nextxy_path = input_path(args.map_dir / 'nextxy.bin')
    basin_path = input_path(args.map_dir / 'basin.bin')
    bifprm_path = (args.map_dir / 'bifprm.csv').resolve()
    # The reference also requires nextxy, even though merging uses path endpoints.
    grid.raster(nextxy_path, '<i4', 2)
    original = grid.raster(basin_path, '<i4')
    paths = read_bifprm_csv(bifprm_path)
    print('Inputs:')
    print(f'  River topology: {nextxy_path.resolve()}')
    print(f'  Basin IDs: {basin_path.resolve()}')
    print(f'  Bifurcation parameters: {bifprm_path}')
    print(f'Parameters: pathways={len(paths)}; basin diagnostics={"enabled" if args.check_map else "disabled"}.')
    print('Calculation: merge all eligible channel and overland pathways in the reference channel/overland ordering.')

    #*** 2. Merge channel and overland bifurcation basins
    basin = merge_basins(original,paths,None,sort_paths=False)
    out = output_root(args)
    #*** 3. Write basin identifiers and display colors
    written = [write_raster(out/'bifbsn.bin', basin, '<i4', grid=grid),
               write_raster(out/'bifcol.bin', color_map(basin,grid.west,grid.east), '<i4',grid=grid)]
    if args.check_map:
        written.append(write_raster(out/'check_bif_bsnmod.bin',diagnostic(original,basin,paths),'<i4',grid=grid))
    print('Output files:')
    for path in written:
        print(f'  {path.resolve()}')


if __name__ == '__main__':
    main()

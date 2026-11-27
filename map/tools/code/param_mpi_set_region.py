# SPDX-License-Identifier: Apache-2.0
# Parallel port of param_mpi_set_region.F90; original Fortran authors and license retained.
"""Greedily assign aggregated basins to MPI regions, preserving Fortran ties.

Read the temporary aggregated basin map and params; visit positive basins in ascending ID,
assign each to the lowest-index least-loaded partition, and write mpireg-N.bin.
"""
import numpy as np

from mod_map_io import Grid, output_root, parser, write_raster


def assign_regions(basin, count):
    """Balance cell counts, deliberately without sorting basins by size."""
    highest = int(basin.max())
    if highest < 1 or count < 1:
        raise ValueError('positive basin and region counts required')
    sizes = np.bincount(basin[basin > 0], minlength=highest + 1)
    loads = np.zeros(count, dtype=np.int32)
    assignments = np.zeros(highest + 1, dtype=np.int32)
    for group in range(1, highest + 1):
        if sizes[group] == 0:
            continue
        region = int(loads.argmin())
        assignments[group] = region + 1
        loads[region] += sizes[group]
    result = np.full(basin.shape, -9999, dtype=np.int32)
    valid = basin > 0
    result[valid] = assignments[basin[valid]]
    return result, loads


def main():
    p = parser(__doc__)
    p.add_argument('count', type=int)
    args = p.parse_args()
    grid = Grid.read(args.map_dir)
    basin_path = (args.map_dir/'bifbsn_mpi.bin' if args.map_format == 'netcdf'
                  else output_root(args)/'bifbsn_mpi.tmp')
    basin = grid.raster(basin_path, '<i4')
    regions, loads = assign_regions(basin, args.count)
    path = output_root(args) / f'mpireg-{args.count}.bin'
    write_raster(path, regions, '<i4', grid=grid)
    print(f'Created {path}')
    for region, load in enumerate(loads, 1):
        print(f'  region {region}: {load} river cells')


if __name__ == '__main__':
    main()

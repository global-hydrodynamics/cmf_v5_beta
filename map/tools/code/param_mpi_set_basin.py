# SPDX-License-Identifier: Apache-2.0
# Parallel port of param_mpi_set_basin.F90; original Fortran authors and license retained.
"""MPI-specific basin merging with reference ordering and size thresholds.

Read named bifprm.csv and basin map; sort by original basin IDs/elevation and
legacy whole-line fallback. Commit channel links ascending, floodplain links
descending, iterating each stage to convergence. No production workflow switch.
"""
import numpy as np

from mod_bifprm_csv import read_bifprm_csv
from mod_map_color import color_map
from mod_map_io import Grid, output_root, parser, write_raster


def merge_basins(original, paths, rate, sort_paths=True):
    """Preserve the reference candidate-link and count-update order."""
    basin = np.array(original, dtype=np.int32)
    highest = int(basin.max())
    if highest < 1:
        raise ValueError('no positive basin IDs')
    counts = np.bincount(basin[basin > 0], minlength=highest + 1).astype(np.int32)
    total = int(counts.sum())
    combined = np.inf if rate is None else int(np.float32(total) * np.float32(rate))
    small = int(np.float32(total) * np.float32(.001))
    rows = sorted(paths, key=lambda p:(p['ibsn'],p['jbsn'],p['elevtn'],p['sort_line'])) if sort_paths else paths
    def pair(path):
        return sorted((int(basin[path['iy']-1,path['ix']-1]), int(basin[path['jy']-1,path['jx']-1])))
    def eligible(a, b):
        return a > 0 and a != b and (counts[a]+counts[b] < combined or counts[a] < small or counts[b] < small)
    for reverse in (False, True):
        active = (rows[::-1] if sort_paths else rows) if reverse else [p for p in rows if p['widths'][0] > 0]
        for iteration in range(highest + 2):
            links = np.full(highest + 1, -9999, dtype=np.int32)
            for path in active:
                a, b = pair(path)
                if eligible(a,b) and (links[b] == -9999 or links[b] > a):
                    links[b] = a
            order = range(highest,0,-1) if reverse else range(1,highest+1)
            for group in order:
                if links[group] == -9999:
                    continue
                target = int(links[group])
                while links[target] > 0:
                    target = int(links[target])
                if counts[group]+counts[target] < combined or counts[group] < small or counts[target] < small:
                    links[group] = target
                    counts[target] += counts[group]
                    counts[group] = 0
                else:
                    links[group] = -9999
            valid = basin > 0
            ids = basin[valid]
            basin[valid] = np.where(links[ids] != -9999, links[ids], ids)
            if not any(eligible(*pair(p)) for p in active):
                break
        else:
            raise ValueError('basin aggregation did not converge')
    return basin


def diagnostic(original, basin, paths):
    """Two legacy records: original-basin size change and endpoint merge classes."""
    highest = int(original.max())
    before = np.bincount(original[original>0], minlength=highest+1)
    after = np.bincount(basin[basin>0], minlength=highest+1)
    change = np.full(basin.shape,-9999,dtype=np.int32)
    valid = original > 0
    ids = original[valid]
    change[valid] = np.where(after[ids] > before[ids],2,np.where(after[ids] == 0,1,0))
    endpoint = np.full(basin.shape,-9999,dtype=np.int32)
    for p in paths:
        a=(p['iy']-1,p['ix']-1);b=(p['jy']-1,p['jx']-1)
        if original[a] == original[b]:
            continue
        value = (3 if p['widths'][0] > 0 else 2) if basin[a] == basin[b] else 1
        endpoint[a]=max(value,endpoint[a]);endpoint[b]=max(value,endpoint[b])
    return np.stack((change,endpoint))


def main():
    p = parser(__doc__)
    p.add_argument('mode',nargs='?',choices=['normal','MaxMPI'],default='normal')
    p.add_argument('check',nargs='?',choices=['check_map'])
    args = p.parse_args()
    grid = Grid.read(args.map_dir / 'params.txt')
    original = grid.raster(args.map_dir / 'basin.bin','<i4')
    paths = read_bifprm_csv(args.map_dir / 'bifprm.csv')
    for row in paths:
        if not (1<=row['ix']<=grid.nx and 1<=row['jx']<=grid.nx and 1<=row['iy']<=grid.ny and 1<=row['jy']<=grid.ny):
            p.error('path endpoint outside map')
    basin = merge_basins(original,paths,.03 if args.mode=='MaxMPI' else .06)
    out = output_root(args)
    write_raster(out/'bifcol_mpi.bin',color_map(basin,grid.west,grid.east),'<i4')
    if args.check:
        write_raster(out/'check_bif_bsnmod_mpi.bin',diagnostic(original,basin,paths),'<i4')
    write_raster(out/'bifbsn_mpi.tmp',basin,'<i4')


if __name__ == '__main__':
    main()

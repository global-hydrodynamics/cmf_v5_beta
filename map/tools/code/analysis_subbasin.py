# SPDX-License-Identifier: Apache-2.0
# Parallel port of analysis_subbasin.F90; original Fortran authors and license retained.
"""Experimental two-stage drainage-area-jump segmentation, matching Fortran.

Cut links only when source area exceeds the stage threshold AND the downstream
area exceeds source+threshold. Stage two only relabels stage-one zero cells.
IDs follow north-first, x-fastest terminal scan; no size-based reordering.
"""
from pathlib import Path

import numpy as np

from mod_map_color import color_map
from mod_map_io import Grid, output_root, parser, write_raster


def propagate_labels(nextxy, labels):
    """Memoize each unassigned path's first downstream label in reference order."""
    ny, nx = labels.shape
    for row, col in np.argwhere((nextxy[0] > 0) & (labels == -999)):
        if labels[row, col] != -999:
            continue
        r, c = int(row), int(col)
        path = []
        while nextxy[0, r, c] > 0 and labels[r, c] == -999:
            path.append((r, c))
            if len(path) > nx * ny:
                raise ValueError('cyclic network')
            c, r = int(nextxy[0, r, c]) - 1, int(nextxy[1, r, c]) - 1
        for rr, cc in path:
            labels[rr, cc] = labels[r, c]


def subbasins(nextxy, area_m2, thresholds):
    """Return int32 segments, preserving masks and single-precision cut decisions."""
    nextxy = np.array(nextxy, dtype=np.int32)
    area = np.array(area_m2, dtype=np.float32)
    area[area > 0] *= np.float32(1e-6)
    ny, nx = area.shape
    basin = np.where(nextxy[0] != -9999, -999, -9999).astype(np.int32)
    highest = 0
    for stage, threshold in enumerate(thresholds):
        if stage:
            basin[basin == 0] = -999
        for row, col in np.argwhere(basin == -999):
            x, y = nextxy[:, row, col]
            if not (1 <= x <= nx and 1 <= y <= ny):
                continue
            frozen = stage > 0 and basin[y - 1, x - 1] > 0
            if frozen or (area[row, col] > threshold and area[y - 1, x - 1] > np.float32(area[row, col] + threshold)):
                nextxy[:, row, col] = -9
        for row, col in np.argwhere((basin == -999) & np.isin(nextxy[0], [-9, -10])):
            if area[row, col] >= threshold:
                highest += 1
                basin[row, col] = highest
            else:
                basin[row, col] = 0
        propagate_labels(nextxy, basin)
    return basin


def main():
    p = parser(__doc__)
    p.add_argument('values', nargs='+')
    args = p.parse_args()
    if len(args.values) not in (1, 2, 3, 4):
        p.error('one/two thresholds and optional output-path pair required')
    count = 2 if len(args.values) in (2, 4) else 1
    thresholds = [np.float32(x) for x in args.values[:count]]
    if any(not np.isfinite(x) or x <= 0 for x in thresholds) or count == 2 and thresholds[1] >= thresholds[0]:
        p.error('positive finite thresholds required; second must be smaller')
    grid = Grid.read(args.map_dir / 'params.txt')
    nextxy = grid.raster(args.map_dir / 'nextxy.bin', '<i4', 2)
    area = grid.raster(args.map_dir / 'uparea.bin')
    basin = subbasins(nextxy, area, thresholds)
    colors = color_map(basin, grid.west, grid.east)
    colors[basin == 0] = 0
    if len(args.values) >= 3:
        outputs = [Path(x) for x in args.values[count:]]
    else:
        label = '_'.join(args.values[:count])
        outputs = [output_root(args) / f'analysis_{tag}_{label}.bin' for tag in ('subbsn', 'subcol')]
    write_raster(outputs[0], basin, '<i4', grid=grid)
    write_raster(outputs[1], colors, '<i4', grid=grid)


if __name__ == '__main__':
    main()

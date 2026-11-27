# SPDX-License-Identifier: Apache-2.0
# Parallel port of param_channel_calc_outclm.F90; original Fortran authors and license retained.
"""Route annual-mean runoff to annual-mean channel discharge.

Read DIMINFO, topology and runoff; map local contributions using INPMAT or the
reference integer resolution ratio; accumulate in reference Kahn/BFS order;
write outclm.bin. Runoff is mm/s, overlap areas m2, discharge m3/s.
"""
from pathlib import Path

import numpy as np

from mod_map_io import Grid, input_path, output_root, parser, read_inpmat, write_raster
try:
    from .map_metadata import read_diminfo_nml
except ImportError:  # Direct execution from map-local Shell workflows.
    from map_metadata import read_diminfo_nml


def local_runoff(nextx, area, source, matrix=None):
    """Preserve float32 slot/block summation order and missing-value handling."""
    ny, nx = nextx.shape
    sy, sx = source.shape
    valid = nextx != -9999
    result = np.zeros((ny, nx), dtype='f4')
    missing = np.float32(1e20)
    if matrix is not None:
        xindices, yindices, weights = matrix
        for x, y, weight in zip(xindices, yindices, weights):
            selected = valid & (x > 0)
            if np.any(selected & ((x > sx) | (y < 1) | (y > sy))):
                raise ValueError('INPMAT index outside runoff grid')
            row, col = np.nonzero(selected)
            values = source[y[selected]-1, x[selected]-1]
            keep = values != missing
            result[row[keep], col[keep]] += np.maximum(values[keep], np.float32(0))*weight[selected][keep]*np.float32(.001)
    elif nx >= sx:
        ratio = nx//sx
        if nx != sx*ratio or ny != sy*ratio:
            raise ValueError('Nearest mode reference leaves cells undefined for nonintegral grid ratios')
        result[:] = np.repeat(np.repeat(np.where(source == missing, 0, np.maximum(source, 0)), ratio, 0), ratio, 1)
        result[~valid] = 0
        result[valid] = result[valid]*area[valid]*np.float32(.001)
    else:
        ratio = sx//nx
        if sx != nx*ratio or sy != ny*ratio:
            raise ValueError('Nearest mode requires a matching integer resolution ratio')
        count = np.zeros((ny, nx), dtype='i4')
        for dy in range(ratio):
            for dx in range(ratio):
                values = source[dy::ratio, dx::ratio]
                keep = valid & (values != missing)
                result[keep] += np.maximum(values[keep], np.float32(0))
                count[keep] += 1
        with np.errstate(invalid='ignore', divide='ignore'):
            result[valid] /= count[valid].astype('f4')
        result[valid] = result[valid]*area[valid]*np.float32(.001)
    return result


def route(nextxy, runoff):
    """Use the same row-major seed order and breadth-first registration order."""
    nx = nextxy.shape[2]
    first, second = nextxy.reshape(2, -1)
    downstream = np.full(first.size, -1, dtype='i8')
    linked = first > 0
    downstream[linked] = (second[linked].astype('i8')-1)*nx+first[linked]-1
    if np.any((downstream[linked] < 0) | (downstream[linked] >= first.size)):
        raise ValueError('Invalid downstream index')
    counts = np.bincount(downstream[linked], minlength=first.size)
    counts[first == -9999] = -9999
    sequence = np.flatnonzero(counts == 0).tolist()
    seen = np.zeros(first.size, dtype='i4')
    discharge = np.zeros(first.size, dtype='f4')
    for cell in sequence:
        discharge[cell] += runoff.ravel()[cell]
        target = downstream[cell]
        if target >= 0:
            discharge[target] += discharge[cell]
            seen[target] += 1
            if seen[target] == counts[target]:
                sequence.append(int(target))
    discharge[first == -9999] = -9999
    return discharge.reshape(runoff.shape)


def main():
    p = parser(__doc__, map_default='.', map_binary_flag=True)
    p.add_argument('diminfo', type=Path)
    p.add_argument('runoff', type=Path)
    p.add_argument('--runoff-binary', action='store_true', help='Read legacy float32 Binary runoff instead of the default NetCDF runoff.')
    p.add_argument('--interp-near', action='store_true', help='Use nearest-grid runoff interpolation instead of the default input matrix.')
    args = p.parse_args()
    if args.runoff_binary and args.runoff.suffix.lower() == '.nc':
        p.error('--runoff-binary cannot be used with a NetCDF (.nc) input path')
    if not args.runoff_binary and args.runoff.suffix.lower() in {'.one', '.bin'}:
        p.error('Binary runoff input requires --runoff-binary')
    #*** 1. Read runoff grid metadata and map inputs
    diminfo_path = args.diminfo.resolve()
    runoff_path = args.runoff.resolve()
    info = read_diminfo_nml(diminfo_path)
    nx, ny, nlfp, sx, sy, slots = info.nx, info.ny, info.nlfp, info.nxin, info.nyin, info.inpn
    grid = Grid(nx, ny, nlfp, *[np.float32(0)]*5)
    nextxy_path = input_path(args.map_dir/'nextxy.bin')
    area_path = input_path(args.map_dir/'ctmare.bin')
    nextxy = grid.raster(nextxy_path, '<i4', 2)
    area = grid.raster(area_path)
    if args.runoff_binary:
        source = np.memmap(args.runoff, mode='r', dtype='<f4', shape=(sy, sx))
    else:
        from netCDF4 import Dataset
        with Dataset(args.runoff) as dataset:
            variable = dataset.variables['runoff']
            variable.set_auto_maskandscale(False)
            if variable.ndim not in (2, 3):
                raise ValueError('Runoff must have (lat,lon) or (time,lat,lon) dimensions')
            source = np.asarray(variable[0] if variable.ndim == 3 else variable[:], dtype='f4')
            if source.shape != (sy, sx):
                raise ValueError('Runoff dimensions do not match DIMINFO')
    matrix = None
    if not args.interp_near:
        matrix_path = Path(info.inpmat_file)
        if not matrix_path.is_absolute():
            matrix_path = args.map_dir/matrix_path
        matrix_path = matrix_path.resolve()
        matrix = read_inpmat(matrix_path, nx, ny, slots)
    print('Inputs:')
    print(f'  DIMINFO: {diminfo_path}')
    print(f'  River topology: {nextxy_path.resolve()}')
    print(f'  Catchment area: {area_path.resolve()}')
    print(f'  Annual-mean runoff: {runoff_path}')
    print(f'Grid sizes: river map={nx} x {ny}; runoff input={sx} x {sy}; input-matrix slots={slots}.')
    if matrix is not None:
        print(f'  Input matrix: {matrix_path}')

    #*** 2. Map local runoff and route discharge downstream
    if matrix is not None:
        print('Calculation: local discharge contribution = max(runoff, 0) [mm/s] * INPMAT area weight [m2] * 0.001; then accumulate downstream in network order.')
    else:
        print('Calculation: apply the reference integer-ratio nearest-grid mapping, multiply mapped runoff [mm/s] by ctmare [m2] and 0.001, then accumulate downstream.')
    print('Missing runoff values are excluded; negative runoff is clipped to zero.')
    output_grid = Grid.from_file(args.map_dir)
    discharge = route(nextxy, local_runoff(nextxy[0], area, source, matrix))

    #*** 3. Write annual-mean discharge
    destination = write_raster(output_root(args)/'outclm.bin', discharge, '<f4', grid=output_grid)
    print(f'Output: annual-mean discharge [m3/s]: {destination.resolve()}')


if __name__ == '__main__':
    main()

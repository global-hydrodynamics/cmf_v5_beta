# SPDX-License-Identifier: Apache-2.0
# Parallel port of region_cut_domain.F90; original Fortran authors and license retained.
"""Crop a regional binary map, retaining reference edge masking and snapping.

Read region_info.txt, snap requested bounds using the Fortran search windows,
translate connectivity and copy field records, then generate nextxy_noedge.
Geometry uses double precision here, as in region_cut_domain.F90.
"""
from pathlib import Path

import numpy as np

try:
    from .map_metadata import MapGeometry, read_map_geometry, write_toml
except ImportError:  # Direct execution from the map-local Shell workflows.
    from map_metadata import MapGeometry, read_map_geometry, write_toml
from mod_map_io import Grid, output_root, parser, write_raster


def snap_bounds(requested, nx, ny, size, west, north):
    """Apply the asymmetric reference boundary search, with first-hit ties."""
    w, e, s, n = requested
    x = west+np.arange(nx)*size
    y = north-np.arange(ny)*size
    result = []
    for position, (value, centers, low, high, shift) in enumerate([
        (w, x, -.1, 1.1, 0), (e, x, -.1, 1.1, size),
        (s, y, -1.1, .1, -size), (n, y, -1.1, .1, 0)]):
        if position in (0, 2):
            eligible = (value >= centers+low*size) & (value < centers+high*size)
        else:
            eligible = (value > centers+low*size) & (value <= centers+high*size)
        choices = centers[eligible]+shift
        if not choices.size:
            raise ValueError('Requested edge outside source snapping window')
        selected = choices[np.argmin(abs(value-choices))]
        result.append(value if abs(selected-value) < .001 else selected)
    return result


def edge_mask(nextxy):
    """Follow all paths connected to the outer two-cell border, in row order."""
    ny, nx = nextxy.shape[1:]
    state = np.where(nextxy[0] == -9999, -9, 0)
    state[(nextxy[0] == -9) | (nextxy[0] == -10)] = 10
    for iy in range(ny):
        for ix in range(nx):
            if nextxy[0, iy, ix] == -9999 or not (ix < 2 or ix >= nx-2 or iy < 2 or iy >= ny-2):
                continue
            x, y = ix, iy
            while state[y, x] == 0 and nextxy[0, y, x] > 0:
                state[y, x] = 20
                x, y = int(nextxy[0, y, x])-1, int(nextxy[1, y, x])-1
            state[y, x] = 20
    for iy in range(ny):
        for ix in range(nx):
            if nextxy[0, iy, ix] <= 0 or state[iy, ix] != 0:
                continue
            path = []
            x, y = ix, iy
            while state[y, x] == 0:
                path.append((y, x))
                x, y = int(nextxy[0, y, x])-1, int(nextxy[1, y, x])-1
                if len(path) > nx*ny:
                    raise ValueError('Cyclic network: reference traversal would not terminate')
            for row, col in path:
                state[row, col] = state[y, x]
    result = nextxy.copy()
    result[:, state == 20] = -9999
    return result


def main():
    p = parser(__doc__)
    p.add_argument('--region-info', type=Path, default=Path('region_info.txt'))
    p.add_argument('--change-info', type=Path, default=Path('dim_change.txt'))
    args = p.parse_args()
    lines = args.region_info.read_text().splitlines()
    source = Path(lines[0].strip())
    source_geometry = read_map_geometry(source)
    nx, ny, nlfp = source_geometry.nx, source_geometry.ny, source_geometry.nlfp
    size = source_geometry.resolution
    sw, se, ss, sn = source_geometry.west, source_geometry.east, source_geometry.south, source_geometry.north
    requested = [float(line.split()[0]) for line in lines[1:5]]
    west, east, south, north = snap_bounds(requested, nx, ny, size, sw, sn)
    mx, my, dx, dy = [int(np.floor(v+.5)) for v in
                      ((east-west)/size, (north-south)/size, (west-sw)/size, (sn-north)/size)]
    if dx < 0 or dy < 0 or dx+mx > nx or dy+my > ny:
        raise ValueError('Regional crop outside source dimensions')
    out = output_root(args)
    out.mkdir(parents=True, exist_ok=True)
    write_toml(out/'params.toml', MapGeometry(mx, my, nlfp, size, west, east, south, north))
    with args.change_info.open('w') as stream:
        stream.write(str(source.resolve())+'/\n')
        for value in (nx, ny, size, sw, se, ss, sn):
            stream.write(str(value)+'\n')
        stream.write('../\n')
        for value in (mx, my, dx, dy, west, east, south, north):
            stream.write(str(value)+'\n')
    # Register source geometry and I/O roots for NetCDF reads and output writes.
    grid = Grid.read(source)
    output_grid = Grid.from_file(out)
    crop = (slice(dy, dy+my), slice(dx, dx+mx))
    nextxy = np.array(grid.raster(source/'nextxy.bin', '<i4', 2)[:, crop[0], crop[1]])
    downxy = np.array(grid.raster(source/'downxy.bin', '<i4', 2)[:, crop[0], crop[1]])
    positive = nextxy[0] > 0
    nextxy[0, positive] -= dx
    nextxy[1, positive] -= dy
    outside = positive & ((nextxy[0] < 1) | (nextxy[0] > mx) | (nextxy[1] < 1) | (nextxy[1] > my))
    nextxy[:, outside] = -10
    downxy[:, outside] = -1000
    valid = nextxy[0] != -9999
    downxy[:, ~valid] = -9999
    write_raster(out/'nextxy.bin', nextxy, '<i4', grid=output_grid)
    write_raster(out/'downxy.bin', downxy, '<i4', grid=output_grid)
    for name, records in [('elevtn', 1), ('fldhgt', nlfp), ('ctmare', 1), ('grdare', 1),
                           ('uparea', 1), ('lonlat', 2), ('nxtdst', 1), ('rivlen', 1), ('width', 1)]:
        data = grid.raster(source/(name+'.bin'), '<f4', records)
        clipped = data[..., crop[0], crop[1]]
        write_raster(out/(name+'.bin'), np.where(valid, clipped, np.float32(-9999)), '<f4', grid=output_grid)
    write_raster(out/'lsmask.bin', valid, '<i4', grid=output_grid)
    for name in ('catmpx', 'class'):
        if (source/(name+'.bin')).is_file():
            write_raster(out/(name+'.bin'), grid.raster(source/(name+'.bin'), '<i4')[crop], '<i4', grid=output_grid)
    write_raster(out/'nextxy_noedge.bin', edge_mask(nextxy), '<i4', grid=output_grid)


if __name__ == '__main__':
    main()

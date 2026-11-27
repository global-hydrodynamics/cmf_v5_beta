# SPDX-License-Identifier: Apache-2.0
# Parallel port of analysis_river_node_latlon.F90; original Fortran authors and license retained.
"""Print directed outlet links intersecting a requested geographic rectangle.

Use stored lonlat rather than cell centers. Include a link when either endpoint
is in the inclusive rectangle. Terminal -9/-10 links have destination -999.
Read-only inputs follow the original ../ map-root convention.
"""
import numpy as np

from mod_map_io import Grid, parser


def main():
    p = parser(__doc__)
    for name in ('west', 'east', 'south', 'north'):
        p.add_argument(name, type=np.float32)
    args = p.parse_args()
    grid = Grid.read(args.map_dir)
    nextxy = grid.raster(args.map_dir / 'nextxy.bin', '<i4', 2)
    uparea = grid.raster(args.map_dir / 'uparea.bin')
    elevtn = grid.raster(args.map_dir / 'elevtn.bin')
    lonlat = grid.raster(args.map_dir / 'lonlat.bin', '<f4', 2)
    print('ix(Fort), iy(Fort),   ori-lat, ori-lon,   dst-lat, dst-lon,   uparea,   elevtn')
    for row, col in np.argwhere((nextxy[0] > 0) | (nextxy[0] == -9) | (nextxy[0] == -10)):
        olon, olat = lonlat[:, row, col]
        if nextxy[0, row, col] > 0:
            c, r = nextxy[:, row, col] - 1
            dlon, dlat = lonlat[:, r, c]
        else:
            dlon = dlat = np.float32(-999)
        inside = lambda x, y: args.west <= x <= args.east and args.south <= y <= args.north
        if inside(olon, olat) or (nextxy[0, row, col] > 0 and inside(dlon, dlat)):
            area = np.float32(uparea[row, col] * np.float32(1e-6))
            print(f'{col+1:8d}{row+1:8d}{olat:12.3f}{olon:12.3f}  {dlat:12.3f}{dlon:12.3f}{area:12.1f}{elevtn[row,col]:8.1f}')


if __name__ == '__main__':
    main()

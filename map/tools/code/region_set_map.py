# SPDX-License-Identifier: Apache-2.0
# Parallel port of region_set_map.F90; original Fortran authors and license retained.
"""Derive regional river sequence, upstream grid properties and basin colors.

Read nextxy and grdare, traverse the directed network, sort basins with the
reference heap tie rules, and write seven derived maps in the selected format. Upstream
area reduction may differ by float32 rounding; basin IDs and colors retain
reference ordering. Existing scientific input maps are never overwritten.
"""
import numpy as np

from mod_allocation_map_io import link_distance
from mod_map_color import color_map
from mod_map_io import Grid, input_path, output_root, parser, write_raster


def heap_order(values):
    """Reference ascending heap sort, including asymmetric equal-child ties."""
    a = [0]+list(values)
    b = list(range(len(a)))
    count = len(values)
    def swap(i, j):
        a[i], a[j] = a[j], a[i]
        b[i], b[j] = b[j], b[i]
    for root in range(count//2, 0, -1):
        i = root
        while 2*i <= count:
            child = 2*i
            if child+1 <= count:
                if a[i] >= a[child] and a[i] >= a[child+1]:
                    break
                if a[child] <= a[child+1]:
                    child += 1
            elif a[child] <= a[i]:
                break
            swap(i, child)
            i = child
    for end in range(count, 0, -1):
        swap(1, end)
        i = 1
        while 2*i < end:
            child = 2*i
            if child+1 < end and a[child+1] > a[child]:
                child += 1
            if a[child] <= a[i]:
                break
            swap(i, child)
            i = child
    return b[1:]


def derive(grid, nextxy, area):
    """Return sequence/area/count/basin maps using a single topological pass."""
    first, second = nextxy.reshape(2, -1)
    total = first.size
    downstream = np.full(total, -1, dtype='i8')
    linked = first > 0
    downstream[linked] = (second[linked].astype('i8')-1)*grid.nx+first[linked]-1
    if np.any((downstream[linked] < 0) | (downstream[linked] >= total)):
        raise ValueError('Invalid downstream indices')
    incoming = np.bincount(downstream[linked], minlength=total)
    valid = first != -9999
    sequence = np.where(valid, 0, -9999).astype('i4')
    front = np.flatnonzero(valid & (incoming == 0))
    heads = front.copy()
    sequence[front] = 1
    uparea = np.where(valid, area.ravel(), np.float32(-9999)).astype('f4')
    upgrid = np.where(valid, 1, -9999).astype('i4')
    levels = []
    visited = 0
    # Vectorize independent cells in each topological front. Reduction order
    # can differ by float32 rounding, as explicitly allowed by the maintainer.
    while front.size:
        levels.append(front)
        visited += len(front)
        current = front[downstream[front] >= 0]
        targets = downstream[current]
        np.add.at(uparea, targets, uparea[current])
        np.add.at(upgrid, targets, upgrid[current])
        np.maximum.at(sequence, targets, sequence[current]+1)
        np.add.at(incoming, targets, -1)
        front = np.unique(targets[incoming[targets] == 0])
    if np.count_nonzero(valid) != visited:
        raise ValueError('Cyclic or inconsistent network')
    # Resolve each cell's terminal by reversing the same topological fronts.
    # Initial basin numbering still follows the first row-major headwater.
    root = np.full(total, -1, dtype='i8')
    terminals = np.flatnonzero(valid & ~linked)
    root[terminals] = terminals
    for front in reversed(levels):
        current = front[downstream[front] >= 0]
        root[current] = root[downstream[current]]
    head_roots = root[heads]
    _, first = np.unique(head_roots, return_index=True)
    terminal_order = head_roots[np.sort(first)]
    number = len(terminal_order)
    labels = np.zeros(total, dtype='i4')
    labels[terminal_order] = np.arange(1, number+1)
    basin = np.zeros(total, dtype='i4')
    basin[valid] = labels[root[valid]]
    sizes = upgrid[terminal_order]
    remap = np.zeros(number+1, dtype='i4')
    for position, identifier in enumerate(heap_order(sizes)):
        remap[identifier] = number-position
    basin = remap[basin]
    basin[~valid] = -9999
    shape = (grid.ny, grid.nx)
    return [field.reshape(shape) for field in (sequence, uparea, upgrid, basin)]


def main():
    p = parser(__doc__)
    args = p.parse_args()
    #*** 1. Read river topology and grid-cell areas
    grid = Grid.read(args.map_dir)
    topology_path = input_path(args.map_dir/'nextxy.bin')
    area_path = input_path(args.map_dir/'grdare.bin')
    nextxy = grid.raster(topology_path, '<i4', 2)
    area = grid.raster(area_path)
    print('Inputs:')
    print(f'  River topology: {topology_path.resolve()}')
    print(f'  Grid-cell area: {area_path.resolve()}')

    #*** 2. Derive directed-network sequence, upstream summaries, and basin colors
    sequence, upstream, counts, basin = derive(grid, nextxy, area)
    longitude = grid.west+(np.arange(grid.nx, dtype='f4')+np.float32(.5))*grid.size
    latitude = grid.north-(np.arange(grid.ny, dtype='f4')+np.float32(.5))*grid.size
    distance = np.where(nextxy[0] == -9999, np.float32(-9999), np.float32(25000))
    row, col = np.nonzero(nextxy[0] > 0)
    x, y = nextxy[:, row, col]-1
    lon1, lon2 = longitude[col], longitude[x]
    lon2 = np.where((lon1 < -90) & (lon2 > 270), lon2-360, lon2)
    lon2 = np.where((lon1 > 270) & (lon2 < -90), lon2+360, lon2)
    distance[row, col] = link_distance(lon1, latitude[row], lon2, latitude[y])
    fields = [('rivseq', sequence, '<i4'), ('uparea_grid', upstream, '<f4'),
              ('upgrid', counts, '<i4'), ('basin', basin, '<i4'),
              ('nxtdst_grid', distance, '<f4'), ('rivlen_grid', distance, '<f4'),
              ('bsncol', color_map(basin, grid.west, grid.east), '<i4')]
    #*** 3. Write derived map fields
    written = [write_raster(output_root(args)/(name+'.bin'), values, dtype, grid=grid)
               for name, values, dtype in fields]
    print('Output files:')
    for path in written:
        print(f'  {path.resolve()}')


if __name__ == '__main__':
    main()

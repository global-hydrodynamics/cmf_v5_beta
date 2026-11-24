# SPDX-License-Identifier: Apache-2.0
# Parallel port of param_inpmat_generate.F90; original Fortran authors and license retained.
"""Generate sparse runoff-to-catchment overlap weights from binary catmxy.

Read geometry, visit high-resolution tiles and pixels in source order, and
write the established diminfo and X/Y/area binary records. Areas accumulate
in float32 pixel order; integer slots retain first encounter order. No change
to the current Fortran workflow is made by this independent implementation.
"""
from pathlib import Path

import numpy as np

from mod_map_io import Grid, output_root, parser


def pixel_area(size, latitude, legacy_default=False):
    """Reference ellipsoidal approximation, including its mixed precision."""
    scale = np.float32(1 if legacy_default else 10)
    low = np.clip(latitude-np.float32(.5)*scale*size, -90, 90).astype('f4')
    high = np.clip(latitude+np.float32(.5)*scale*size, -90, 90).astype('f4')
    pi = np.float32(np.pi)
    # Fortran multiplies latitude*pi in default REAL before promotion by 180.D0.
    sin_low = np.sin((low*pi).astype('f8')/180.)
    sin_high = np.sin((high*pi).astype('f8')/180.)
    # DATA constants without D exponents are first rounded to default REAL.
    eccentricity = float(np.float32(.00669447))
    dpi = float(np.float32(np.pi))
    first = sin_low*(1+eccentricity*sin_low**2/2)
    second = sin_high*(1+eccentricity*sin_high**2/2)
    area = (dpi*6378136.**2*(1-eccentricity)/180.*(first-second)).astype('f4')
    area = np.abs(area*np.float32(size*scale))
    if not legacy_default:
        area *= np.float32(.01)
    return area


def generate(grid, source, out, size, west, east, north, south, order,
             diminfo, inpmat, legacy_default=False):
    """Accumulate bounded row blocks without changing float32 addition order."""
    nxin = int(np.floor(np.float32((east-west)/size)+np.float32(.5)))
    nyin = int(np.floor(np.float32((north-south)/size)+np.float32(.5)))
    count = np.zeros(grid.nx*grid.ny, dtype='i4')
    xslots = np.zeros((grid.ny*grid.nx, 100), dtype='i4')
    yslots = np.zeros_like(xslots)
    areas = np.zeros(xslots.shape, dtype='f4')
    slots = {}
    lines = (source/'location.txt').read_text().splitlines()
    for line in lines[2:2+int(lines[0].split()[0])]:
        fields = line.split()
        name = fields[1]
        origin_x, origin_y = np.float32(fields[2]), np.float32(fields[5])
        nx, ny = int(fields[6]), int(fields[7])
        resolution = np.float32(fields[8])
        path = source/(name+'.catmxy.bin')
        if not path.is_file():
            continue
        assignments = np.memmap(path, mode='r', dtype='<i2', shape=(2, ny, nx))
        longitude = origin_x+(np.arange(nx, dtype='f4')+np.float32(.5))*resolution
        longitude[longitude >= 180] -= np.float32(360)
        longitude[longitude < -180] += np.float32(360)
        longitude[longitude < west] += np.float32(360)
        longitude[longitude > east] -= np.float32(360)
        latitude = origin_y-(np.arange(ny, dtype='f4')+np.float32(.5))*resolution
        ixin = np.clip(((longitude-west)/size).astype('i4')+1, 1, nxin)
        iyin = np.clip(((north-latitude)/size).astype('i4')+1, 1, nyin)
        if order == 'StoN':
            iyin = nyin-iyin+1
        area_path = source/(name+'.grdare.bin')
        area_map = (np.memmap(area_path, mode='r', dtype='<f4', shape=(ny, nx))
                    if area_path.is_file() else None)
        reference_area = pixel_area(resolution, latitude, legacy_default)
        for start in range(0, ny, 64):
            stop = min(ny, start+64)
            mx, my = assignments[:, start:stop]
            valid = (mx > 0) & (mx <= grid.nx) & (my > 0) & (my <= grid.ny)
            if legacy_default and np.any((mx > 0) & ~valid):
                # The reference would index outside its arrays for this input.
                raise ValueError('Invalid positive catmxy outside the reference array bounds')
            valid &= (longitude >= west)[None, :] & (longitude <= east)[None, :]
            valid &= ((latitude[start:stop] >= south) & (latitude[start:stop] <= north))[:, None]
            row, col = np.nonzero(valid)
            coarse = (my[row, col].astype('i8')-1)*grid.nx+mx[row, col]-1
            source_id = (iyin[start+row].astype('i8')-1)*nxin+ixin[col]-1
            keys = coarse*(nxin*nyin)+source_id
            unique, first, inverse = np.unique(keys, return_index=True, return_inverse=True)
            positions = np.empty(len(unique), dtype='i8')
            for item in np.argsort(first):
                key = int(unique[item])
                cell = key//(nxin*nyin)
                if key not in slots:
                    slot = int(count[cell])
                    if slot == 100:
                        raise ValueError('Reference nmax=100 overflow')
                    slots[key] = cell*100+slot
                    count[cell] += 1
                    xslots[cell, slot] = ixin[col[first[item]]]
                    yslots[cell, slot] = iyin[start+row[first[item]]]
                positions[item] = slots[key]
            if area_map is None:
                weights = reference_area[start+row]
            else:
                weights = np.array(area_map[start+row, col], copy=True)
                weights[weights > 0] *= np.float32(1e6)
            np.add.at(areas.ravel(), positions[inverse], weights)
    maximum = int(count.max())
    if maximum == 0:
        raise ValueError('No valid input-grid overlap; reference has zero-length records')
    out.mkdir(parents=True, exist_ok=True)
    with (out/inpmat).open('xb') as stream:
        for field in (xslots, yslots, areas):
            field[:, :maximum].T.reshape(maximum, grid.ny, grid.nx).tofile(stream)
    descriptor = out/diminfo
    with descriptor.open('x') as stream:
        for value, label in zip([grid.nx, grid.ny, grid.nlfp, nxin, nyin, maximum],
                                ['nXX', 'nYY', 'floodplain layer', 'input nXX ', 'input nYY ', 'input num']):
            stream.write(f'{value:10d}     !! {label}\n')
        stream.write(str(inpmat)+'\n')
        for value, label in [(grid.west, 'west  edge'), (grid.east, 'east  edge'),
                             (grid.north, 'north edge'), (grid.south, 'south edge')]:
            stream.write(f'{value:12.3f}     !! {label}\n')


def main():
    p = parser(__doc__, map_default='.')
    p.add_argument('hires_tag')
    p.add_argument('size', type=np.float32)
    for name, default in [('west', -180), ('east', 180), ('north', 90), ('south', -90)]:
        p.add_argument(name, nargs='?', type=np.float32, default=np.float32(default))
    p.add_argument('order', nargs='?', choices=['NtoS', 'StoN'], default='NtoS')
    p.add_argument('diminfo', type=Path)
    p.add_argument('inpmat', type=Path)
    args = p.parse_args()
    generate(Grid.read(args.map_dir/'params.txt'), args.map_dir/args.hires_tag,
             output_root(args), args.size, args.west, args.east, args.north, args.south,
             args.order, args.diminfo, args.inpmat)


if __name__ == '__main__':
    main()

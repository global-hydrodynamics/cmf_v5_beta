# SPDX-License-Identifier: Apache-2.0
# Parallel port of region_combine_hires.F90; original Fortran authors and license retained.
"""Combine/crop high-resolution map tiles with bounded working memory.

Read dim_change and source locations, translate stored catchment assignments,
and copy field blocks to independent outputs. Preserve the reference's two
branches: combined arrays for small regions, whole named tiles for large ones.
catmzz/catmz100 are int8 in this reference contract, not inferred from values.
"""
from pathlib import Path

import numpy as np

from mod_map_io import RasterTile, output_root, parser, write_highres_raster


PIXELS_PER_DEGREE = {'1min': 60, '30sec': 120, '15sec': 240, '5sec': 720, '3sec': 1200, '1sec': 3600}
# This is the legacy program's binary contract, not a new variable registry.
LAYERS = [('catmxy', '<i2', 2, -9999), ('catmzz', 'i1', 1, -9), ('catmz100', 'i1', 1, -9),
          ('flddif', '<f4', 1, -9999), ('grdare', '<f4', 1, -9999), ('hand', '<f4', 1, -9999),
          ('elevtn', '<f4', 1, -9999), ('uparea', '<f4', 1, -9999), ('rivwth', '<f4', 1, -9999),
          ('visual', 'i1', 1, -9), ('downxy', '<i2', 2, -9999), ('flwdir', 'i1', 1, -9)]


def source_array(path, dtype, records, ny, nx):
    return RasterTile(path, dtype, records, (ny, nx), optional=True)


def scratch_path_for(destination, netcdf):
    return destination.with_suffix(destination.suffix + '.tmp') if netcdf else destination


def translated(assignments, dx, dy, mx, my, tiled=False):
    """Keep the reference branch-specific positive/special-code test."""
    result = np.array(assignments, copy=True)
    change = result[0] > (-100 if tiled else 0)
    result[0, change] -= dx
    result[1, change] -= dy
    invalid = change & ((result[0] < 1) | (result[0] > mx) | (result[1] < 1) | (result[1] > my))
    result[:, invalid] = -999
    return result


def copy_native_tile(source, out, tag, region, offsets, coarse_shape, netcdf=False):
    """Copy contiguous whole-tile blocks; only catmxy requires a transform."""
    name, _, _, _, _, nx, ny = region
    dx, dy = offsets
    mx, my = coarse_shape
    for layer, dtype, records, missing in LAYERS:
        if layer == 'grdare':
            continue  # The reference tiled branch never writes this layer.
        values = source_array(source/(name+'.'+layer+'.bin'), dtype, records, ny, nx)
        destination = out/(tag+'.'+layer+'.bin')
        scratch = scratch_path_for(destination, netcdf)
        with scratch.open('wb') as stream:
            stream.truncate(records*ny*nx*np.dtype(dtype).itemsize)
        target = np.memmap(scratch, mode='r+', dtype=dtype, shape=(records, ny, nx))
        for start in range(0, ny, 64):
            stop = min(ny, start+64)
            block = values.read(start, stop, 0, nx, dtype) if values.path is not None else None
            if block is None:
                target[:, start:stop] = missing
            elif layer == 'catmxy':
                target[:, start:stop] = translated(block, dx, dy, mx, my, tiled=True)
            else:
                target[:, start:stop] = block
        # Closing the mapping schedules writes, like closing Fortran's file;
        # no extra synchronous disk flush is part of the reference contract.
        del target
        values.close()
        if netcdf:
            mapped = np.memmap(scratch, mode='r', dtype=dtype, shape=(records, ny, nx))
            write_highres_raster(destination, mapped, dtype, region[1:5])
            del mapped
            scratch.unlink()


def copy_region(source, out, tag, regions, bounds, shape, offsets, coarse_shape, tiled=False, netcdf=False):
    """Copy one layer at a time; first assignment wins, other fields last win."""
    if tiled:
        copy_native_tile(source, out, tag, regions[0], offsets, coarse_shape, netcdf)
        return
    west, east, south, north = bounds
    ny, nx = shape
    dx, dy = offsets
    mx, my = coarse_shape
    size = 1./PIXELS_PER_DEGREE[tag]
    chosen = np.zeros(shape, dtype=bool)  # Needed only for catmzz/catmz100 first-fill policy.
    accepted = []
    for region in regions:
        name, w, e, s, n, sx, sy = region
        assignment = source_array(source/(name+'.catmxy.bin'), '<i2', 2, sy, sx)
        if assignment.path is not None:
            accepted.append(region)
        assignment.close()
    for layer, dtype, records, missing in LAYERS:
        if layer == 'grdare' and (tag == '3sec' or tiled):
            continue
        if layer in ('downxy', 'flwdir') and not accepted:
            continue
        destination = out/(tag+'.'+layer+'.bin')
        scratch = scratch_path_for(destination, netcdf)
        with scratch.open('wb') as stream:
            stream.truncate(records*ny*nx*np.dtype(dtype).itemsize)
        target = np.memmap(scratch, mode='r+', dtype=dtype, shape=(records, ny, nx))
        for row in range(0, ny, 64):
            target[:, row:row+64] = missing
        # A disk-backed first-fill mask is unnecessary: recompute assignment occupancy
        # while copying its two companion classification layers in the same order.
        if layer in ('catmxy', 'catmzz', 'catmz100'):
            chosen[:] = False
        for name, w, e, s, n, sx, sy in accepted:
            values = source_array(source/(name+'.'+layer+'.bin'), dtype, records, sy, sx)
            assignment = source_array(source/(name+'.catmxy.bin'), '<i2', 2, sy, sx)
            if tiled:
                columns, target_x = np.arange(sx), np.arange(sx)
                source_rows, target_y = np.arange(sy), np.arange(sy)
            else:
                # REAL() in the source rounds centers to float32 before double indexing.
                longitude = (w+(np.arange(sx, dtype='f4')+np.float32(.5)).astype('f8')*size).astype('f4')
                latitude = (n-(np.arange(sy, dtype='f4')+np.float32(.5)).astype('f8')*size).astype('f4')
                columns = np.flatnonzero((longitude > west) & (longitude < east))
                source_rows = np.flatnonzero((latitude > south) & (latitude < north))
                target_x = ((longitude[columns].astype('f8')-west)/size).astype('i8')
                target_y = ((north-latitude[source_rows].astype('f8'))/size).astype('i8')
            if len(columns) == 0 or len(source_rows) == 0:
                values.close()
                assignment.close()
                continue
            x0, x1 = int(columns[0]), int(columns[-1])+1
            for start in range(0, len(source_rows), 64):
                rows = source_rows[start:start+64]
                yy = target_y[start:start+64]
                y0, y1 = int(rows[0]), int(rows[-1])+1
                index = np.ix_(yy, target_x)
                original_block = assignment.read(y0, y1, x0, x1, '<i2')
                values_block = values.read(y0, y1, x0, x1, dtype) if values.path is not None else None
                if layer in ('catmxy', 'catmzz', 'catmz100'):
                    original = original_block
                    mask = ~chosen[index] if not tiled else np.ones((len(rows), len(columns)), dtype=bool)
                    if layer == 'catmxy':
                        block = translated(original, dx, dy, mx, my, tiled)
                    else:
                        block = (values_block if values_block is not None
                                 else np.full((records, len(rows), len(columns)), missing, dtype=dtype))
                    for record in range(records):
                        previous = target[record][index]
                        previous[mask] = block[record][mask]
                        target[record][index] = previous
                    # Only an assignment value of -9999 leaves room for a later tile.
                    occupied = chosen[index]
                    occupied[mask] = original[0][mask] != -9999
                    chosen[index] = occupied
                else:
                    for record in range(records):
                        target[record][index] = (values_block[record] if values_block is not None else missing)
            values.close()
            assignment.close()
        target.flush()
        del target
        if netcdf:
            mapped = np.memmap(scratch, mode='r', dtype=dtype, shape=(records, ny, nx))
            write_highres_raster(destination, mapped, dtype, bounds)
            del mapped
            scratch.unlink()


def main():
    p = parser(__doc__)
    p.add_argument('hires_tag', choices=list(PIXELS_PER_DEGREE))
    p.add_argument('--change-info', type=Path, default=Path('dim_change.txt'))
    args = p.parse_args()
    lines = args.change_info.read_text().splitlines()
    tag = args.hires_tag
    source = Path(lines[0].strip())/tag
    if args.map_format == 'binary' and not (source/'location.txt').is_file():
        source = Path(lines[0].strip())/'binary'/tag
    mx, my, dx, dy = (int(lines[i].split()[0]) for i in (9, 10, 11, 12))
    west, east, south, north = (float(lines[i].split()[0]) for i in (13, 14, 15, 16))
    cnum = PIXELS_PER_DEGREE[tag]
    nx, ny = int((east-west)*cnum), int((north-south)*cnum)
    out = output_root(args)/tag
    out.mkdir(parents=True, exist_ok=True)
    tiled = tag != '1min' and (nx > 16000 or ny > 16000)
    locations = []
    if not tiled:
        text = (source/'location.txt').read_text().splitlines()
        regions = []
        for line in text[2:2+int(text[0].split()[0])]:
            f = line.split()
            w, e, s, n = map(float, f[2:6])
            if w > east or e < west or n < south or s > north:
                continue
            regions.append((f[1], w, e, s, n, int(f[6]), int(f[7])))
        copy_region(source, out, tag, regions, (west, east, south, north), (ny, nx), (dx, dy), (mx, my),
                    netcdf=args.map_format == 'netcdf')
        locations.append((tag, west, east, south, north, nx, ny))
    else:
        width = 30 if tag in ('30sec', '15sec') else 10 if tag in ('5sec', '3sec') else 5
        for latitude in range(90-width, -91, -width):
            for longitude in range(-180, 180, width):
                if longitude >= east or longitude+width <= west or latitude+width <= south or latitude >= north:
                    continue
                name = f'{"s" if latitude < 0 else "n"}{abs(latitude):02d}{"w" if longitude < 0 else "e"}{abs(longitude):03d}'
                if not (source/(name+'.catmxy.bin')).is_file():
                    continue
                region = (name, longitude, longitude+width, latitude, latitude+width, width*cnum, width*cnum)
                # copy_region writes the tag prefix; rename the prefix via its output argument.
                temporary = out/name
                temporary.mkdir()
                copy_region(source, temporary, tag, [region], region[1:5], (width*cnum, width*cnum),
                            (dx, dy), (mx, my), True, args.map_format == 'netcdf')
                for product in temporary.iterdir():
                    product.rename(out/(name+product.name[len(tag):]))
                temporary.rmdir()
                locations.append(region)
    with (out/'location.txt').open('w') as stream:
        stream.write(f'{len(locations):6d}  narea\n')
        stream.write(f'{"iarea":>6}{"carea":>10}{"west":>10}{"east":>10}{"south":>10}{"north":>10}{"nx":>8}{"ny":>8}{"csize":>20}\n')
        for i, (name, w, e, s, n, sx, sy) in enumerate(locations, 1):
            stream.write(f'{i:6d}{name:>10}{w:10.3f}{e:10.3f}{s:10.3f}{n:10.3f}{sx:8d}{sy:8d}{1./cnum:20.15f}\n')


if __name__ == '__main__':
    main()

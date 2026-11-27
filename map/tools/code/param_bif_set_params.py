# SPDX-License-Identifier: Apache-2.0
# Parallel port of param_bif_set_params.F90; original Fortran authors and license retained.
"""Filter bifori.csv widths and estimate legacy bifurcation channel depths.

Read the FLOW source CSV and map depth/basin/outlets, retain paths with a
positive selected width, then write finalized bifprm.csv plus optional maps.
The existing depth formula and endpoint-depth cap use float32 operations.
"""
from pathlib import Path
import sys

import numpy as np

from mod_map_io import Grid, output_root, parser, write_raster
try:
    from .mod_bifori_csv import read_bifori_csv
except ImportError:  # Direct execution from map-local Shell workflows.
    from mod_bifori_csv import read_bifori_csv
try:
    from .map_metadata import read_diminfo_nml
except ImportError:  # Direct execution from map-local Shell workflows.
    from map_metadata import read_diminfo_nml


def main():
    p = parser(__doc__,'.')
    p.add_argument('river_depth',type=Path)
    p.add_argument('output',type=Path)
    p.add_argument('layers',type=int)
    p.add_argument('diminfo',nargs='?',type=Path,default=Path('diminfo_test-1deg.nml'))
    p.add_argument(
        '--check-map',
        action='store_true',
        help='Generate optional diagnostic maps.',
    )
    args = p.parse_args()
    if not 1 <= args.layers <= 10:
        p.error('BIFLAYER must be 1..10')
    info = read_diminfo_nml(args.diminfo)
    grid=Grid(info.nx, info.ny, 0, *[np.float32(0)]*5)
    grid.raster(args.map_dir/'nextxy.bin','<i4',2)
    depth=grid.raster(args.river_depth)
    basin=grid.raster(args.map_dir/'basin.bin','<i4')
    lonlat=grid.raster(args.map_dir/'lonlat.bin','<f4',2)
    bifori = read_bifori_csv(args.map_dir/'bifori.csv')
    selected_width_count = min(bifori.width_count, args.layers)
    if args.layers > bifori.width_count:
        print(f'WARNING: BIFLAYER={args.layers} exceeds {bifori.width_count} stored widths; using available widths.',
              file=sys.stderr)
    selected_overland_fields = bifori.overland_fields[:selected_width_count - 1]
    diagnostic=np.full((2,grid.ny,grid.nx),-9999,dtype=np.float32)
    overland_count = len(selected_overland_fields)
    fields = ['pth_id', 'ix', 'iy', 'jx', 'jy', 'length', 'elevtn', 'depth', 'riv_width']
    fields += [f'ovl_width_{k}' for k in range(1, overland_count + 1)]
    fields += ['start_lat', 'start_lon', 'end_lat', 'end_lon', 'ibsn', 'jbsn']
    output=args.output_dir/args.output.name if args.output_dir is not None else args.output
    output.parent.mkdir(parents=True,exist_ok=True)
    rows = []
    number=0
    for row in bifori.rows:
        ix,iy,jx,jy=(int(row[name]) for name in ('ix','iy','jx','jy'))
        length_elevation=np.asarray([row['length'],row['elevtn']],dtype=np.float32)
        widths=np.asarray([row['riv_width'],*(row[name] for name in selected_overland_fields)],
                          dtype=np.float32)
        if not np.any(widths>0):
            continue
        if min(ix,iy,jx,jy)<1 or max(ix,jx)>grid.nx or max(iy,jy)>grid.ny:
            p.error('retained endpoint outside map')
        a=(iy-1,ix-1);b=(jy-1,jx-1);end=lonlat[:,b[0],b[1]]
        if not np.all(np.isfinite(end)) or np.any(end < -9990) or abs(end[0])>360 or abs(end[1])>90:
            p.error('retained endpoint has invalid outlet coordinates')
        number+=1
        if widths[0]<=0:
            estimate=np.float32(-9999);widths[0]=0
        else:
            estimate=np.float32(np.float32(np.log10(widths[0]))*np.float32(2.5)-np.float32(4))
            estimate=np.minimum(np.maximum(np.float32(.5),estimate),np.maximum(depth[a],depth[b]))
            diagnostic[0,a[0],a[1]]=estimate;diagnostic[1,a[0],a[1]]=widths[0]
        ibsn,jbsn=sorted((int(basin[a]),int(basin[b])))
        real_fields=[f'{x:.2f}' for x in [*length_elevation,estimate,*widths]]
        rows.append([number,ix,iy,jx,jy,*real_fields,
                     format_geo_coordinate(float(row['start_lat'])),
                     format_geo_coordinate(float(row['start_lon'])),
                     format_geo_coordinate(end[1]),format_geo_coordinate(end[0]),ibsn,jbsn])
    write_aligned_csv(output, fields, rows)
    if args.check_map:
        write_raster(output_root(args)/'check_bif_dphwth.bin',diagnostic,'<f4',
                     grid=Grid.from_file(args.map_dir))


def write_aligned_csv(path, fields, rows):
    """Write ordinary CSV with deterministic, monospaced column alignment."""
    columns = list(zip(*([fields] + rows))) if rows else [(value,) for value in fields]
    widths = [max(len(str(value)) for value in column) for column in columns]
    with path.open('w', newline='', encoding='utf-8') as stream:
        stream.write(','.join(str(value).rjust(width) for value, width in zip(fields, widths)) + '\n')
        for row in rows:
            stream.write(','.join(str(value).rjust(width) for value, width in zip(row, widths)) + '\n')


def format_geo_coordinate(value):
    """Format latitude or longitude to the CSV's 0.001-degree precision."""
    return f'{value:.3f}'


if __name__ == '__main__':
    main()

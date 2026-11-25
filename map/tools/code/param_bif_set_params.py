# SPDX-License-Identifier: Apache-2.0
# Parallel port of param_bif_set_params.F90; original Fortran authors and license retained.
"""Filter bifori widths and estimate legacy bifurcation channel depths.

Read Binary topology/depth/basin/outlets, retain paths with a positive selected
width, then write named bifprm.csv in source order plus optional depth/width maps.
The log-width depth formula and endpoint-depth cap use float32 operations.
"""
import csv
from pathlib import Path

import numpy as np

from mod_map_io import Grid, output_root, parser, write_raster


def main():
    p = parser(__doc__,'.')
    p.add_argument('river_depth',type=Path)
    p.add_argument('output',type=Path)
    p.add_argument('layers',type=int)
    p.add_argument('diminfo',nargs='?',type=Path,default=Path('diminfo_test-1deg.txt'))
    p.add_argument('check',nargs='?',choices=['check_map'])
    args = p.parse_args()
    if not 1 <= args.layers <= 10:
        p.error('BIFLAYER must be 1..10')
    dims=[int(s.split()[0]) for s in args.diminfo.read_text().splitlines()[:2]]
    grid=Grid(*dims,0,*[np.float32(0)]*5)
    grid.raster(args.map_dir/'nextxy.bin','<i4',2)
    depth=grid.raster(args.river_depth)
    basin=grid.raster(args.map_dir/'basin.bin','<i4')
    lonlat=grid.raster(args.map_dir/'lonlat.bin','<f4',2)
    lines=(args.map_dir/'bifori.txt').read_text().splitlines()
    npath,nlayer=(int(v) for v in lines[0].split()[:2])
    nlayer=min(nlayer,args.layers)
    diagnostic=np.full((2,grid.ny,grid.nx),-9999,dtype=np.float32)
    fields=['pth_id','ix','iy','jx','jy','length','elevtn','depth']+[f'width_{k}' for k in range(1,nlayer+1)]+['start_lat','start_lon','end_lat','end_lon','ibsn','jbsn']
    output=args.output_dir/args.output.name if args.output_dir is not None else args.output
    output.parent.mkdir(parents=True,exist_ok=True)
    with output.open('w',newline='') as stream:
        writer=csv.writer(stream,lineterminator='\n');writer.writerow(fields)
        number=0
        for line in lines[1:npath+1]:
            data=line.split();ix,iy,jx,jy=map(int,data[:4]);values=np.array(data[4:],dtype=np.float32)
            widths=values[2:2+nlayer].copy()
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
            real_fields=[f'{x:.2f}' for x in [values[0],values[1],estimate,*widths]]
            writer.writerow([number,ix,iy,jx,jy,*real_fields,f'{values[-2]:.3f}',f'{values[-1]:.3f}',f'{end[1]:.16e}',f'{end[0]:.16e}',ibsn,jbsn])
    if args.check:
        write_raster(output_root(args)/'check_bif_dphwth.bin',diagnostic,'<f4',
                     grid=Grid.from_file(args.map_dir/'params.txt'))


if __name__ == '__main__':
    main()

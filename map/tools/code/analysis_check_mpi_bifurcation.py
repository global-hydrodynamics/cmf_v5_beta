# SPDX-License-Identifier: Apache-2.0
# Parallel port of analysis_check_mpi_bifurcation.F90; original Fortran authors and license retained.
"""Reproduce model-local vector membership to classify MPI bifurcation paths.

Read regions/nextxy/bifprm.csv. Traversal deliberately admits the reference
out-of-region downstream extension; this is not a simple region-ID comparison.
Optional CSV contains only dropped paths, preserving water-level/width fields.
"""
from collections import deque
from pathlib import Path

import numpy as np

from mod_bifprm_csv import read_bifprm_csv
from mod_map_io import Grid, parser


def classify_paths(regions,nextxy,paths):
    """Return classes 1 retained,2 dropped,3 invalid, and endpoint region IDs."""
    ny,nx=regions.shape
    valid=np.array([1<=p['ix']<=nx and 1<=p['jx']<=nx and 1<=p['iy']<=ny and 1<=p['jy']<=ny for p in paths])
    up=np.zeros(len(paths),dtype=bool);down=up.copy();retained=up.copy()
    ids=np.full((len(paths),2),-9999,dtype=np.int32)
    for i,p in enumerate(paths):
        if valid[i]:ids[i]=[regions[p['iy']-1,p['ix']-1],regions[p['jy']-1,p['jx']-1]]
    for region in range(1,max(0,int(regions.max()))+1):
        counts=np.zeros(regions.shape,dtype=np.int32);visited=counts.copy();vector=np.zeros(regions.shape,dtype=bool)
        sources=np.argwhere((regions==region)&(nextxy[0]>0))
        for r,c in sources:
            x,y=nextxy[:,r,c]-1
            if not (0<=x<nx and 0<=y<ny):raise ValueError('downstream outside map')
            counts[y,x]+=1
        queue=deque()
        for r,c in sources:
            if counts[r,c]==visited[r,c]:queue.append((r,c));vector[r,c]=True
        while queue:
            r,c=queue.popleft();x,y=nextxy[:,r,c]-1
            if not (0<=x<nx and 0<=y<ny):raise ValueError('downstream outside map')
            visited[y,x]+=1
            if visited[y,x]==counts[y,x] and nextxy[0,y,x]>0 and not vector[y,x]:
                queue.append((y,x));vector[y,x]=True
        vector[(regions==region)&(nextxy[0]<0)&(nextxy[0]!=-9999)]=True
        for i,p in enumerate(paths):
            if not valid[i]:continue
            a=(p['iy']-1,p['ix']-1);b=(p['jy']-1,p['jx']-1)
            if ids[i,0]==region and vector[a]:up[i]=True
            if ids[i,1]==region and vector[b]:down[i]=True
            if vector[a] and vector[b]:retained[i]=True
    classes=np.where(valid&up&down,np.where(retained,1,2),3)
    return classes,ids


def main():
    p=parser(__doc__,'.');p.add_argument('region_file',type=Path);p.add_argument('--csv',type=Path)
    args=p.parse_args();grid=Grid.read(args.map_dir/'params.txt')
    regions=grid.raster(args.region_file,'<i4');nextxy=grid.raster(args.map_dir/'nextxy.bin','<i4',2)
    paths=read_bifprm_csv(args.map_dir/'bifprm.csv');classes,ids=classify_paths(regions,nextxy,paths)
    channel=np.array([row['widths'][0]>0 for row in paths]);totals=np.bincount(classes,minlength=4)[1:]
    print('MPI regions:',max(0,int(regions.max())));print('Bifurcation pathways:',len(paths))
    print('Retained by a model-local vector:',totals[0])
    print('  including endpoints in different assigned regions via downstream vector extension:',np.count_nonzero((classes==1)&(ids[:,0]!=ids[:,1])))
    print('Dropped (both endpoints have a vector, but never on the same rank):',totals[1])
    print('Invalid/unassigned (an endpoint has no model vector):',totals[2])
    if len(paths):print(f'Dropped fraction of all pathways: {np.float32(np.float32(totals[1])/np.float32(len(paths))*np.float32(100)):8.4f} %')
    for label,mask in [('Channel',channel),('Floodplain-only',~channel)]:
        print(label+' retained/dropped/invalid:',*(np.count_nonzero(mask&(classes==k)) for k in (1,2,3)))
    print('The dropped fraction measures connectivity exclusion, not simulation error.')
    if args.csv:
        with args.csv.open('w') as out:
            out.write('ix,iy,jx,jy,region_up,region_down,elevation,latitude,longitude,type,width1\n')
            for row,kind,regions_pair in zip(paths,classes,ids):
                if kind!=2:continue
                label='channel' if row['widths'][0]>0 else 'floodplain_only'
                out.write(','.join(str(row[k]) for k in ['ix','iy','jx','jy'])+f",{regions_pair[0]},{regions_pair[1]},{row['elevtn']:.3f},{row['start_lat']:.6f},{row['start_lon']:.6f},{label},{row['widths'][0]:.3f}\n")
        print('Dropped-path CSV:',args.csv)


if __name__ == '__main__':
    main()

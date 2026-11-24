"""Opt-in synthetic larger coarse-network/crop comparison, sequential only."""
import argparse
import json
from pathlib import Path
import statistics
import sys

import numpy as np

from benchmark_python_ports import CODE, compare_file, compile_references, timed


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--work',type=Path,required=True)
    p.add_argument('--repeats',type=int,default=3)
    args=p.parse_args();args.work.mkdir(parents=True,exist_ok=False)
    build=compile_references(args.work)
    source=args.work/'source';source.mkdir()
    nx,ny=720,360
    (source/'params.txt').write_text('720\n360\n2\n.5\n-180\n180\n-90\n90\n')
    xy=np.empty((2,ny,nx),dtype='<i4');xy[0]=np.arange(1,nx+1)[None,:];xy[1]=np.arange(2,ny+2)[:,None];xy[:,-1]=-9;xy.tofile(source/'nextxy.bin')
    np.zeros_like(xy).tofile(source/'downxy.bin')
    for name in ('grdare','ctmare','uparea','elevtn','nxtdst','rivlen','width'):
        np.full((ny,nx),1e6 if name in ('grdare','ctmare','uparea') else 1,dtype='<f4').tofile(source/(name+'.bin'))
    np.ones((2,ny,nx),dtype='<f4').tofile(source/'fldhgt.bin')
    np.zeros((2,ny,nx),dtype='<f4').tofile(source/'lonlat.bin')
    results=[]
    for program in ('region_cut_domain','region_set_map'):
        f=args.work/(program+'_f');out=args.work/(program+'_p');f.mkdir();out.mkdir();work=f/'work';work.mkdir()
        products=(['params.txt','nextxy.bin','downxy.bin','elevtn.bin','ctmare.bin','grdare.bin','uparea.bin','nxtdst.bin','rivlen.bin','width.bin','fldhgt.bin','lonlat.bin','lsmask.bin','nextxy_noedge.bin'] if program=='region_cut_domain' else ['rivseq.bin','uparea_grid.bin','upgrid.bin','nxtdst_grid.bin','rivlen_grid.bin','basin.bin','bsncol.bin'])
        if program=='region_cut_domain':(work/'region_info.txt').write_text(str(source)+'/\n-120\n120\n-60\n60\n')
        else:
            for name in ('params.txt','nextxy.bin','grdare.bin'):(f/name).symlink_to(source/name)
        times=[[],[]];memory=[[],[]]
        for repeat in range(args.repeats):
            if repeat:
                for product in products:(f/product).unlink(missing_ok=True)
                for file in (work/'dim_change.txt',out/'dim_change.txt'):file.unlink(missing_ok=True)
            for product in products:(out/product).unlink(missing_ok=True)
            a,elapsed,rss=timed([str(build/program)],work,f/f'run{repeat}.log');times[0].append(elapsed);memory[0].append(rss)
            extra=['--region-info',str(work/'region_info.txt'),'--change-info',str(out/'dim_change.txt')] if program=='region_cut_domain' else []
            b,elapsed,rss=timed([sys.executable,str(CODE/(program+'.py')),'--map-dir',str(f),'--output-dir',str(out),*extra],args.work,out/f'run{repeat}.log');times[1].append(elapsed);memory[1].append(rss)
            if a.returncode or b.returncode:raise RuntimeError(f'{program}: {a.returncode}, {b.returncode}; see logs')
            integer={'nextxy.bin','nextxy_noedge.bin','downxy.bin','lsmask.bin','rivseq.bin','upgrid.bin','basin.bin','bsncol.bin'}
            checks={name:compare_file(f/name,out/name,name in integer) for name in products}
        result={'program':program,'dataset':'SYNTHETIC 720x360 (259200 cells), crop 480x240','repeats':args.repeats,
                'fortran_seconds':statistics.median(times[0]),'python_seconds':statistics.median(times[1]),
                'ratio':statistics.median(times[1])/statistics.median(times[0]),'fortran_peak_bytes':max((v for v in memory[0] if v is not None),default=None),'python_peak_bytes':max((v for v in memory[1] if v is not None),default=None),
                'status':'PASS' if all(v['equivalent'] for v in checks.values()) else 'DIFFER','outputs':checks}
        results.append(result);print(json.dumps(result),flush=True)
        (args.work/'results.json').write_text(json.dumps(results,indent=2))


if __name__=='__main__':main()

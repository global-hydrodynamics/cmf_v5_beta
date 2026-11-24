"""Opt-in synthetic 3sec tile benchmark; no global data are acquired.

Creates exact int16/float32 direct-access files in a NEW temporary work root.
The full 12000x12000 case uses a 10-degree source tile and a 2-degree crop.
Reuse benchmark_python_ports for compilation, timing and numerical comparison.
"""
import argparse
import json
from pathlib import Path
import statistics
import sys

import numpy as np

from benchmark_python_ports import CODE, compare_file, compile_references, timed


def fixture(source, pixels):
    """Generate a regular synthetic river domain and one native tile, blockwise."""
    tag = source/'3sec'
    tag.mkdir(parents=True)
    extent = pixels/1200
    coarse = int(np.ceil(extent/.25))
    (source/'params.txt').write_text(f'{coarse}\n{coarse}\n1\n0.25\n0\n{coarse*.25}\n0\n{coarse*.25}\n')
    # Independent terminal cells deliberately isolate per-catchment aggregation.
    np.full((2,coarse,coarse), -9, dtype='<i4').tofile(source/'nextxy.bin')
    np.full((coarse,coarse), 1e6, dtype='<f4').tofile(source/'ctmare.bin')
    (tag/'location.txt').write_text(f'1 narea\niarea carea west east south north nx ny csize\n1 tile 0 {extent} 0 {extent} {pixels} {pixels} {1/1200:.15f}\n')
    fields = [('catmxy', '<i2', 2), ('elevtn', '<f4', 1), ('rivwth', '<f4', 1), ('flddif', '<f4', 1), ('grdare', '<f4', 1)]
    for name,dtype,records in fields:
        target = np.memmap(tag/f'tile.{name}.bin', mode='w+', dtype=dtype, shape=(records,pixels,pixels))
        for start in range(0,pixels,64):
            stop=min(pixels,start+64)
            if name=='catmxy':
                target[0,start:stop] = np.arange(pixels,dtype='i4')[None,:]//300+1
                target[1,start:stop] = (np.arange(start,stop,dtype='i4')[:,None]//300+1)
            elif name=='elevtn':
                target[0,start:stop] = np.arange(pixels,dtype='f4')[None,:]*np.float32(.1)+np.arange(start,stop,dtype='f4')[:,None]
            else:
                target[:,start:stop] = 1 if name=='rivwth' else 0 if name=='flddif' else np.float32(1e-6)
        target.flush()
        del target
    return coarse,extent


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--work',type=Path,required=True)
    p.add_argument('--pixels',type=int,default=12000)
    p.add_argument('--repeats',type=int,default=1)
    p.add_argument('--source',type=Path,help='Reuse a previously generated synthetic source; never alter it')
    p.add_argument('--whole-tile',action='store_true',help='Exercise the >16000-pixel extent branch; requires 12000-pixel source')
    args=p.parse_args()
    args.work.mkdir(parents=True,exist_ok=False)
    build=compile_references(args.work)
    source=args.source.resolve() if args.source else args.work/'source'
    if args.source:
        extent=args.pixels/1200
        coarse=int(np.ceil(extent/.25))
    else:
        source.mkdir()
        coarse,extent=fixture(source,args.pixels)
    if args.whole_tile and args.pixels != 12000:
        p.error('--whole-tile requires --pixels 12000')
    if args.whole_tile:
        # Create read-only aliases in a new source directory; preserve the old fixture.
        aliases=args.work/'tile_source';(aliases/'3sec').mkdir(parents=True)
        for item in (source/'3sec').glob('tile.*.bin'):
            (aliases/'3sec'/item.name.replace('tile.', 'n00e000.', 1)).symlink_to(item)
        source=aliases
    crop=min(2.,extent)
    products=['catmxy','catmzz','catmz100','flddif','hand','elevtn','uparea','rivwth','visual','downxy','flwdir']
    results=[]
    for program in (['region_combine_hires'] if args.whole_tile else ['region_combine_hires','param_water_calc_prmwat']):
        f=args.work/('combine_f' if program.startswith('region') else 'water_f')
        py=args.work/('combine_p' if program.startswith('region') else 'water_p')
        f.mkdir();py.mkdir()
        ft=[];pt=[];fm=[];pm=[]
        for repeat in range(args.repeats):
            if program.startswith('region'):
                out=f/'3sec';out.mkdir(exist_ok=True)
                if repeat:
                    for item in out.iterdir():item.unlink()
                    for item in (py/'3sec').iterdir():item.unlink()
                change=f/'dim_change.txt'
                change.write_text('\n'.join([str(source)+'/',str(coarse),str(coarse),'.25','0',str(extent),'0',str(extent),'../',str(80 if args.whole_tile else int(crop/.25)),str(40 if args.whole_tile else int(crop/.25)),'0','0','0',str(20 if args.whole_tile else crop),str(0 if args.whole_tile else extent-crop),str(extent)])+'\n')
                # The reference requires its own output in ../3sec.
                work=f/'work';work.mkdir(exist_ok=True)
                (work/'dim_change.txt').write_text(change.read_text())
                a,elapsed,rss=timed([str(build/program),'3sec'],work,f/f'run{repeat}.log')
                ft.append(elapsed);fm.append(rss)
                b,elapsed,rss=timed([sys.executable,str(CODE/(program+'.py')),'3sec','--map-dir',str(f),'--output-dir',str(py),'--change-info',str(change)],args.work,py/f'run{repeat}.log')
                pt.append(elapsed);pm.append(rss)
                prefix='n00e000' if args.whole_tile else '3sec'
                checks={name:compare_file(out/f'{prefix}.{name}.bin',py/'3sec'/f'{prefix}.{name}.bin',name in ('catmxy','catmzz','catmz100','visual','downxy','flwdir')) for name in products}
                checks['location.txt']=compare_file(out/'location.txt',py/'3sec/location.txt')
            else:
                (f/'prmwat.bin').unlink(missing_ok=True);(py/'prmwat.bin').unlink(missing_ok=True)
                # Separate Fortran CWD with read-only input symlinks.
                for name in ('params.txt','nextxy.bin','ctmare.bin','3sec'):
                    if not (f/name).exists():(f/name).symlink_to(source/name)
                a,elapsed,rss=timed([str(build/program),'3sec'],f,f/f'run{repeat}.log');ft.append(elapsed);fm.append(rss)
                b,elapsed,rss=timed([sys.executable,str(CODE/(program+'.py')),'3sec','--map-dir',str(source),'--output-dir',str(py)],args.work,py/f'run{repeat}.log');pt.append(elapsed);pm.append(rss)
                checks={'prmwat':compare_file(f/'prmwat.bin',py/'prmwat.bin')}
            if a.returncode or b.returncode:raise RuntimeError(f'{program}: F={a.returncode} P={b.returncode}; see logs')
        result={'program':program,'dataset':f'SYNTHETIC 3sec {args.pixels}x{args.pixels}, '+('whole tile; requested 20x10 degree domain' if args.whole_tile else f'crop {int(crop*1200)}x{int(crop*1200)}'),
                'repeats':args.repeats,'fortran_seconds':statistics.median(ft),'python_seconds':statistics.median(pt),
                'ratio':statistics.median(pt)/statistics.median(ft),'fortran_peak_bytes':max((v for v in fm if v is not None),default=None),'python_peak_bytes':max((v for v in pm if v is not None),default=None),
                'status':'PASS' if all(v['equivalent'] for v in checks.values()) else 'DIFFER','outputs':checks}
        results.append(result);print(json.dumps(result),flush=True)
        (args.work/'results.json').write_text(json.dumps(results,indent=2))


if __name__=='__main__':main()

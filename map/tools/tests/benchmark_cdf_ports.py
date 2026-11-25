"""Optional NetCDF interface comparison; requires existing netCDF4 and nf-config."""
import argparse
import json
from pathlib import Path
import shutil
import statistics
import subprocess
import sys

import numpy as np
from netCDF4 import Dataset

from benchmark_python_ports import CODE, FLAGS, SAMPLE, base_copy, compare_file, timed


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--work',type=Path,required=True)
    p.add_argument('--repeats',type=int,default=3)
    args=p.parse_args();args.work.mkdir(parents=True,exist_ok=False)
    flags=subprocess.check_output(['nf-config','--fflags'],text=True).split()
    libraries=subprocess.check_output(['nf-config','--flibs'],text=True).split()+subprocess.check_output(['nc-config','--libs'],text=True).split()
    results=[]
    for program in ('param_channel_calc_outclm','param_channel_calc_rivwth'):
        case=args.work/program;case.mkdir();exe=case/'reference'
        subprocess.run(['gfortran',*FLAGS,'-DUseCDF_CMF',*flags,str(CODE/(program+'.F90')),*libraries,'-o',str(exe)],check=True,capture_output=True)
        f=case/'f';py=case/'p';py.mkdir()
        products=['outclm.bin'] if program.endswith('outclm') else ['rivhgt.bin','rivwth.bin','rivman.bin','rivhgt_inf.bin','rivpar.nc']
        base_copy(f,products)
        diminfo=f/'diminfo_test-1deg.txt'
        if program.endswith('outclm'):
            runoff=case/'runoff.nc'
            with Dataset(runoff,'w',format='NETCDF3_64BIT_OFFSET') as ds:
                ds.createDimension('time',2);ds.createDimension('lat',180);ds.createDimension('lon',360)
                var=ds.createVariable('runoff','f4',('time','lat','lon'))
                var[0]=np.full((180,360),.001,dtype='f4')
                var[1]=np.full((180,360),10,dtype='f4')
            options=[str(diminfo),str(runoff),'--map-binary']
        else:options=[str(diminfo),'.1','.5','0','1','.4','.75','0','10','--map-binary']
        times=[[],[]];memory=[[],[]]
        for repeat in range(args.repeats):
            if repeat:
                for name in products:(f/name).unlink(missing_ok=True)
            for name in products:(py/name).unlink(missing_ok=True)
            a,elapsed,rss=timed([str(exe),*options],f,case/f'f{repeat}.log');times[0].append(elapsed);memory[0].append(rss)
            b,elapsed,rss=timed([sys.executable,str(CODE/(program+'.py')),*options,'--map-dir',str(f),'--output-dir',str(py)],case,case/f'p{repeat}.log');times[1].append(elapsed);memory[1].append(rss)
            if a.returncode or b.returncode:raise RuntimeError(f'{program}: F={a.returncode} P={b.returncode}; see logs')
            checks={name:compare_file(f/name,py/name) for name in products if name.endswith('.bin')}
            if 'rivpar.nc' in products:
                with Dataset(f/'rivpar.nc') as reference,Dataset(py/'rivpar.nc') as actual:
                    checks['rivpar.nc']={'equivalent':list(reference.dimensions)==list(actual.dimensions) and set(reference.variables)==set(actual.variables)}
                    for name in reference.variables:
                        a,b=reference[name],actual[name];a.set_auto_maskandscale(False);b.set_auto_maskandscale(False)
                        attrs_a={k:a.getncattr(k) for k in a.ncattrs()};attrs_b={k:b.getncattr(k) for k in b.ncattrs()}
                        okay=a.dimensions==b.dimensions and a.dtype==b.dtype and attrs_a==attrs_b and np.array_equal(a[:],b[:])
                        checks[name]={'equivalent':bool(okay),'max_abs':float(np.max(abs(a[:]-b[:]))) }
        result={'program':program,'dataset':'Mekong Binary map + 2-time synthetic NetCDF (first record) / rivpar.nc','repeats':args.repeats,
                'fortran_seconds':statistics.median(times[0]),'python_seconds':statistics.median(times[1]),'ratio':statistics.median(times[1])/statistics.median(times[0]),
                'fortran_peak_bytes':max((v for v in memory[0] if v is not None),default=None),'python_peak_bytes':max((v for v in memory[1] if v is not None),default=None),'status':'PASS' if all(v['equivalent'] for v in checks.values()) else 'DIFFER','outputs':checks}
        results.append(result);print(json.dumps(result),flush=True)
        (args.work/'results.json').write_text(json.dumps(results,indent=2))


if __name__=='__main__':main()

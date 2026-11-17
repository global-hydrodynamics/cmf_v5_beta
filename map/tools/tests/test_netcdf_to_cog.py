"""Scientific storage, coordinates, display overviews and safe-publication contracts."""
import hashlib
import os
from pathlib import Path
import subprocess
import sys

import pytest
np = pytest.importorskip('numpy')
nc = pytest.importorskip('netCDF4')
rio = pytest.importorskip('rasterio')
from rasterio.enums import Resampling
from map.tools.code import convert_netcdf_to_cog as cog

ROOT = Path(__file__).resolve().parents[3]
REGISTRY = ROOT / 'variable_table/map_variables.csv'


def fixture(tmp_path, product='elevtn', dtype='float32', order=('lat', 'lon'), reverse_y=False,
            reverse_x=False, layers=0, names=None, fill=-9999, nx=16, ny=16):
    names = names or [product]
    root = tmp_path / 'map'
    (root/'netcdf').mkdir(parents=True, exist_ok=True)
    (root/'params.txt').write_text(f'{nx}\n{ny}\n{layers or 1}\n.1\n10\n{10+nx*.1}\n{30-ny*.1}\n30\n')
    source = root/'netcdf'/f'{product}.nc'
    arrays = []
    with nc.Dataset(source, 'w') as ds:
        for name, size in [('lat', ny), ('lon', nx)]:
            ds.createDimension(name, size)
            coord = ds.createVariable(name, 'f8', (name,))
            coord.units = 'degrees_north' if name == 'lat' else 'degrees_east'
            values = 30-(np.arange(ny)+.5)*.1 if name == 'lat' else 10+(np.arange(nx)+.5)*.1
            coord[:] = values[::-1] if ((name == 'lat' and reverse_y) or (name == 'lon' and reverse_x)) else values
        if layers:
            ds.createDimension('layer', layers)
        for i, name in enumerate(names):
            dims = ('layer',)+order if layers else order
            var = ds.createVariable(name, dtype, dims, fill_value=fill, zlib=True)
            var.units = 'm' if np.dtype(dtype).kind == 'f' else '1'
            data = (np.arange(nx*ny).reshape(ny, nx) % 100 + i*100).astype(dtype)
            data[0, 0] = fill
            data = np.stack([data+j*1000 for j in range(layers)]) if layers else data
            if layers:
                data[:, 0, 0] = fill
            arrays.append(data.copy())
            if reverse_y:
                data = data[..., ::-1, :]
            if reverse_x:
                data = data[..., :, ::-1]
            if order == ('lon', 'lat'):
                data = data.swapaxes(-1, -2)
            var[:] = data
    rows = cog.hires.registry_rows(REGISTRY)
    selected = [r for r in rows if r['binary_filename'] == f'{product}.bin']
    if not selected:
        selected = [dict(name=n, dtype=dtype, dimensions='NX,NY', record_index=str(i+1),
                         missing_value=str(fill), units='1', long_name=n, physical_description='test index')
                    for i,n in enumerate(names)]
    task = cog.Task(source, root/'COG'/f'{product}.tif', selected, cog.base_geometry(root/'params.txt'))
    return task, arrays


@pytest.mark.parametrize('dtype', ['float32', 'int8', 'int16', 'int32'])
@pytest.mark.parametrize('order,ry,rx', [(('lat','lon'),False,False), (('lon','lat'),True,True)])
def test_native_types_coordinates_and_order(tmp_path, dtype, order, ry, rx):
    fill = -9 if dtype == 'int8' else -9999
    product = 'elevtn' if dtype == 'float32' else 'fixture'
    task, arrays = fixture(tmp_path, product, dtype, order, ry, rx, fill=fill)
    before = hashlib.sha256(task.source.read_bytes()).digest()
    assert cog.convert(task, blocksize=128).startswith('PASS')
    with rio.open(task.target) as ds:
        assert ds.crs.to_epsg() == 4326
        assert ds.dtypes == (dtype,)
        assert ds.bounds == pytest.approx((10,28.4,11.6,30))
        assert ds.read(1).tobytes() == arrays[0].tobytes()
        assert ds.read_masks(1)[0,0] == 0
        assert ds.tags(1)['source_record_1based'] == '1'
    assert hashlib.sha256(task.source.read_bytes()).digest() == before


def test_multivariable_layers_and_band_order(tmp_path):
    task, arrays = fixture(tmp_path, 'nextxy', 'int32', names=['nextx','nexty'])
    cog.convert(task, blocksize=128)
    with rio.open(task.target) as ds:
        assert ds.descriptions == ('nextx','nexty')
        for i, a in enumerate(arrays, 1):
            assert ds.read(i).tobytes() == a.tobytes()
    task, arrays = fixture(tmp_path/'layer', 'fldhgt', layers=3, order=('lon','lat'), reverse_y=True)
    cog.convert(task, blocksize=128)
    with rio.open(task.target) as ds:
        assert ds.count == 3
        for i in range(3):
            np.testing.assert_array_equal(ds.read(i+1), arrays[0][i])
            assert ds.tags(i+1)['source_indices_1based'] == f'layer={i+1}'


def test_average_nodata_and_nearest_pair_overviews(tmp_path):
    task, arrays = fixture(tmp_path)
    cog.convert(task, blocksize=128, overviews=[2,4,8,16,32])
    with rio.open(task.target) as ds:
        assert ds.overviews(1) == [2,4,8,16]
        overview = ds.read(1, out_shape=(8,8), resampling=Resampling.nearest)
        expected = np.ma.masked_equal(arrays[0], -9999).reshape(8,2,8,2).mean(axis=(1,3))
        np.testing.assert_allclose(overview, expected)
        assert ds.tags()['overview_resampling'] == 'average'
    task, arrays = fixture(tmp_path/'pair', 'catmxy', 'int16', names=['catmxx','catmyy'])
    cog.convert(task, blocksize=128)
    with rio.open(task.target) as ds:
        overview = ds.read(out_shape=(2,8,8), resampling=Resampling.nearest)
        pairs = set(zip(arrays[0].flat, arrays[1].flat))
        assert set(zip(overview[0].flat, overview[1].flat)) <= pairs
        assert ds.tags()['overview_resampling'] == 'nearest'
    # Odd source dimensions have rounded actual overview sizes/factors.
    task, _ = fixture(tmp_path/'odd', nx=19, ny=17)
    assert cog.convert(task, blocksize=128).startswith('PASS')


def test_skip_force_failure_and_no_sidecars(tmp_path, monkeypatch):
    task, _ = fixture(tmp_path)
    cog.convert(task, blocksize=128)
    previous = task.target.read_bytes()
    assert cog.convert(task, blocksize=128).startswith('SKIP')
    with nc.Dataset(task.source, 'a') as ds:
        ds['elevtn'][1,1] = 999
    assert cog.convert(task, blocksize=128, force=True).startswith('PASS')
    assert task.target.read_bytes() != previous
    previous = task.target.read_bytes()
    def fail(*args, **kwargs):
        raise RuntimeError('injected verification failure')
    monkeypatch.setattr(cog, 'verify', fail)
    with pytest.raises(RuntimeError, match='injected'):
        cog.convert(task, blocksize=128, force=True)
    assert task.target.read_bytes() == previous
    assert sorted(p.name for p in task.target.parent.iterdir()) == [task.target.name]


@pytest.mark.parametrize('change', ['coords','packing','dtype','mixed_fill','extra','irregular'])
def test_unsupported_is_explicit_and_never_publishes(tmp_path, change):
    task, _ = fixture(tmp_path, 'nextxy', 'int32', names=['nextx','nexty'])
    with nc.Dataset(task.source, 'a') as ds:
        if change == 'coords': ds['lat'][:] = ds['lat'][:]+.2
        if change == 'irregular': ds['lat'][3] += .001
        if change == 'packing': ds['nextx'].scale_factor = 2
        if change == 'mixed_fill': ds['nexty'].missing_value = -123
        if change == 'extra': ds.createVariable('unmapped', 'i4', ('lat','lon'))[:] = 1
    if change == 'dtype': task.rows[0] = dict(task.rows[0], dtype='float32')
    with pytest.raises(cog.Unsupported):
        cog.convert(task, blocksize=128)
    assert not task.target.exists()


def test_discovery_all_registry_files_highres_and_unknowns(tmp_path, capsys):
    task, _ = fixture(tmp_path, 'nextxy_noedge', 'int32', names=['nextx','nexty'])
    root = task.source.parent.parent
    high = root/'15sec_nc'
    high.mkdir()
    (high/'location.txt').write_text('1 narea\niarea carea west east south north nx ny csize\n1 a 10 11.6 28.4 30 16 16 .1\n')
    pair, _ = fixture(tmp_path/'seed', 'catmxy', 'int16', names=['catmxx','catmyy'])
    import shutil
    shutil.copyfile(pair.source, high/'a.catmxy.nc')
    plan = cog.plan(root, ['base','15sec'], ['all'], REGISTRY)
    assert [x.target.relative_to(root).as_posix() for x in plan] == ['COG/nextxy_noedge.tif','COG/15sec/a.catmxy.tif']
    for t in plan: assert cog.convert(t, blocksize=128).startswith('PASS')
    assert 'SKIP missing registered NetCDF' in capsys.readouterr().out
    for task in plan:
        task.target.unlink()  # Exercise actual conversions in workers, not just existing-file skips.
    options = ['--map-dir',str(root),'--resolutions','base 15sec',
               '--variables','nextxy_noedge catmxy','--jobs','2','--blocksize','128']
    assert cog.main(options) == 0
    previous = plan[0].target.read_bytes()
    with nc.Dataset(plan[0].source, 'a') as ds:
        ds['nextx'].scale_factor = 2
    assert cog.main(options + ['--force']) == 1
    assert plan[0].target.read_bytes() == previous
    assert plan[1].target.is_file()
    with pytest.raises(ValueError, match='No registered'):
        cog.plan(root,['base'],['not_registered'],REGISTRY)


def test_cog_standard_validator_and_shell_paths(tmp_path, monkeypatch):
    task, _ = fixture(tmp_path)
    cog.convert(task, blocksize=128)
    validator = pytest.importorskip('rio_cogeo.cogeo')
    assert validator.cog_validate(task.target, strict=True)[0]
    for folder in ('tools','mekong_15min'):
        script = ROOT/f'map/{folder}/script_format_conv/s05-convert_netcdf_to_cog.sh'
        subprocess.run(['sh','-n',str(script)], check=True)
        env = dict(os.environ, PATH=str(Path(sys.executable).parent)+os.pathsep+os.environ['PATH'])
        result = subprocess.run(['sh', str(script),'--map-dir',str(task.source.parent.parent),
                                 '--resolutions','base','--variables','elevtn','--jobs','1'],
                                cwd=tmp_path,env=env,text=True,capture_output=True)
        assert result.returncode == 0, result.stdout+result.stderr
    local = task.source.parent.parent / 'script_format_conv'
    local.mkdir()
    monkeypatch.chdir(local)
    task.target.unlink()
    assert cog.main(['--resolutions','base','--variables','elevtn','--jobs','1','--blocksize','128']) == 0
    assert task.target.is_file()
    monkeypatch.chdir(ROOT/'map/tools/script_format_conv')
    assert cog.main(['--jobs','1']) == 2  # Shared template is not an implicit map.


def test_bounded_raster_read_windows(tmp_path, monkeypatch):
    task, _ = fixture(tmp_path, nx=513, ny=259)
    original = cog.read_plane
    sizes=[]
    def bounded(ds,band,axes,window):
        assert window.width <= 128 and window.height <= 128
        sizes.append((window.width, window.height))
        return original(ds,band,axes,window)
    monkeypatch.setattr(cog,'read_plane',bounded)
    cog.convert(task,blocksize=128)
    assert len(sizes) == 30  #15 write blocks and15 full native verification blocks.


def test_special_float_bits_and_nan_nodata(tmp_path):
    task, _ = fixture(tmp_path, fill=float('nan'))
    bits = np.array([0, 0x80000000, 0x7f800000, 0xff800000, 0x7fc00001], dtype='uint32')
    with nc.Dataset(task.source, 'a') as ds:
        ds.set_auto_maskandscale(False)
        ds['elevtn'][1, :5] = bits.view('float32')
    assert cog.convert(task, blocksize=128).startswith('PASS')
    with rio.open(task.target) as ds:
        np.testing.assert_array_equal(ds.read(1)[1, :5].view('uint32'), bits)
        assert ds.read_masks(1)[1,4] == 0


def test_extra_records_and_unmapped_variables(tmp_path):
    task, _ = fixture(tmp_path)
    with nc.Dataset(task.source, 'a') as ds:
        # Additional records may precede or follow the spatial dimensions.
        ds.createDimension('record', 2)
        ds.renameVariable('elevtn', 'old')
        var = ds.createVariable('elevtn', 'f4', ('lat','record','lon'), fill_value=-9999)
        var.units = 'm'
        var[:,0,:] = 1
        var[:,1,:] = 2
        ds.renameVariable('old', 'unexpected')
    # Extra unmapped spatial content cannot disappear silently.
    with pytest.raises(cog.Unsupported, match='unmapped'):
        cog.convert(task,blocksize=128)
    # Build a clean multiple-record file to test native record ordering.
    with nc.Dataset(task.source) as src, nc.Dataset(task.source.with_suffix('.new'),'w') as dst:
        for name,d in src.dimensions.items():dst.createDimension(name,len(d))
        for name in ('lat','lon','elevtn'):
            v=src[name]; out=dst.createVariable(name,v.dtype,v.dimensions,fill_value=getattr(v,'_FillValue',None))
            out.setncatts({k:v.getncattr(k) for k in v.ncattrs() if k != '_FillValue'})
            out[:]=v[:]
    task.source.with_suffix('.new').replace(task.source)
    cog.convert(task,blocksize=128)
    with rio.open(task.target) as ds:
        assert ds.count == 2
        assert ds.tags(1)['source_indices_1based'] == 'record=1'
        assert ds.tags(2)['source_indices_1based'] == 'record=2'
        assert np.all(ds.read(1) == 1) and np.all(ds.read(2) == 2)


def test_invalid_job_and_overview_settings_report_failure(tmp_path):
    task,_ = fixture(tmp_path)
    assert cog.main(['--map-dir',str(task.source.parent.parent),'--jobs','0']) == 2
    assert cog.main(['--map-dir',str(task.source.parent.parent),'--overviews','3']) == 2


def test_large_netcdf_with_320_mib_process_budget(tmp_path):
    """A 512MiB native plane cannot fit as a full array alongside the runtime."""
    import time
    if os.name != 'posix':
        pytest.skip('POSIX ps/resource monitor required for RSS budget test')
    code = r'''
import json, resource, sys
from pathlib import Path
import netCDF4 as nc
import numpy as np
from map.tools.code import convert_netcdf_to_cog as c
root=Path(sys.argv[1]); (root/'netcdf').mkdir()
(root/'params.txt').write_text('16384\n8192\n1\n.001\n10\n26.384\n21.808\n30\n')
nc.set_chunk_cache(4*1024*1024,1009,.75)
p=root/'netcdf/elevtn.nc'
with nc.Dataset(p,'w') as ds:
 for name in ('lat','lon'):
  ds.createDimension(name,8192 if name=='lat' else 16384)
  a=ds.createVariable(name,'f8',(name,)); a.units='degrees_north' if name=='lat' else 'degrees_east'
  a[:]=30-(np.arange(8192)+.5)*.001 if name=='lat' else 10+(np.arange(16384)+.5)*.001
 v=ds.createVariable('elevtn','f4',('lat','lon'),fill_value=-9999,zlib=True,chunksizes=(512,512))
 v.set_var_chunk_cache(1024*1024,1009,.75)
 block=np.full((512,512),1.25,dtype='float32')
 for y in range(0,8192,512):
  for x in range(0,16384,512):v[y:y+512,x:x+512]=block
 del block
rows=c.hires.registry_rows(c.DEFAULT_REGISTRY)
rows=[r for r in rows if r['binary_filename']=='elevtn.bin']
t=c.Task(p,root/'COG/elevtn.tif',rows,c.base_geometry(root/'params.txt'))
print(c.convert(t),flush=True)
rss=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
print(json.dumps({'peak_rss_mib':rss/(1024**2 if sys.platform=='darwin' else 1024)}),flush=True)
'''
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1')
    log = tmp_path/'process.log'
    peak = 0
    with log.open('w') as stream:
        child = subprocess.Popen([sys.executable,'-c',code,str(tmp_path)],cwd=ROOT,env=env,stdout=stream,stderr=subprocess.STDOUT)
        try:
            while child.poll() is None:
                memory = subprocess.run(['ps','-o','rss=','-p',str(child.pid)],text=True,capture_output=True).stdout.strip()
                if memory:
                    peak = max(peak,int(memory))
                    assert int(memory) <= 320*1024, 'process exceeded320MiB RSS budget'
                time.sleep(.05)
        finally:
            if child.poll() is None:
                child.kill()
            child.wait()
    assert child.returncode == 0, log.read_text()
    assert 'native bytes verified' in log.read_text()
    print(f'512MiB native plane: supervised RSS peak {peak/1024:.1f}MiB')



def test_mid_write_failure_preserves_previous_output(tmp_path, monkeypatch):
    task, _ = fixture(tmp_path, nx=513, ny=259)
    task.target.parent.mkdir()
    task.target.write_bytes(b'previous complete output')
    original = cog.read_plane
    calls = 0
    def fail_second_block(*args):
        nonlocal calls
        calls += 1
        if calls == 2:
            raise OSError('injected mid-write failure')
        return original(*args)
    monkeypatch.setattr(cog, 'read_plane', fail_second_block)
    with pytest.raises(OSError, match='mid-write'):
        cog.convert(task, blocksize=128, force=True)
    assert task.target.read_bytes() == b'previous complete output'
    assert list(task.target.parent.iterdir()) == [task.target]


def test_mixed_storage_types_and_unmapped_inputs_report_unsupported(tmp_path):
    task, _ = fixture(tmp_path, 'fixture', 'int32', names=['x'])
    with nc.Dataset(task.source, 'a') as ds:
        ds.createVariable('y', 'f4', ('lat','lon'), fill_value=-9999)[:] = 1
    task.rows.append(dict(task.rows[0],name='y',dtype='float32',record_index='2'))
    with pytest.raises(cog.Unsupported, match='mixed storage'):
        cog.convert(task, blocksize=128)
    task.rows = []
    with pytest.raises(cog.Unsupported, match='no registered numeric raster mapping'):
        cog.convert(task, blocksize=128)
    assert not task.target.exists()



def test_classic_netcdf_parameter_input(tmp_path):
    task, _ = fixture(tmp_path)
    replacement = task.source.with_suffix('.classic')
    with nc.Dataset(task.source) as src, nc.Dataset(replacement,'w',format='NETCDF3_64BIT_OFFSET') as dst:
        for name,d in src.dimensions.items():
            dst.createDimension(name,len(d))
        for name,v in src.variables.items():
            out = dst.createVariable(name,v.dtype,v.dimensions,fill_value=getattr(v,'_FillValue',None))
            out.setncatts({k:v.getncattr(k) for k in v.ncattrs() if k != '_FillValue'})
            out[:] = v[:]
    replacement.replace(task.source)
    assert cog.convert(task,blocksize=128).startswith('PASS')



@pytest.mark.parametrize('jobs', [1, 2])
def test_known_non_targets_skip_without_error_or_output(tmp_path, capsys, jobs):
    task, _ = fixture(tmp_path)
    root = task.source.parent.parent
    for name in cog.EXCLUDED_INPUTS:
        # Not even opened: known exclusions must not depend on table/container schema.
        (root/'netcdf'/name).write_bytes(b'non-target sentinel')
    options = ['--map-dir', str(root), '--resolutions', 'base', '--jobs', str(jobs), '--blocksize', '128']
    assert cog.main(options) == 0
    text = capsys.readouterr()
    assert '1 PASS; 3 SKIP; 0 UNSUPPORTED; 0 FAIL' in text.out
    assert 'UNSUPPORTED' not in text.err and 'FAIL' not in text.err
    for name, reason in cog.EXCLUDED_INPUTS.items():
        assert reason in text.out
        assert not (root/'COG'/Path(name).with_suffix('.tif')).exists()
        assert (root/'netcdf'/name).read_bytes() == b'non-target sentinel'
    assert cog.main(options + ['--variables', 'bifprm rivclim rivpar', '--force']) == 0
    assert '0 PASS; 3 SKIP; 0 UNSUPPORTED; 0 FAIL' in capsys.readouterr().out
    # An unexpected unmapped raster/file remains an error, rather than silently skipped.
    with nc.Dataset(root/'netcdf/unknown.nc', 'w'):
        pass
    assert cog.main(options) == 1
    assert 'UNSUPPORTED' in capsys.readouterr().err

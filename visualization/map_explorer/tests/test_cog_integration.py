"""COG LOD and scientific interaction contracts on small, known synthetic tiles."""
from pathlib import Path
from unittest.mock import Mock
import json
import os

import numpy as np
import pytest
from netCDF4 import Dataset
rasterio = pytest.importorskip('rasterio')
from rasterio.shutil import copy as raster_copy
from rasterio.enums import Resampling
from rasterio.transform import from_origin

from app import Explorer
from hires import discover_tiles, assignment
from hires_cog import COGSource, RasterCache, sampling
from hires_netcdf import NetCDFSource
from map_reader import Geometry, MapReader
from selection import visible_catchment_boundary


def write_tile(root, prefix='a', west=10, east=14, n=128, optional=True, directory_name='1min_nc'):
    # Full map extent; extra tiles can partition longitude with same native spacing.
    step = (east-west)/n
    ny = round(3/step)
    directory = root/directory_name
    directory.mkdir(exist_ok=True)
    arrays = {}
    yy,xx = np.indices((ny,n))
    arrays['catmxy'] = np.stack((np.floor((west-10+(xx+.5)*step)).astype('int16')+1,
                                np.floor((yy+.5)*step).astype('int16')+1))
    if n >= 64:
        arrays['catmxy'][:,30:40,30:40] = np.array([4,3])[:,None,None]
        arrays['catmxy'][:,2,2] = -999
        arrays['catmxy'][:,3,3] = -9999
        arrays['catmxy'][:,4,4] = [1,-9999]
    arrays['elevtn'] = ((xx+yy*n)/100).astype('float32')
    arrays['flddif'] = arrays['elevtn']/2
    arrays['visual'] = np.where(xx%3==0,10,7).astype('int8')
    arrays['uparea'] = ((xx+1)*1e5+yy).astype('float32')
    if optional:
        arrays['rivwth'] = (xx+1).astype('float32')
        arrays['catmz100'] = (xx%20).astype('int8')
    arrays['elevtn'][0,0] = -9999
    for name,data in arrays.items():
        names = ['catmxx','catmyy'] if name=='catmxy' else [name]
        planes = data if name=='catmxy' else data[None]
        path = directory/f'{prefix}.{name}.nc'
        units = 'm2' if name=='uparea' else 'code' if name=='visual' else '1' if planes.dtype.kind=='i' else 'm'
        fill = -9 if planes.dtype==np.dtype('int8') else -9999
        with Dataset(path,'w') as ds:
            ds.createDimension('lat',ny);ds.createDimension('lon',n)
            for axis,values in [('lon',west+(np.arange(n)+.5)*step),('lat',23-(np.arange(ny)+.5)*step)]:
                var=ds.createVariable(axis,'f8',(axis,));var.units='degrees_east' if axis=='lon' else 'degrees_north';var[:]=values
            for key,plane in zip(names,planes):
                var=ds.createVariable(key,plane.dtype,('lat','lon'),fill_value=fill);var.units=units;var[:]=plane
        cog = root/'COG/1min'/f'{prefix}.{name}.tif';cog.parent.mkdir(parents=True,exist_ok=True)
        stage = cog.with_suffix('.stage.tif')
        with rasterio.open(stage,'w',driver='GTiff',width=n,height=ny,count=len(planes),dtype=planes.dtype,
                           crs='EPSG:4326',transform=from_origin(west,23,step,step),nodata=fill,
                           tiled=True,blockxsize=128,blockysize=128) as ds:
            ds.write(planes);ds.update_tags(source_file=path.name)
            for i,key in enumerate(names,1):ds.update_tags(i,source_variable=key,units=units)
            ds.build_overviews([2,4,8,16],Resampling.nearest if planes.dtype.kind=='i' else Resampling.average)
        raster_copy(stage,cog,driver='COG',BLOCKSIZE=128,COMPRESS='DEFLATE',OVERVIEWS='FORCE_USE_EXISTING')
        stage.unlink()
    return arrays,(prefix,west,east,20,23,n,ny,step)


@pytest.fixture
def cog_map(map_dir,monkeypatch,tmp_path):
    monkeypatch.setenv('CMF_EXPLORER_STATS_CACHE',str(tmp_path/'stats'))
    arrays,area = write_tile(map_dir)
    prefix,w,e,s,n,nx,ny,step = area
    (map_dir/'1min_nc/location.txt').write_text(f'1 narea\niarea carea west east south north nx ny csize\n1 {prefix} {w} {e} {s} {n} {nx} {ny} {step}\n')
    return map_dir,arrays


def app_for(cog_map):
    root,arrays = cog_map
    app=Explorer(root,root.parent/'exports')
    app.background.value='catchment'
    app.map_viewport.bounds=[210,160]
    app.render_view()
    return app,arrays


def test_discovery_native_values_and_no_highres_netcdf(cog_map,monkeypatch):
    root,arrays=cog_map
    monkeypatch.setattr(NetCDFSource,'open',Mock(side_effect=AssertionError('highres NC opened')))
    monkeypatch.setattr(NetCDFSource,'read',Mock(side_effect=AssertionError('highres NC read')))
    tiles=discover_tiles(root,[]);tile=tiles['1min/a']
    assert tile.storage=='COG' and len(tile.cog)==7
    np.testing.assert_array_equal(tile.sample('catmxy',np.array([34]),np.array([34]))[:,0,0],[4,3])
    assert tile.sample('uparea',np.array([5]),np.array([6]))[0,0] == pytest.approx(arrays['uparea'][5,6]*1e-6)
    app,_=app_for(cog_map)
    assert app.point_select.value=='grid'
    app.set_extent((10.9,11.2,21.8,22.1))
    assert app.point_select.value=='catchment'
    app.inspect(10+34.5/32,23-34.5/32)
    assert app.selected==(2,3) and app.selection.native_pixel==(34,34)
    assert 'native hires elevtn [m]' in app._selection_values


def test_standard_location_csv_uses_current_netcdf_provenance(map_dir):
    arrays, area = write_tile(map_dir, directory_name='1min')
    prefix, west, east, south, north, nx, ny, step = area
    location = map_dir/'1min/location.csv'
    location.write_text(
        'iarea,carea,west,east,south,north,nx,ny,csize\n'
        f'1,{prefix},{west},{east},{south},{north},{nx},{ny},{step}\n'
    )

    messages = []
    tile = discover_tiles(map_dir, messages)['1min/a']

    assert not messages
    assert tile.storage == 'COG'
    for name in ('catmxy', 'visual'):
        assert tile.cog[name].netcdf_path == map_dir/'1min'/f'{prefix}.{name}.nc'
    np.testing.assert_array_equal(tile.sample('catmxy', np.array([34]), np.array([34]))[:, 0, 0], [4, 3])
    assert tile.sample('visual', np.array([3]), np.array([3]))[0, 0] == arrays['visual'][3, 3]


def test_overview_selection_both_axes_and_decimation(cog_map):
    tile=discover_tiles(cog_map[0],[])['1min/a'];g=tile.geometry
    wide=tile.display_plan('elevtn',g.extent,(16,12))
    assert wide.factor==8 and not wide.native
    assert tile.display('elevtn',wide).shape==(12,16)
    intermediate=tile.display_plan('elevtn',g.extent,(64,48))
    assert intermediate.factor==2
    detail=tile.display_plan('elevtn',(10,10.5,22.5,23),(64,64))
    assert detail.factor==1 and detail.native
    # Requesting the native band is insufficient if one axis still decimates.
    stretched=tile.display_plan('elevtn',g.extent,(1000,90))
    assert stretched.factor==1 and not stretched.native
    assert stretched.pixel_screen[1]<1
    assert sampling(g,g.extent,(10000,10000),()).shape[0]*sampling(g,g.extent,(10000,10000),()).shape[1] <= 2_000_000


def test_grid_click_never_samples_native_and_mode_crossing(cog_map,monkeypatch):
    app,_=app_for(cog_map)
    tile=next(iter(app.scene.tiles.values()))
    spy=Mock(wraps=tile.sample);monkeypatch.setattr(tile,'sample',spy)
    app.inspect(11.08,21.92)
    assert spy.call_count==0
    assert app.selected==(1,1) and app.selection.native_pixel is None
    assert not app.cell_inspector.pixel_section.visible
    app.set_extent((10.9,11.2,21.8,22.1))
    app.inspect(11.078125,21.921875)
    assert app.point_select.value=='catchment' and app.selected==(2,3)
    assert app.cell_inspector.pixel_section.visible
    app.set_extent(app.reader.geometry.extent)
    assert app.point_select.value=='grid' and app.selection.boundary is None
    assert app.selected==(1,1)


def test_invalid_assignments_and_optional_attributes(cog_map):
    app,_=app_for(cog_map)
    app.set_extent((10,10.3,22.7,23))
    for row,col,status in [(2,2,'unassigned land'),(3,3,'other background'),(4,4,'invalid pair')]:
        app.inspect(10+(col+.5)/32,23-(row+.5)/32)
        assert app.selected is None and app.selection.boundary is None
        assert app._selection_values['assignment status']==status
    tile=next(iter(app.scene.tiles.values()));tile.files.pop('rivwth');tile.cog.pop('rivwth')
    app.inspect(10.2,22.8)
    assert 'native hires rivwth [m]' not in app._selection_values


def test_palette_cache_source_invalidation_and_limits(cog_map):
    app,_=app_for(cog_map);tile=next(iter(app.scene.tiles.values()))
    counts=sum(s.io_reads for s in tile.cog.values())
    app.background_ui.opacity.value=55;app.render_view()
    app.terrain_palette.value='pale_terrain';app.render_view()
    assert sum(s.io_reads for s in tile.cog.values())==counts
    assert tile.cog['catmxy'].cache.bytes<=tile.cog['catmxy'].cache.max_bytes
    source=tile.cog['elevtn'];old=source.read(np.array([7]),np.array([8]))[0,0,0]
    # Value change on an existing COG is a synthetic cache invalidation fixture only.
    with rasterio.open(source.path,'r+',IGNORE_COG_LAYOUT_BREAK='YES') as ds:
        block=ds.read(1);block[7,8]+=1;ds.write(block,1)
    # Editing a COG breaks its layout marker, so it must be rejected rather than reused.
    with pytest.raises(ValueError,match='COG'):
        source.read(np.array([7]),np.array([8]))


def test_exact_stats_are_native_assigned_and_persistent(cog_map,monkeypatch):
    root,arrays=cog_map;tile=discover_tiles(root,[])['1min/a'];g=MapReader(root).geometry
    valid,_,_=assignment(*arrays['catmxy'],g)
    expected=np.percentile(arrays['elevtn'][valid & (arrays['elevtn']!=-9999)],(5,95))
    np.testing.assert_allclose(tile.percentiles('elevtn'),expected)
    tile2=discover_tiles(root,[])['1min/a']
    monkeypatch.setattr(tile2,'sample',Mock(side_effect=AssertionError('persistent cache missed')))
    np.testing.assert_allclose(tile2.percentiles('elevtn'),expected)


def test_visible_boundary_has_no_artificial_viewport_edges(cog_map):
    root,arrays=cog_map;tile=discover_tiles(root,[])['1min/a'];coarse=MapReader(root).geometry
    # This entire subwindow lies inside one geographic assignment, so no physical edges there.
    boundary=visible_catchment_boundary(tile,coarse,0,0,(10.3,10.5,22.5,22.7))
    assert len(boundary.segments)==0 and boundary.pixel_count>0 and not boundary.complete
    boundary=visible_catchment_boundary(tile,coarse,2,3,(10.85,11.3,21.7,22.15))
    assert len(boundary.segments)>=4


def test_older_cog_remains_preferred_after_netcdf_copy(cog_map):
    root, _ = cog_map
    newer = max(p.stat().st_mtime_ns for p in (root/'COG/1min').glob('*.tif')) + 10_000_000_000
    for path in (root/'1min_nc').glob('*.nc'):
        os.utime(path, ns=(newer, newer))
    notes = []
    tile = discover_tiles(root, notes)['1min/a']
    assert tile.storage == 'COG'
    assert set(tile.cog) == set(tile.files)
    assert all(path.suffix == '.tif' for path in tile.files.values())
    assert not tile.netcdf
    assert not any('fallback' in note for note in notes)


def test_missing_and_malformed_cog_fallback(cog_map):
    root,_=cog_map
    (root/'COG/1min/a.elevtn.tif').unlink()
    (root/'COG/1min/a.visual.tif').write_bytes(b'bad TIFF')
    notes=[];tile=discover_tiles(root,notes)['1min/a']
    assert tile.files['elevtn'].suffix=='.nc' and tile.files['visual'].suffix=='.nc'
    assert any('fallback' in x for x in notes)
    # No COG means Grid selection even in a native-size fallback view.
    for path in (root/'COG/1min').glob('*.tif'):path.unlink()
    app,_=app_for(cog_map)
    app.set_extent((10.9,11.2,21.8,22.1))
    assert app.point_select.value=='grid'


def test_multiple_tiles_display_cache_export_and_settings(map_dir,tmp_path,monkeypatch):
    monkeypatch.setenv('CMF_EXPLORER_STATS_CACHE',str(tmp_path/'stats'))
    _,a=write_tile(map_dir,'a',10,12,64)
    _,b=write_tile(map_dir,'b',12,14,64)
    text='2 narea\niarea carea west east south north nx ny csize\n'
    for i,(prefix,w,e,s,n,nx,ny,step) in enumerate((a,b),1):text+=f'{i} {prefix} {w} {e} {s} {n} {nx} {ny} {step}\n'
    (map_dir/'1min_nc/location.txt').write_text(text)
    app=Explorer(map_dir,tmp_path.parent/'multi_exports');app.background.value='elevtn';app.render_view()
    assert app.frame.background_count==2 and len(app.image_source.data['image'])==2
    plot=app.plot;extent=app.extent;state=app.settings();app.load(json.dumps(state).encode())
    assert app.plot is plot and app.extent==extent
    assert app.export().is_file()
    app.inspect(12.5,22.5)
    assert app.selection.tile_key=='1min/b'
    pin=app.pins.add();assert pin.mode=='catchment'
    app.close();assert not app.scene.tiles


def test_retina_frame_and_drawer_measurement(cog_map):
    from map_session import ExplorerSession
    root, _ = cog_map
    session = ExplorerSession(root, root.parent/'exports')
    app = session.active
    app.background.value = "catchment"
    # Bokeh batches frame dimensions and device ratio in a single event update.
    with app.map_viewport.param.update(bounds=[700, 500], pixel_ratio=2):
        app.render_view()
        assert app.frame.sampling
    session.dataset_toggle.value = True
    revision = app.map_viewport.layout_revision
    session.dataset_toggle.value = False
    assert app.map_viewport.layout_revision == revision + 1
    session.close()


def test_optional_cog_fallback_and_window_count_refresh(cog_map):
    root, _ = cog_map
    (root/'COG/1min/a.flddif.tif').unlink()
    app = Explorer(root, root.parent/'exports')
    app.background.value = 'flddif'
    app.set_extent(app.reader.geometry.extent)
    assert app.frame.layer is not None and app.point_select.value == 'grid'
    app.background.value = 'catchment'
    app.set_extent((10.9, 11.4, 21.6, 22.1))
    app.inspect(11.08, 21.92)
    assert app.selection.boundary is not None
    app.set_extent((11, 11.3, 21.7, 22))
    assert app._selection_values['unit catchment assigned pixel count'] == app.selection.boundary.pixel_count
    assert f"{app.selection.boundary.pixel_count:,} high-res pixels" in app.selection_summary.object
    app.close()



def test_sparse_statistics_use_bounded_native_assigned_samples(cog_map, monkeypatch):
    import hires
    root, arrays = cog_map
    monkeypatch.setattr(hires, 'EXACT_STATS_MAX_PIXELS', 1)
    tile = discover_tiles(root, [])['1min/a']
    reader = MapReader(root)
    calls = []
    original = tile.sample
    def bounded(name, rows, cols):
        assert len(rows) <= 16 and len(cols) <= 16
        if name == 'catmxy':
            calls.append((rows.copy(), cols.copy()))
        return original(name, rows, cols)
    monkeypatch.setattr(tile, 'sample', bounded)
    monkeypatch.setattr(hires.tempfile, 'TemporaryFile', Mock(side_effect=AssertionError('full-tile workspace')))
    low, high = tile.percentiles('elevtn')
    assert len(calls) == 144
    expected = []
    inherited_expected = []
    inherited = reader.read('uparea').astype(float).filled(np.nan)*1e-6
    for rows, cols in calls:
        x, y = arrays['catmxy'][:, rows[:, None], cols[None, :]]
        valid, _, _ = assignment(x, y, reader.geometry)
        values = arrays['elevtn'][rows[:, None], cols[None, :]]
        expected.extend(values[valid & np.isfinite(values) & (values != -9999)])
        inherited_expected.extend(inherited[y[valid]-1, x[valid]-1])
    np.testing.assert_allclose((low, high), np.percentile(expected, (5,95)))
    inherited_expected = np.asarray(inherited_expected)
    np.testing.assert_allclose(tile.percentiles('uparea', inherited=inherited),
                              np.percentile(inherited_expected[np.isfinite(inherited_expected)], (5,95)))
    assert len(calls) == 288
    # Persistent estimated limits do not read any pixels again.
    fresh = discover_tiles(root, [])['1min/a']
    monkeypatch.setattr(fresh, 'sample', Mock(side_effect=AssertionError('sparse cache missed')))
    np.testing.assert_allclose(fresh.percentiles('elevtn'), (low, high))


def test_sparse_policy_cache_separate_from_exact_and_log_uses_nonpositive(cog_map, monkeypatch):
    import hires
    root, arrays = cog_map
    tile = discover_tiles(root, [])['1min/a']
    tile.percentiles('elevtn')
    exact_keys = set(tile._stats)
    monkeypatch.setattr(hires, 'EXACT_STATS_MAX_PIXELS', 1)
    native = tile.sample
    def shifted(name, rows, cols):
        values = native(name, rows, cols)
        return values-50 if name == 'elevtn' else values
    monkeypatch.setattr(tile, 'sample', shifted)
    limits = tile.percentiles('elevtn')
    assert limits[0] < 0 < limits[1]
    assert len(set(tile._stats)-exact_keys) == 1
    from background_style import resolve_color_limits
    assert resolve_color_limits(*limits, True)[0] == .01


def test_large_map_sampling_keeps_display_and_manual_limits_usable(cog_map, monkeypatch):
    import hires
    monkeypatch.setattr(hires, 'EXACT_STATS_MAX_PIXELS', 1)
    monkeypatch.setattr(hires.tempfile, 'TemporaryFile', Mock(side_effect=AssertionError('full-tile workspace')))
    app, _ = app_for(cog_map)
    assert app.frame.layer is not None and app._background_error is None
    assert any('approximate P5/P95' in label for label in app.frame.legend)
    assert 'Approximate P5/P95' in app.background_ui.color_note.object
    app.set_extent((10.9,11.2,21.8,22.1))
    app.inspect(11.078125,21.921875)
    assert app.point_select.value == 'catchment' and app.selected == (2,3)
    app.highres_auto_limits.value = False
    app.highres_low.value, app.highres_high.value = 1, 12
    app.render_view()
    assert (app.frame.layer.low, app.frame.layer.high) == (1,12)
    assert not any('approximate P5/P95' in label for label in app.frame.legend)
    app.close()

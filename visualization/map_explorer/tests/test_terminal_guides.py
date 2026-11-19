"""Stored endpoint markers and native-window guide geometry without global scans."""
from unittest.mock import Mock

import numpy as np
from netCDF4 import Dataset

from app import Explorer
from conftest import install_test_cogs
from hires import assignment
from map_reader import MapReader
from map_products import Products
from river_network import RiverNetwork
from scene import Frame, Scene
from test_v2 import products


def test_minus10_markers_keep_links_and_code_pairs_distinct(products):
    root = products
    raw = np.fromfile(root/'nextxy.bin', dtype='<i4').reshape(2,3,4)
    raw[:,1,1] = -10
    raw[:,1,2] = [-10,2]  # mixed, not a paired terminal
    raw[:,1,3] = -9
    raw.tofile(root/'nextxy.bin')
    app = Explorer(root, root.parent/'terminal-exports')
    app.set_extent(app.reader.geometry.extent)
    app.representation.value = 'outlet_vector'
    outlon, outlat = app.scene.products.outlets
    np.testing.assert_array_equal(app.frame.terminal_points, [[outlon[1,1],outlat[1,1]]])
    assert app.terminal_renderer.glyph.marker == 'diamond'
    assert app.terminal_renderer.glyph.fill_color == '#D73027'
    assert app.terminal_renderer.glyph.size == 7
    assert app.mouth_renderer.glyph.size == 6 and app.mouth_renderer.glyph.fill_color == '#6489AE'
    np.testing.assert_array_equal(app.frame.mouth_points,
        [[outlon[0,2],outlat[0,2]],[outlon[1,3],outlat[1,3]]])
    assert app._network_cache.inspect(1,1)['downstream status'] == 'terminal (-10; no downstream link)'
    native = app._network_cache
    view = app.scene.products.network_view(native, 'outlet_vector')
    ids = view.visible(app.extent)
    expected = sorted(zip(view.x0[ids],view.y0[ids],view.x1[ids],view.y1[ids]))
    actual = sorted(zip(*(app.frame.main[k] for k in ('x0','y0','x1','y1'))))
    assert actual == expected  # endpoints add markers, never fabricate river links
    assert app.export().is_file()
    app.representation.value = 'grid_center'
    np.testing.assert_array_equal(app.frame.terminal_points, [[11.5,21.5]])
    app.representation.value = 'off'
    assert not len(app.terminal_source.data['x']) and not len(app.mouth_source.data['x'])
    app.close()
    # An invalid stored outlet is reported, not replaced with a grid center.
    with Dataset(root/'netcdf/lonlat.nc','a') as ds:
        ds['outlon'][1,1] = -9999
    app = Explorer(root, root.parent/'terminal-exports')
    app.representation.value = 'outlet_vector'
    assert not len(app.frame.terminal_points)
    assert any('no valid stored outlets' in x for x in app.frame.diagnostics)
    app.close()


def test_native_window_guides_match_centroids_and_cache_without_full_tile_index(products, monkeypatch):
    install_test_cogs(products)
    app = Explorer(products, products.parent/'guide-exports')
    app.background.value = 'catchment'
    app.set_extent(app.reader.geometry.extent)
    tile = next(iter(app.scene.tiles.values()))
    monkeypatch.setattr(tile, 'centroids', Mock(side_effect=AssertionError('full tile centroid scan')))
    app.overlay_controls['headwater'].value = True
    guides = next(o for o in app.frame.overlays if o.label.startswith('Headwater guides'))
    g = app.reader.geometry
    rows,cols = np.arange(tile.geometry.ny),np.arange(tile.geometry.nx)
    x,y = tile.sample('catmxy',rows,cols)
    valid,_,_ = assignment(x,y,g)
    heads = app.scene._headwater_masks[app.network_choice.value]
    outlon,outlat = app.scene.products.outlets
    expected = []
    for cell in np.flatnonzero(heads):
        row,col = divmod(cell,g.nx)
        rr,cc = np.where(valid & (x==col+1) & (y==row+1))
        if len(rr) and np.isfinite(outlon[row,col]) and np.isfinite(outlat[row,col]):
            expected.append([[np.mean(tile.geometry.lon[cc]),np.mean(tile.geometry.lat[rr])],
                             [outlon[row,col],outlat[row,col]]])
    np.testing.assert_allclose(guides.segments, expected)
    # Style-only redraw reuses the derived geometry; no native scan is repeated.
    native = tile.sample
    monkeypatch.setattr(tile,'sample',Mock(side_effect=AssertionError('guide cache missed')))
    app.render_view()
    monkeypatch.setattr(tile,'sample',native)
    app.set_extent((10.5,12.5,21,22.5))
    assert len(app.scene._guide_cache) == 2
    assert all(len(key[1]) == 4 for key in app.scene._guide_cache)
    # Wide/decimated display defers native guides instead of using overview labels.
    options = app.scene_options(); options['screen'] = (1,1)
    frame = app.scene.build(app.extent, app.variable.value, app.layer, app.network, options)
    assert not any(o.label.startswith('Headwater guides') for o in frame.overlays)
    assert any('zoom to native detail' in x for x in frame.diagnostics)
    app.close()
    assert not app.scene._guide_cache and not app.scene._headwater_masks


def test_periodic_native_guide_centroid_wraps_at_seam(tmp_path):
    (tmp_path/'params.txt').write_text('360\n1\n1\n1\n-180\n180\n0\n1\n')
    area = np.zeros((1,360),dtype='<f4');area[0,[0,359]]=1e6;area.tofile(tmp_path/'uparea.bin')
    x = np.full((1,360),-9999,dtype='<i4');y=x.copy()
    x[0,0]=360;y[0,0]=1;x[0,359]=y[0,359]=-10;x[0,358]=y[0,358]=-9
    np.stack((x,y)).tofile(tmp_path/'nextxy.bin')
    lon = np.full((1,360),-9999,dtype='<f4');lat=lon.copy()
    lon[0,0]=179.75;lon[0,359]=179.5;lon[0,358]=178.75;lat[0,[0,358,359]]=.5
    np.stack((lon,lat)).tofile(tmp_path/'lonlat.bin')
    high=tmp_path/'fine';high.mkdir()
    (high/'location.txt').write_text('1\nheader\n1 a -180 180 0 1 360 1 1\n')
    cat=np.full((2,1,360),-999,dtype='<i2');cat[:,0,[0,359]]=[[1,1],[1,1]]
    cat.tofile(high/'a.catmxy.bin')
    reader=MapReader(tmp_path);scene=Scene(reader);network=RiverNetwork(reader)
    view=scene.products.network_view(network,'outlet_vector')
    frame=Frame();scene._headwater_guides(frame,view,'fine/a',reader.geometry.extent,(720,100),1200)
    guide=frame.overlays[0].segments
    assert len(guide)==2 and np.all(np.abs(guide[:,1,0]-guide[:,0,0])<=.25)
    assert np.all(np.abs(guide[:,:,0])>=179.5)  # never an artificial Greenwich centroid
    scene._terminal_markers(frame,view,reader.geometry.extent)
    assert not len(frame.terminal_points) and not len(frame.mouth_points)  # world view
    exact=Frame();scene._terminal_markers(exact,view,(120,180,0,1))  # sixty coarse cells
    np.testing.assert_array_equal(exact.terminal_points,[[179.5,.5]])
    np.testing.assert_array_equal(exact.mouth_points,[[178.75,.5]])
    wide=Frame();scene._terminal_markers(wide,view,(119.9,180,0,1))
    assert not len(wide.terminal_points) and not len(wide.mouth_points)
    assert any('hidden above 60' in message for message in wide.diagnostics)

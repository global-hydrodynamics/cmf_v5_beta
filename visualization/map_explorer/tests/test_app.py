"""Programmatic GUI integration, scientific display state and reliable PNG export."""
import json
from pathlib import Path

import numpy as np
from PIL import Image
import pytest

from conftest import write_network
from app import Explorer, create_app
from config import load_settings
from map_layers import colorize, raster_subset
from map_reader import MapReader


def test_app_layer_inspection_extent_and_export(map_dir, tmp_path):
    write_network(map_dir)
    np.arange(12,dtype='<i4').reshape(3,4).tofile(map_dir/'basin.bin')
    app=Explorer(map_dir, tmp_path.parent/'exports')
    assert app.layer.logarithmic
    app.set_extent((11,13,20.5,22.5))
    app.variable.value='basin'
    assert app.extent == (11,13,20.5,22.5)
    assert not app.layer.logarithmic
    data=app.inspect(11.5,22.5)
    assert data['basin [1]'] == 1
    assert data['downstream status'] == 'flexible'
    app.network_choice.value='off'
    assert len(app.link_source.data['x0']) == 0
    assert app.inspect(11.5,22.5)['downstream status'] == 'flexible'
    app.network_choice.value='nextxy'
    app.area_width.value=True
    app.area_color.value=True
    path=app.export()
    with Image.open(path) as image:
        assert image.width > 500 and image.height > 500
        assert image.format == 'PNG'
    saved=app.save()
    app.variable.value='uparea'
    app.load(saved.read_bytes())
    assert app.variable.value == 'basin'
    assert app.extent == (11,13,20.5,22.5)
    assert app.area_width.value and app.area_color.value


def test_bokeh_raster_flip_and_subset(map_dir,tmp_path):
    app=Explorer(map_dir,tmp_path.parent/'exports')
    image=app.image_source.data['image'][0]
    expected=colorize(app.layer,np.array([[8.,1.]]))
    assert image[0,0] == expected[0,0]  # southernmost row first for Bokeh
    assert image[-1,0] == expected[0,1]
    subset,extent=raster_subset(app.layer,app.reader.geometry,(11,13,21,22))
    np.testing.assert_array_equal(subset,[[5,6]])
    assert extent == (11,13,21,22)


def test_error_feedback_and_no_output_in_map(map_dir):
    app=Explorer(map_dir,map_dir.parent/'exports')
    app.extent_inputs[0].value=100
    app._guard(app.apply_extent)
    assert 'Error' in app.status.object
    assert app.extent == app.reader.geometry.extent
    with pytest.raises(ValueError,match='outside'):
        Explorer(map_dir,map_dir/'output')
    assert 'Cannot open map' in create_app(map_dir/'absent').object


def test_settings_validation_before_mutation(map_dir):
    app=Explorer(map_dir,map_dir.parent/'exports')
    settings=app.settings()
    settings['network_options']['width']=float('nan')
    with pytest.raises(ValueError):
        load_settings(json.dumps(settings),app.reader)
    settings=app.settings();settings['map_path']='/another/map'
    with pytest.raises(ValueError,match='another map'):
        app.load(json.dumps(settings).encode())
    assert app.variable.value == 'uparea'


@pytest.mark.skipif(not (Path(__file__).resolve().parents[3]/'map/mekong_15min/params.txt').exists(), reason='Mekong map not beside application')
def test_mekong_integration(tmp_path):
    root=Path(__file__).resolve().parents[3]/'map/mekong_15min'
    app=Explorer(root,tmp_path)
    assert app.reader.geometry.nx == 80 and app.reader.geometry.ny == 120
    assert len(app.network.rows) > 0 and app.network.flexible.any()
    r=app.reader
    for name,source in r.sources.items():
        if (root/f'{name}.bin').exists():
            binary=np.fromfile(root/f'{name}.bin',dtype='<i4' if name in ('basin','bsncol') else '<f4').reshape(120,80)
            np.testing.assert_array_equal(r.read(name).filled(-9999),binary)
    for name in r.network_sources:
        binary=np.fromfile(root/f'{name}.bin',dtype='<i4').reshape(2,120,80)
        for record,actual in zip(binary,r.read_network(name)):
            np.testing.assert_array_equal(actual.filled(-9999),record)
    # Default coarse background selects its geographic grid; native assignment
    # codes remain separately inspectable and must not override this rule.
    lon,lat=105.8,10.8
    tile=app.scene.tiles[app.hires_source.value]
    rr,cc=tile.geometry.cell(lon,lat)
    x,y=map(int,tile.mmap('catmxy')[:,rr,cc])
    result=app.inspect(lon,lat)
    rr_geo,cc_geo=r.geometry.cell(lon,lat)
    assert result['ix (1-based)'] == cc_geo+1 and result['iy (1-based)'] == rr_geo+1
    assert result['assigned coarse ix (1-based)'] == x and result['assigned coarse iy (1-based)'] == y
    for name in r.sources:
        app.variable.value=name
        assert app.layer is not None and 'Error' not in app.status.object
    app.variable.value='uparea'
    assert app.export().is_file()

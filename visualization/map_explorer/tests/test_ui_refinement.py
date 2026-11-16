"""Explicit selection across backgrounds and distinct computational geometry."""

from pathlib import Path

import numpy as np
import pytest
from bokeh.models import HoverTool
from matplotlib.collections import LineCollection

from app import Explorer
from scene import export_scene
from test_v2 import products

BACKGROUNDS = ["none", "coarse", "catchment", "elevtn", "difference", "flddif"]


@pytest.mark.parametrize("mode", ["grid","catchment"])
@pytest.mark.parametrize("background", BACKGROUNDS)
def test_explicit_selection_and_independent_overlay(products, background, mode):
    path = products / "fine/tile.catmxy.bin"
    data = np.fromfile(path, dtype="<i2").reshape(2, 6, 8)
    data[:, 2:5, 1:5] = 1  # not the geographically containing coarse cell
    data[:, 3, 2] = 2  # hole, same geometry used across every background
    data.tofile(path)
    app = Explorer(products, products.parent / "exports")
    app.point_select.value = mode
    app.background.value = background
    app.overlay_controls["catchment_boundaries"].value = True
    normal = [entry[0] for entry in app.frame.overlays if "assignment boundaries" in entry[3]]
    assert len(normal) == 1 and len(normal[0]) > 0
    reference = normal[0].copy()
    app.scene.build(app.extent, app.variable.value, app.layer, app.network, app.scene_options(), max_side=2)
    info = app.inspect(11.000001, 21.999999)
    assert app.reader.geometry.cell(11.000001, 21.999999) == (1, 1)
    coarse = mode == 'grid'
    assert app.selected == ((1,1) if coarse else (0,0)) and app.selection.native_pixel == (2,2)
    pair = 2 if coarse else 1
    assert app.selection.boundary.pixel_count == int(((data[0]==pair)&(data[1]==pair)).sum())
    expected = np.array([[[11,22],[12,22]],[[12,22],[12,21]],[[12,21],[11,21]],[[11,21],[11,22]]]
                        if coarse else [[[10,23],[11,23]],[[11,23],[11,22]],[[11,22],[10,22]],[[10,22],[10,23]]])
    np.testing.assert_array_equal(app.selection.coarse_outline, expected)
    assert app.selected_coarse_renderer is not app.selection_boundary_renderer
    assert app.selected_coarse_renderer.glyph.line_dash == 'dashed'
    assert app.selected_coarse_renderer.glyph.line_color != app.selection_boundary_renderer.glyph.line_color
    assert "High-resolution ix (1-based, Fortran)" in app.inspection.object
    assert "Native assignment catmx" in app.inspection.object
    state = app.selection
    for other in BACKGROUNDS:
        app.background.value = other
        expected_cell = (1,1) if coarse else (0,0)
        assert app.selected == expected_cell
        if state.method == app.selection.method:
            assert app.selection is state
        normal = [entry[0] for entry in app.frame.overlays if "assignment boundaries" in entry[3]]
        np.testing.assert_array_equal(normal[0], reference)
        app.inspect(10.25, 22.75)  # -999 land: no stale selection/fallback
        if coarse:
            assert app.selected == (0,0) and app.selection.coarse_outline is not None
        else:
            assert app.selected is None and app.selection.boundary is None
            assert len(app.selected_coarse_source.data['x0']) == 0
        app.inspect(11.000001, 21.999999)
        assert app.selected == expected_cell
        state = app.selection
    app.overlay_controls["catchment_boundaries"].value = False
    assert len(app.selection_boundary_source.data["x0"]) > 0
    assert len(app.selected_coarse_source.data["x0"]) == 4


def test_ui_contracts_and_no_hires_fallback(map_dir):
    app = Explorer(map_dir, map_dir.parent / "exports")
    assert app.coordinate.text.startswith("Lon:")
    assert not app.plot.select(HoverTool)
    callbacks = app.plot.js_event_callbacks["mousemove"]
    assert len(callbacks) == 1 and callbacks[0].args["target"] is app.coordinate
    assert "Lon:" in callbacks[0].code and "Lat:" in callbacks[0].code
    assert app.overlay_controls["channel"].name == "Bifurcation Channel"
    assert app.overlay_controls["overland"].name == "Bifurcation Overland"
    assert app.overlay_controls["catchment_boundaries"].name == "Unit Catchment Boundaries"
    assert app.overlay_controls["catchment_boundaries"].disabled
    assert "no catmxy" in app.boundary_status.object
    app.inspect(11.25, 21.75)
    assert app.selected == (1, 1) and app.selection.boundary is None
    assert "no catmxy" in app.selection.status
    assert len(app.selected_coarse_source.data["x0"]) == 4
    app.overlay_controls["catchment_boundaries"].value = True
    assert any("need catmxy" in msg for msg in app.frame.diagnostics)


def test_png_receives_both_exact_selection_geometries(products, tmp_path, monkeypatch):
    app = Explorer(products, products.parent / "exports")
    app.inspect(11.25, 21.75)  # coarse background, native catchment now selected
    captured = []
    original = LineCollection.__init__

    def capture(self, segments, *args, **kwargs):
        if kwargs.get("zorder") in (9, 10):
            captured.append((kwargs["zorder"], np.array(segments)))
        original(self, segments, *args, **kwargs)

    monkeypatch.setattr(LineCollection, "__init__", capture)
    assert app.export().is_file()
    np.testing.assert_array_equal(dict(captured)[9], app.selection.coarse_outline)
    np.testing.assert_array_equal(dict(captured)[10], app.selection.boundary.segments)


ROOT = Path(__file__).resolve().parents[3]


@pytest.mark.skipif(not (ROOT / "map/mekong_15min/params.txt").exists(), reason="Mekong unavailable")
def test_mekong_all_backgrounds_assignment_and_rectangle(tmp_path):
    app = Explorer(ROOT / "map/mekong_15min", tmp_path)
    app.set_extent((104.5, 107, 9.5, 12))
    for mode,background in [(mode,bg) for mode in ("grid","catchment") for bg in BACKGROUNDS]:
        app.point_select.value = mode
        app.background.value = background
        app.overlay_controls["catchment_boundaries"].value = True
        info = app.inspect(105.8, 10.8)
        coarse = mode == 'grid'
        expected = (96,63) if coarse else (96,62)
        assert app.selected == expected
        tile = app.scene.tiles[app.hires_source.value]
        x,y = tile.mmap('catmxy')
        assert info['unit catchment assigned pixel count'] == np.count_nonzero((x==expected[1]+1)&(y==expected[0]+1))
        rectangle = app.selection.coarse_outline
        assert rectangle[0].tolist() == ([[105.75,11.0],[106.0,11.0]] if coarse else [[105.5,11.0],[105.75,11.0]])
    assert app.export().is_file()

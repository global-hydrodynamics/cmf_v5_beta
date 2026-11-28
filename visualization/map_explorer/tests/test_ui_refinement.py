"""Explicit selection across backgrounds and distinct computational geometry."""
from conftest import native_assignments

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
    app = Explorer(products, products.parent / "exports")
    app.point_select.value = mode  # Historical requests cannot override automatic mode.
    app.background.value = background
    app.overlay_controls["catchment_boundaries"].value = True
    assert app.point_select.value == "grid" and app.point_select.disabled
    assert not any("assignment boundaries" in entry[3] for entry in app.frame.overlays)
    info = app.inspect(11.000001,21.999999)
    assert app.selected == (1,1) and app.selection.native_pixel is None
    assert app.selection.boundary is None and not app.cell_inspector.pixel_section.visible
    expected = np.array([[[11,22],[12,22]],[[12,22],[12,21]],[[12,21],[11,21]],[[11,21],[11,22]]])
    np.testing.assert_array_equal(app.selection.coarse_outline,expected)
    assert app.selected_coarse_renderer is not app.selection_boundary_renderer
    assert app.selected_coarse_renderer.glyph.line_dash == 'dashed'
    for other in BACKGROUNDS:
        app.background.value = other
        assert app.selected == (1,1) and app.selection.boundary is None
        app.inspect(10.25,22.75)
        assert app.selected == (0,0)
        app.inspect(11.000001,21.999999)
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
    assert "Grid mode" in app.boundary_status.object
    app.inspect(11.25, 21.75)
    assert app.selected == (1, 1) and app.selection.boundary is None
    assert "Grid selected" in app.selection.status
    assert len(app.selected_coarse_source.data["x0"]) == 4
    app.overlay_controls["catchment_boundaries"].value = True
    assert any("Grid mode" in msg for msg in app.frame.diagnostics)


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
    assert 10 not in dict(captured) and app.selection.boundary is None


ROOT = Path(__file__).resolve().parents[3]


@pytest.mark.skipif(not (ROOT / "map/mekong_15min/params.nml").exists(), reason="Mekong unavailable")
def test_mekong_all_backgrounds_assignment_and_rectangle(tmp_path):
    app = Explorer(ROOT / "map/mekong_15min", tmp_path)
    app.set_extent((104.5, 107, 9.5, 12))
    for mode,background in [(mode,bg) for mode in ("grid","catchment") for bg in BACKGROUNDS]:
        app.point_select.value = mode
        app.background.value = background
        app.overlay_controls["catchment_boundaries"].value = True
        info = app.inspect(105.8, 10.8)
        coarse = app.point_select.value == 'grid'
        expected = (96,63) if coarse else (96,62)
        assert app.selected == expected
        tile = app.scene.tiles[app.hires_source.value]
        x,y = native_assignments(tile)
        if not coarse:
            r0,r1,c0,c1 = app.selection.boundary.bounds
            assert info['unit catchment assigned pixel count'] == np.count_nonzero((x[r0:r1,c0:c1]==expected[1]+1)&(y[r0:r1,c0:c1]==expected[0]+1))
        else:
            assert 'unit catchment assigned pixel count' not in info
        rectangle = app.selection.coarse_outline
        assert rectangle[0].tolist() == ([[105.75,11.0],[106.0,11.0]] if coarse else [[105.5,11.0],[105.75,11.0]])
    assert app.export().is_file()

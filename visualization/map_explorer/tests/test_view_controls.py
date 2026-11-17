from conftest import install_test_cogs
"""View translation, explicit frame policy and Gallery graphical contracts."""

import json
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest
from bokeh.events import RangesUpdate
from matplotlib.collections import LineCollection
from PIL import Image

from app import Explorer
from map_products import RIVER_GRADIENTS, area_style
from presets import PresetLibrary, VISIBLE_PRESETS
from test_river_controls import reference
from test_v2 import products
from view_controls import ASPECTS, aspect_extent, allocated_frame, geographic_ratio, translated_extent


@pytest.mark.parametrize("aspect", ASPECTS)
def test_frame_choice_keeps_center_scale_and_selection(products, aspect):
    app = Explorer(products, products.parent / "out")
    assert app.map_aspect.value == "square"
    assert abs(app.plot.frame_width / app.plot.frame_height - 1) < 0.003
    app.set_extent((11, 13, 21, 22))
    app.inspect(11.25, 21.75)
    selected = app.selection
    plot = app.plot
    app.map_aspect.value = aspect
    w, e, s, n = app.extent
    assert (w + e, s + n) == pytest.approx((24, 43))
    assert n - s == pytest.approx(1)
    assert geographic_ratio(app.extent) == pytest.approx(ASPECTS[aspect])
    assert abs(app.plot.frame_width / app.plot.frame_height - ASPECTS[aspect]) < 0.003
    assert app.selection is selected and app.plot is plot
    saved = app.settings()
    app.load(json.dumps(saved).encode())
    assert app.settings() == saved


def test_center_move_clamps_without_zoom_and_letterboxes(products):
    app = Explorer(products, products.parent / "out")
    app.set_extent((11, 13, 21, 22))
    app.map_aspect.value = "square"
    old = app.extent
    app.inspect(11.25, 21.75)
    selected = app.selection
    app.center_lon.value = 13.8
    app.center_lat.value = 22.8
    app.move_center()
    w, e, s, n = app.extent
    assert (e - w, n - s) == pytest.approx((old[1] - old[0], old[3] - old[2]))
    assert e == pytest.approx(14) and n == pytest.approx(23)
    assert "adjusted" in app.view_note.object
    assert app.map_aspect.value == "square" and app.selection is selected
    assert app.center_lon.value == (w + e) / 2 and app.center_lat.value == (s + n) / 2
    data, allocation = allocated_frame(app.extent, app.map_viewport.bounds, 1)
    assert allocation[0] == allocation[1] and data != allocation
    assert abs(data[0] - data[1] * geographic_ratio(app.extent)) <= 1
    before = app.extent
    app.center_lon.value = 99
    with pytest.raises(ValueError, match="outside"):
        app.move_center()
    assert app.extent == before
    app._navigation(RangesUpdate(app.plot, x0=11, x1=12, y0=21, y1=22))
    assert (app.center_lon.value, app.center_lat.value) == (11.5, 21.5)
    assert app.map_aspect.value == "square"
    app.set_extent((11, 13, 21, 22))
    assert app.map_aspect.value == "custom"


def test_legacy_extents_authoritative_and_bad_view_atomic(products):
    app = Explorer(products, products.parent / "out")
    app.set_extent((10.5, 13, 20.25, 22.75))
    for version in (1, 2):
        data = app.settings()
        data.pop("viewport")
        data["version"] = version
        app.load(json.dumps(data).encode())
        assert app.extent == tuple(data["extent"]) and app.map_aspect.value == "custom"
    for view in (
        {"aspect": "square", "frame_ratio": 2},
        {"aspect": "bogus", "frame_ratio": 1},
        {"aspect": "custom", "frame_ratio": float("nan")},
    ):
        before = app.settings()
        data = app.settings()
        data["viewport"] = view
        with pytest.raises(ValueError):
            app.load(json.dumps(data).encode())
        assert app.settings() == before


def test_translation_periodic_and_oversized():
    g = SimpleNamespace(west=-180, east=180, south=-90, north=90, periodic=True)
    extent = translated_extent((-10, 10, -5, 5), g, 370, 20)
    assert extent == pytest.approx((0, 20, 15, 25))
    with pytest.raises(ValueError, match="spans"):
        translated_extent((-200, 200, -5, 5), g, 0, 0)
    fit = aspect_extent((-180, 180, -90, 90), g, 4 / 3)
    assert geographic_ratio(fit) == pytest.approx(4 / 3)


@pytest.mark.parametrize("palette", RIVER_GRADIENTS)
@pytest.mark.parametrize("classification", ["continuous", "quartiles", "six_log"])
def test_gradient_mapping_geometry_and_manual_limits(palette, classification):
    net, reader, ids = reference()
    before = net._areas.copy()
    width, colors, _, _ = area_style(
        net, reader, ids, color_area=True, scale_width=True, classification=classification, area_palette=palette
    )
    assert colors[0].lower() == RIVER_GRADIENTS[palette][0].lower()
    assert colors[6].lower() == RIVER_GRADIENTS[palette][-1].lower()
    changed = area_style(
        net,
        reader,
        ids,
        color_area=True,
        scale_width=True,
        classification=classification,
        area_palette=palette,
        area_limits=[10, 1000],
    )
    np.testing.assert_array_equal(changed[0], width)
    np.testing.assert_array_equal(net._areas, before)
    if classification != "quartiles":
        assert changed[1][0] == changed[1][1] and changed[1][3] == changed[1][6]


def test_overlay_groups_and_disabled_styles_retain_preferences(products):
    app = Explorer(products, products.parent / "out")
    keys = ("catchment_boundaries", "channel_pixels", "channel", "overland", "outlets", "headwater", "coarse_grid")
    assert app.overlay_visibility.objects[1:] == [app.overlay_controls[k] for k in keys]
    for visible, style, value in [
        ("catchment_boundaries", "catchment_boundary_color", "#123456"),
        ("channel", "channel_color", "#123456"),
        ("overland", "overland_color", "#123456"),
        ("outlets", "outlet_size", 8),
    ]:
        app.overlay_controls[visible].value = True
        app.overlay_controls[style].value = value
        app.overlay_controls[visible].value = False
        assert app.overlay_controls[style].disabled and app.overlay_controls[style].value == value
        app.overlay_controls[visible].value = True
        assert not app.overlay_controls[style].disabled and app.overlay_controls[style].value == value


def test_selection_style_png_receives_identical_geometry(products, monkeypatch):
    install_test_cogs(products)
    app = Explorer(products, products.parent / "out")
    app.set_extent(app.reader.geometry.extent)
    app.background.value = "catchment"
    app.inspect(11.5, 22.5)
    native = app.selection.boundary.segments.copy()
    coarse = app.selection.coarse_outline.copy()
    assert app.selection_boundary_renderer.glyph.line_color == "#FF7F00"
    assert app.selection_boundary_renderer.glyph.line_width == 3
    assert app.selection_boundary_renderer.glyph.line_dash == "solid"
    assert app.selected_coarse_renderer.glyph.line_color == "#D8C8F0"
    assert app.selected_coarse_renderer.glyph.line_width == 3
    link = app.selected_link.data
    assert len(link["x1"]) == 1
    expected = (
        np.arctan2(
            link["y1"][0] - link["y0"][0], (link["x1"][0] - link["x0"][0]) * np.cos(np.deg2rad(sum(app.extent[2:]) / 2))
        )
        - np.pi / 2
    )
    assert link["angle"][0] == pytest.approx(expected)
    assert app.selected_arrow_renderer.glyph.fill_color == "#FFD400"
    assert app.selected_arrow_renderer.glyph.x == "x1" and app.selected_arrow_renderer.glyph.y == "y1"
    captured = {}
    original = LineCollection.__init__

    def capture(self, segments, *args, **kwargs):
        if kwargs.get("zorder") in (9, 10):
            captured[kwargs["zorder"]] = (np.asarray(segments), kwargs)
        original(self, segments, *args, **kwargs)

    monkeypatch.setattr(LineCollection, "__init__", capture)
    from matplotlib.axes import Axes

    arrows = []
    original_scatter = Axes.scatter

    def scatter(self, x, y, *args, **kwargs):
        if kwargs.get("zorder") == 8.2:
            arrows.append((x, y, kwargs))
        return original_scatter(self, x, y, *args, **kwargs)

    monkeypatch.setattr(Axes, "scatter", scatter)
    legends = []
    original_legend = Axes.legend

    def legend(self, *args, **kwargs):
        legends.extend(kwargs.get("handles", []))
        return original_legend(self, *args, **kwargs)

    monkeypatch.setattr(Axes, "legend", legend)
    assert app.export().is_file()
    selected = {h.get_label(): h for h in legends if h.get_label().startswith("Selected ")}
    coarse_key = "Selected computational coarse grid cell"
    native_key = next(k for k in selected if k.startswith("Selected stored"))
    assert selected[coarse_key].get_color() == "#D8C8F0" and selected[coarse_key].get_linestyle() == "--"
    assert selected[native_key].get_color() == "#FF7F00" and selected[native_key].get_linestyle() == "-"
    np.testing.assert_array_equal(captured[10][0], native)
    np.testing.assert_array_equal(captured[9][0], coarse)
    assert captured[10][1]["colors"] == "#FF7F00" and captured[9][1]["colors"] == "#D8C8F0"
    assert captured[9][1]["linewidths"] == 3 * 72 / 160
    assert app.selected_coarse_renderer.glyph.line_dash=="dashed"
    assert captured[10][1]["linewidths"] == 3 * 72 / 160
    assert len(arrows) == 1 and arrows[0][2]["c"] == ["#FFD400"]
    assert [arrows[0][0][0], arrows[0][1][0]] == pytest.approx([link["x1"][0], link["y1"][0]])
    app.raster_type.value = "highres"
    app.inspect(10.25, 22.75)
    assert not len(app.selected_link.data["angle"])


ROOT = Path(__file__).resolve().parents[3]


@pytest.mark.skipif(not (ROOT / "map/mekong_15min/params.txt").exists(), reason="Mekong unavailable")
def test_seven_visible_gallery_renderings_and_legacy_library(tmp_path):
    app = Explorer(ROOT / "map/mekong_15min", tmp_path)
    assert tuple(app.preset_choice.options.values()) == VISIBLE_PRESETS
    assert all(label.count(identity) == 1 for label, identity in app.preset_choice.options.items())
    assert len(PresetLibrary().presets) == 15
    app.set_extent((104.5, 107, 9.5, 12))
    plot = app.plot
    extent = app.extent
    for identity in VISIBLE_PRESETS:
        app.apply_preset(identity)
        assert app.extent == extent and app.plot is plot
        if identity == "p01-f01d":
            assert app.variable.value == "subcol" and not len(app.frame.main["x0"])
            assert any("bsncol display-class" in overlay.label for overlay in app.frame.overlays)
            assert app.scene_options()["background_method"] == "subbasin_context"
            rgba = app.frame.images[0][0].view("u1").reshape(*app.frame.images[0][0].shape, 4)
            assert np.any(np.all(rgba[:, :, :3] == 179, axis=2))
        if identity == "p01-f02a":
            assert app.network_choice.value == "nextxy"
            assert app.frame.paths["xs"] and len(app.frame.arrows["x"]) > 0
            lengths = list(map(len, app.frame.paths["xs"]))
            assert 2 in lengths and 17 in lengths
            assert "#f28e2b" in [c.lower() for c in app.frame.paths["color"]]
            for i, (xs, ys) in enumerate(zip(app.frame.paths["xs"], app.frame.paths["ys"])):
                assert [xs[0], ys[0], xs[-1], ys[-1]] == pytest.approx(
                    [app.frame.main[k][i] for k in ("x0", "y0", "x1", "y1")]
                )
            assert not len(app.link_source.data["x0"])
        if identity == "p01-f03c":
            assert app.network_choice.value == "nextxy" and app.representation.value == "outlet_vector"
            assert app.palette.value == "subcol_gray" and len(set(app.frame.main["color"])) > 4
            assert not len(app.frame.arrows["x"])
    app.apply_preset("p01-f01d")
    app.variable.value = "uparea"
    app.load(json.dumps(app.settings()).encode())
    assert app.scene_options()["background_method"] == "default"

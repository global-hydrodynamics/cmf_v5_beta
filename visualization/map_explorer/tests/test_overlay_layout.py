"""Stored-overlay scientific geometry, styles, pixel sizes and bounded viewport."""

import json
from pathlib import Path

import numpy as np
import pytest
from matplotlib.axes import Axes
from matplotlib.collections import LineCollection

from app import Explorer
from map_products import AREA_COLORS
from map_viewport import frame_size
from river_controls import RIVER_PALETTES
from scene import DASH_PIXELS
from test_v2 import products


def test_boundary_color_is_independent_of_selection_network_and_bifurcations(products):
    app = Explorer(products, products.parent / "out")
    app.inspect(11.25, 21.75)
    app.overlay_controls["catchment_boundaries"].value = True
    initial = next(o for o in app.frame.overlays if "assignment boundaries" in o.label)
    state = app.selection
    highlight = app.selection_boundary_renderer.glyph.line_color
    main = {key: np.array(values).copy() for key, values in app.frame.main.items()}
    app.overlay_controls["catchment_boundary_color"].value = "#0055cc"
    current = next(o for o in app.frame.overlays if "assignment boundaries" in o.label)
    np.testing.assert_array_equal(current.segments, initial.segments)
    assert current.color == "#0055cc" and current.dash == "solid"
    assert app.selection is state and app.selection_boundary_renderer.glyph.line_color == highlight == "#FF7F00"
    for key, values in main.items():
        np.testing.assert_array_equal(app.frame.main[key], values)
    app.background.value = "none"
    assert next(o for o in app.frame.overlays if "assignment boundaries" in o.label).color == "#0055cc"


def test_bifurcation_dashes_geometry_and_full_channel_width_quantiles(products):
    app = Explorer(products, products.parent / "out")
    segments = np.array([[[10.5, 22.5], [11.5, 21.5]]] * 8 + [[[11.5, 21.5], [12.5, 20.5]]] * 2)
    data = dict(app.scene.products.bifurcations)
    data.update(
        segments=segments,
        first_width=np.r_[2.0 ** np.arange(8), 0, 0],
        channel=np.r_[np.ones(8, bool), np.zeros(2, bool)],
    )
    app.scene.products.__dict__["bifurcations"] = data
    app.overlay_controls["channel"].value = app.overlay_controls["overland"].value = True
    channel = next(o for o in app.frame.overlays if o.dash == "dashed")
    overland = next(o for o in app.frame.overlays if o.dash == "dotted")
    np.testing.assert_array_equal(channel.segments, segments[:8])
    np.testing.assert_array_equal(overland.segments, segments[8:])
    np.testing.assert_array_equal(channel.width, [1.5, 1.5, 2.25, 2.25, 3, 3, 3.75, 3.75])
    np.testing.assert_array_equal(overland.width, [1.5, 1.5])
    assert app.overlay_renderers["dashed"].glyph.line_dash.value == [6, 3]
    assert app.overlay_renderers["dotted"].glyph.line_dash.value == [1, 3]
    app.bif_width_mode.value = False
    assert not app.overlay_controls["bif_classes"].value
    assert np.all(next(o for o in app.frame.overlays if o.dash == "dashed").width == 1.5)
    app.overlay_controls["bif_classes"].value = True
    assert app.bif_width_mode.value
    app.overlay_controls["channel"].value = False
    assert app.bif_width_mode.disabled


@pytest.mark.parametrize("size", [0, 4, 8, 16])
def test_outlet_pixel_sizes_positions_selection_and_png(products, monkeypatch, size):
    app = Explorer(products, products.parent / "out")
    app.inspect(11.25, 21.75)
    assert app.overlay_controls["outlet_size"].disabled
    app.overlay_controls["outlets"].value = True
    points = app.frame.points.copy()
    state = app.selection
    app.overlay_controls["outlet_size"].value = size
    assert app.selection is state and len(app.selected_source.data["x"]) == 1
    if size:
        np.testing.assert_array_equal(app.frame.points, points)
        np.testing.assert_array_equal(app.outlet_source.data["size"], np.full(len(points), size))
    else:
        assert len(app.frame.points) == 0
    captured = []
    original = Axes.scatter

    def capture(self, *args, **kwargs):
        if kwargs.get("facecolors") == "white":
            captured.append(kwargs["s"])
        return original(self, *args, **kwargs)

    monkeypatch.setattr(Axes, "scatter", capture)
    assert app.export().is_file()
    assert captured == ([(size * 72 / 160) ** 2] if size else [])
    app.overlay_controls["outlets"].value = False
    assert app.overlay_controls["outlet_size"].disabled and not len(app.frame.points)


def test_png_receives_typed_overlay_colors_and_absolute_dashes(products, monkeypatch):
    app = Explorer(products, products.parent / "out")
    for key in ("channel", "overland", "catchment_boundaries"):
        app.overlay_controls[key].value = True
    app.overlay_controls["catchment_boundary_color"].value = "#0055cc"
    captured = []
    original = LineCollection.__init__

    def capture(self, segments, *args, **kwargs):
        if kwargs.get("zorder") == 4:
            captured.append((np.array(segments), kwargs.copy()))
        original(self, segments, *args, **kwargs)

    monkeypatch.setattr(LineCollection, "__init__", capture)
    assert app.export().is_file() and len(captured) == len(app.frame.overlays)
    for overlay, (segments, kw) in zip(app.frame.overlays, captured):
        np.testing.assert_array_equal(segments, overlay.segments)
        assert kw["colors"] == overlay.color
        dash = DASH_PIXELS[overlay.dash]
        assert kw["linestyles"] == ((0, tuple(v * 72 / 160 for v in dash)) if dash else "solid")


@pytest.mark.parametrize("extent", [(10, 14, 21, 22), (11, 11.5, 20, 23), (11.1, 11.5, 21.1, 21.5)])
@pytest.mark.parametrize("bounds", [[900, 700], [500, 350]])
def test_actual_frame_fits_height_width_without_changing_extent_or_map_data(products, extent, bounds):
    app = Explorer(products, products.parent / "out")
    app.set_extent(extent)
    plot = app.plot
    data = {key: np.array(values).copy() for key, values in app.frame.main.items()}
    app.map_viewport.bounds = bounds
    assert app.plot is plot and app.extent == extent
    assert app.plot.frame_height <= bounds[1] - 85 and app.plot.frame_width <= bounds[0] - 150
    expected = (extent[1] - extent[0]) * np.cos(np.deg2rad((extent[2] + extent[3]) / 2)) / (extent[3] - extent[2])
    assert abs(app.plot.frame_width - app.plot.frame_height * expected) <= 1
    assert app.map_viewport.height == app.plot.frame_height + 90
    for key, values in data.items():
        np.testing.assert_array_equal(app.frame.main[key], values)
    assert frame_size(extent, bounds) == (app.plot.frame_width, app.plot.frame_height)


def test_exact_eight_palette_order_and_old_colors_remain_explicit(products):
    app = Explorer(products, products.parent / "out")
    app.color_mode.value = "upstream_area"
    assert list(app.river_ui.palette.options) == [
        "Shades_rainbow",
        "Turbo",
        "Blues",
        "YlGnBu",
        "plasma",
        "Blue → Navy",
        "Gray → Black",
        "Gray → White",
    ]
    assert app.river_ui.palette.options == RIVER_PALETTES
    assert app.river_ui.palette.value == "shade_rainbow"
    reference = app.frame.main["color"].copy()
    for palette in RIVER_PALETTES.values():
        app.river_ui.palette.value = palette
        assert app.network_options()["area_palette"] == palette
        app.color_mode.value = "connection_type"
        app.color_mode.value = "upstream_area"
        assert app.river_ui.palette.value == palette
    app.river_ui.palette.get_root()  # Exercise Panel live-model coercion, not only unmounted widgets.
    app.area_palette.value = "cividis"
    assert app.river_ui.palette.value is None and "cividis" in app.river_ui.legacy_palette.object
    assert app.network_options()["area_palette"] == "cividis"
    assert not np.array_equal(reference, app.frame.main["color"])
    saved = app.settings()
    app.load(json.dumps(saved).encode())
    assert app.settings() == saved
    assert app.river_ui.palette.value is None
    app.river_ui.palette.value = "turbo"
    assert app.area_palette.value == "turbo" and not app.river_ui.legacy_palette.visible
    assert "magma" in app.palette.options  # Background palettes remain unrestricted.


@pytest.mark.parametrize(
    "key,value",
    [
        ("outlet_size", -1),
        ("outlet_size", 21),
        ("outlet_size", float("nan")),
        ("outlet_size", 3.5),
        ("catchment_boundary_color", "blue"),
    ],
)
def test_overlay_settings_validate_before_mutation(products, key, value):
    app = Explorer(products, products.parent / "out")
    before = app.settings()
    data = app.settings()
    data["layers"]["overlays"][key] = value
    with pytest.raises(ValueError):
        app.load(json.dumps(data).encode())
    assert app.settings() == before


def test_overlay_roundtrip_and_defaults_for_older_files(products):
    app = Explorer(products, products.parent / "out")
    app.overlay_controls["catchment_boundary_color"].value = "#0055cc"
    app.overlay_controls["outlet_size"].value = 16
    app.bif_width_mode.value = False
    data = app.settings()
    app.load(json.dumps(data).encode())
    assert app.settings() == data
    data["layers"]["overlays"].pop("outlet_size")
    data["layers"]["overlays"].pop("catchment_boundary_color")
    app.load(json.dumps(data).encode())
    assert app.overlay_controls["outlet_size"].value == 4
    assert app.overlay_controls["catchment_boundary_color"].value == "#4A4A4A" and not app.bif_width_mode.value


ROOT = Path(__file__).resolve().parents[3]


@pytest.mark.skipif(not (ROOT / "map/mekong_15min/params.txt").exists(), reason="Mekong unavailable")
def test_mekong_gallery_legacy_palette_and_mixed_overlay_export(tmp_path):
    app = Explorer(ROOT / "map/mekong_15min", tmp_path)
    app.apply_preset("p01-f03a", use_gallery_extent=True)
    assert app.river_ui.palette.value is None and "viridis" in app.river_ui.legacy_palette.object
    assert set(app.frame.main["color"]) <= set(AREA_COLORS)
    assert len(app.river_ui.palette.options) == 8
    app.set_extent((104.5, 107, 9.5, 12))
    app.inspect(105.8, 10.8)
    app.overlay_controls["channel"].value = app.overlay_controls["overland"].value = True
    app.overlay_controls["catchment_boundaries"].value = True
    app.overlay_controls["outlets"].value = True
    app.overlay_controls["outlet_size"].value = 16
    assert {o.dash for o in app.frame.overlays} == {"solid", "dashed", "dotted"}
    assert app.export().is_file()

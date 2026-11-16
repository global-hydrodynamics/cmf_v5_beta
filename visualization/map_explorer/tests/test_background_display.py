"""Physical limits/norms, raster-only alpha, palette wiring and channel gating."""

import json
from pathlib import Path

import numpy as np
import pytest
from bokeh.models import LogColorMapper
from matplotlib.axes import Axes

from app import Explorer
from background_style import PALETTES, apply_opacity, validate_style
from hires import Tile
from test_v2 import products


def rgba(values):
    values = np.ascontiguousarray(values)
    return values.view("u1").reshape((*values.shape, 4))


@pytest.mark.parametrize("opacity", [0, 0.3, 1])
def test_alpha_preserves_existing_transparency(opacity):
    source = np.array([[[12, 34, 56, 0], [12, 34, 56, 128], [12, 34, 56, 255]]], dtype="u1").view("<u4").reshape(1, 3)
    result = rgba(apply_opacity(source, opacity))
    np.testing.assert_array_equal(result[..., :3], rgba(source)[..., :3])
    np.testing.assert_array_equal(result[..., 3], np.rint(np.array([[0, 128, 255]]) * opacity))
    assert rgba(source)[0, 1, 3] == 128


@pytest.mark.parametrize("mode", ["coarse", "catchment", "elevtn", "flddif", "difference"])
def test_opacity_changes_only_raster_not_colorbar_or_selection(products, mode):
    app = Explorer(products, products.parent / "exports")
    app.background.value = mode
    app.inspect(11.25, 21.75)
    original = rgba(app.frame.images[0][0]).copy()
    state = app.selection
    limits = (app.mapper.low, app.mapper.high)
    links = {key: np.array(values).copy() for key, values in app.frame.main.items()}
    app.background_opacity.value = 30
    current = rgba(app.frame.images[0][0])
    np.testing.assert_array_equal(current[..., :3], original[..., :3])
    np.testing.assert_array_equal(current[..., 3], np.rint(original[..., 3].astype(float) * 0.3))
    assert app.selection is state and (app.mapper.low, app.mapper.high) == limits
    for key, values in links.items():
        np.testing.assert_array_equal(app.frame.main[key], values)
    app.background_opacity.value = 0
    assert not rgba(app.frame.images[0][0])[..., 3].any()


def test_channel_pixels_highres_only_and_independent_alpha(products):
    app = Explorer(products, products.parent / "exports")
    channels = app.overlay_controls["channel_pixels"]
    assert channels.visible and channels.disabled
    assert channels not in app.background_ui.view.objects and channels in app.overlay_visibility.objects
    app.raster_type.value = "highres"
    channels.value = True
    assert channels.visible and not channels.disabled and len(app.frame.images) == 2
    pixels = app.frame.images[1][0].copy()
    np.testing.assert_array_equal(rgba(pixels)[1, 0], [131, 198, 237, 255])
    np.testing.assert_array_equal(rgba(pixels)[1, 1], [199, 166, 221, 255])
    assert rgba(pixels)[0, 0, 3] == 0
    app.background_opacity.value = 0
    np.testing.assert_array_equal(app.frame.images[1][0], pixels)
    app.raster_type.value = "coarse"
    assert channels.value and channels.visible and channels.disabled
    assert len(app.frame.images) == 1
    app.raster_type.value = "highres"
    assert channels.value and len(app.frame.images) == 2
    tile = app.scene.tiles[app.hires_source.value]
    app.scene.tiles["no_visual"] = Tile(
        "no_visual",
        tile.directory,
        tile.prefix,
        tile.geometry,
        {key: path for key, path in tile.files.items() if key != "visual"},
    )
    app.hires_source.options = list(app.scene.tiles)
    app.hires_source.value = "no_visual"
    assert channels.disabled and len(app.frame.images) == 1
    assert "no visual" in app.background_ui.channel_note.object


@pytest.mark.parametrize("palette", list(PALETTES.values()))
def test_catchment_palettes_change_colors_not_assignments(products, palette):
    app = Explorer(products, products.parent / "exports")
    app.raster_type.value = "highres"
    app.inspect(11.25, 21.75)
    state = app.selection
    data = app.frame.layer.image.copy()
    original = app.frame.images[0][0].copy()
    app.highres_palette.value = palette
    np.testing.assert_array_equal(app.frame.layer.image, data)
    assert app.selection is state and app.frame.layer.logarithmic
    if palette != "gallery":
        assert not np.array_equal(original, app.frame.images[0][0])
    app.highres_variable.value = "elevtn"
    app.highres_variable.value = "catchment"
    assert app.highres_palette.value == palette


@pytest.mark.parametrize("mode", ["elevtn", "flddif", "difference"])
@pytest.mark.parametrize("scale", ["gallery", "linear", "log"])
def test_terrain_physical_limits_and_explicit_log_mask(products, mode, scale):
    app = Explorer(products, products.parent / "exports")
    app.raster_type.value = "highres"
    app.highres_variable.value = mode
    app.highres_palette.value = "viridis"
    app.highres_scale.value = scale
    tile = app.scene.tiles[app.hires_source.value]
    native = tile.sample(mode, np.arange(6), np.arange(8))
    expected = ~np.isfinite(native) | ((native <= 0) if scale == "log" else False)
    np.testing.assert_array_equal(np.isnan(app.frame.layer.image), expected)
    reference = tile.percentiles(mode, positive=scale == "log")
    assert (app.frame.layer.low, app.frame.layer.high) == reference
    app.set_extent((11, 13, 20.5, 22.5))
    assert (app.frame.layer.low, app.frame.layer.high) == reference
    app.highres_auto_limits.value = False
    app.highres_high.value = 100
    app.highres_low.value = 1 if scale == "log" else -10
    assert (app.mapper.low, app.mapper.high) == (1 if scale == "log" else -10, 100)
    assert isinstance(app.mapper, LogColorMapper) == (scale == "log")
    assert "m" in app.bar.title
    assert any("manual limits" in text for text in app.frame.legend)


def test_catchment_linear_log_manual_and_independent_preferences(products):
    app = Explorer(products, products.parent / "exports")
    app.raster_type.value = "highres"
    app.highres_palette.value = "YlGnBu"
    app.highres_scale.value = "linear"
    app.highres_auto_limits.value = False
    app.highres_high.value = 8
    app.highres_low.value = 2
    assert not app.frame.layer.logarithmic and (app.mapper.low, app.mapper.high) == (2, 8)
    app.highres_scale.value = "log"
    assert app.frame.layer.logarithmic and (app.mapper.low, app.mapper.high) == (2, 8)
    app.highres_low.value = 0
    assert "positive" in app.status.object
    app.highres_low.value = 1
    assert "Error" not in app.status.object
    app.highres_variable.value = "elevtn"
    app.highres_palette.value = "gray"
    app.highres_variable.value = "catchment"
    assert app.highres_palette.value == "YlGnBu" and app.highres_scale.value == "log"
    assert (app.highres_low.value, app.highres_high.value) == (1, 8)


@pytest.mark.parametrize(
    "style",
    [
        {"palette": "unknown"},
        {"limits": [2, 2]},
        {"limits": [5, 1]},
        {"limits": [0, 10], "scale": "log"},
        {"limits": [float("nan"), 10]},
    ],
)
def test_invalid_highres_saved_style_is_rejected_before_mutation(products, style):
    app = Explorer(products, products.parent / "exports")
    before = app.settings()
    candidate = app.settings()
    candidate["layers"]["highres_style"] = style
    with pytest.raises(ValueError):
        app.load(json.dumps(candidate).encode())
    assert app.settings() == before


def test_saved_controls_and_png_alpha_handoff(products, monkeypatch):
    app = Explorer(products, products.parent / "exports")
    app.raster_type.value = "highres"
    app.highres_palette.value = "magma"
    app.highres_scale.value = "linear"
    app.highres_auto_limits.value = False
    app.highres_high.value = 20
    app.highres_low.value = 1
    app.overlay_controls["channel_pixels"].value = True
    app.background_opacity.value = 30
    saved = app.settings()
    other = Explorer(products, products.parent / "exports-2")
    other.load(json.dumps(saved).encode())
    assert other.settings() == saved
    assert other.background_opacity.value == 30 and other.highres_palette.value == "magma"
    images = []
    original = Axes.imshow

    def capture(self, image, *args, **kwargs):
        images.append(np.array(image))
        return original(self, image, *args, **kwargs)

    monkeypatch.setattr(Axes, "imshow", capture)
    assert app.export().is_file() and len(images) == 2
    np.testing.assert_array_equal(images[0], rgba(app.frame.images[0][0]))
    np.testing.assert_array_equal(images[1], rgba(app.frame.images[1][0]))
    assert images[0][1, 0, 3] == 76 and images[1][1, 0, 3] == 255


ROOT = Path(__file__).resolve().parents[3]


@pytest.mark.skipif(not (ROOT / "map/mekong_15min/params.txt").exists(), reason="Mekong unavailable")
def test_mekong_display_controls_and_preset_defaults(tmp_path):
    app = Explorer(ROOT / "map/mekong_15min", tmp_path)
    app.set_extent((104.5, 107, 9.5, 12))
    app.raster_type.value = "highres"
    app.inspect(105.8, 10.8)
    state = app.selection
    for palette in ("gallery", "gray", "viridis", "YlGnBu"):
        app.highres_palette.value = palette
        assert app.selection is state
    app.highres_variable.value = "elevtn"
    app.highres_scale.value = "linear"
    app.highres_auto_limits.value = False
    app.highres_high.value = 50
    app.highres_low.value = 0
    assert (app.mapper.low, app.mapper.high) == (0, 50)
    app.highres_low.value = 1
    app.highres_scale.value = "log"
    assert app.frame.layer.logarithmic
    app.background_opacity.value = 30
    assert app.export().is_file()
    expected = app.apply_preset("p01-f04b")
    assert app.settings() == expected and app.background_opacity.value == 100
    assert app.highres_palette.value == "gallery" and app.highres_scale.value == "gallery"
    assert app.overlay_controls["channel_pixels"].value and len(app.frame.images) == 2

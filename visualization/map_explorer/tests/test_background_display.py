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
def test_opacity_matches_raster_and_colorbar_without_changing_selection(products, mode):
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
    assert app.bar.scale_alpha == app.frame.background_opacity == 0.3
    assert app.bar.background_fill_color == app.plot.background_fill_color
    for key, values in links.items():
        np.testing.assert_array_equal(app.frame.main[key], values)
    app.background_opacity.value = 0
    assert not rgba(app.frame.images[0][0])[..., 3].any()
    assert app.bar.scale_alpha == app.frame.background_opacity == 0
    app.background_opacity.value = 100
    assert app.bar.scale_alpha == app.frame.background_opacity == 1
    assert app.selection is state and (app.mapper.low, app.mapper.high) == limits


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
def test_terrain_physical_limits_and_explicit_log_floor(products, mode, scale):
    app = Explorer(products, products.parent / "exports")
    app.raster_type.value = "highres"
    app.highres_variable.value = mode
    app.highres_palette.value = "viridis"
    app.highres_scale.value = scale
    tile = app.scene.tiles[app.hires_source.value]
    native = tile.sample(mode, np.arange(6), np.arange(8))
    expected = ~np.isfinite(native) | ((native<=0) if scale=="log" else False)
    np.testing.assert_array_equal(np.isnan(app.frame.layer.image), expected)
    reference = tile.percentiles(mode)
    if scale == "log":
        low = reference[0] if reference[0] > 0 else .01
        if reference[1] <= low:
            assert app._background_error is not None and not app.image_source.data["image"]
        else:
            reference = (low, reference[1])
            assert (app.frame.layer.low, app.frame.layer.high) == reference
            app.set_extent((11, 13, 20.5, 22.5))
            assert (app.frame.layer.low, app.frame.layer.high) == reference
    else:
        from map_layers import resolve_color_limits
        reference = resolve_color_limits(*reference)
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
    assert "Error" in app.status.object
    assert app.highres_low.value == 0 and not app.image_source.data["image"]
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
        {"limits": [1, 2, 3], "scale": "log"},
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


def test_channel_pixels_have_a_separate_browser_layer_through_view_updates(products):
    app = Explorer(products, products.parent / "channel-layer")
    channels = app.overlay_controls["channel_pixels"]
    app.raster_type.value = "highres"
    channels.value = True
    assert app.raster.level == "image"
    assert app.channel_raster.level == "underlay"
    assert app.channel_raster.data_source is app.channel_image_source
    assert app.plot.renderers.index(app.raster) < app.plot.renderers.index(app.channel_raster)
    assert app.plot.renderers.index(app.channel_raster) < app.plot.renderers.index(app.overlay_renderers["solid"])

    for variable in ("elevtn", "flddif", "difference"):
        app.highres_variable.value = variable
        for opacity in (100, 0, 50):
            app.background_opacity.value = opacity
            assert len(app.image_source.data["image"]) == 1
            assert len(app.channel_image_source.data["image"]) == 1
            np.testing.assert_array_equal(app.image_source.data["image"][0], app.frame.images[0][0][::-1])
            np.testing.assert_array_equal(app.channel_image_source.data["image"][0], app.frame.images[1][0][::-1])
            assert np.any(rgba(app.channel_image_source.data["image"][0])[..., 3] == 255)

    channels.value = False
    assert not app.channel_image_source.data["image"]
    channels.value = True
    app.raster_type.value = "coarse"
    assert channels.value and not app.channel_image_source.data["image"]
    app.raster_type.value = "highres"
    assert len(app.channel_image_source.data["image"]) == 1


def test_sampled_channel_pixels_report_loss_of_thin_features(products):
    app = Explorer(products, products.parent / "sampled-channel")
    app.raster_type.value = "highres"
    app.overlay_controls["channel_pixels"].value = True
    frame = app.scene.build(app.extent, app.variable.value, app.layer, app.network, app.scene_options(), max_side=2)
    assert any("Channel Pixels are sampled" in message for message in frame.diagnostics)
    assert not any("Channel Pixels are sampled" in message for message in app.frame.diagnostics)


def test_log_clips_below_manual_minimum_without_mutating_native_values(products):
    from map_layers import colorize
    app = Explorer(products, products.parent / "log-floor")
    app.raster_type.value = "highres"
    app.highres_variable.value = "elevtn"
    tile = app.scene.tiles[app.hires_source.value]
    native = tile.sample("elevtn", np.arange(6), np.arange(8)).copy()
    app.highres_scale.value = "log"
    app.highres_auto_limits.value = False
    app.highres_high.value = 100
    app.highres_low.value = 0.1
    layer = app.frame.layer
    valid = np.isfinite(native) & (native>0)
    np.testing.assert_array_equal(layer.image[valid], np.maximum(native[valid], 0.1))
    np.testing.assert_array_equal(np.isnan(layer.image), ~valid)
    np.testing.assert_array_equal(tile.sample("elevtn", np.arange(6), np.arange(8)), native)
    colors = colorize(layer, layer.image)
    minimum_color = colorize(layer, np.array([[0.1]]))[0, 0]
    assert np.all(colors[valid & (native < 0.1)] == minimum_color)
    app.highres_low.value = -10
    assert app.highres_low.value == -10 and "Error" in app.status.object
    app.highres_low.value=.1
    assert "Error" not in app.status.object
    assert app.export().is_file()  # PNG uses the same clipped display data/limits.


def test_log_all_nonpositive_reference_remains_displayable(products):
    data = np.zeros((6, 8), dtype="<f4")
    data[1, 1] = -3
    data[0, 1] = -9999
    path = products / "fine/tile.elevtn.bin"
    data.tofile(path)
    before = path.read_bytes()
    app = Explorer(products, products.parent / "nonpositive-log")
    app.raster_type.value = "highres"
    app.highres_variable.value = "elevtn"
    app.highres_scale.value = "log"
    assert "logarithmic color range" in app.status.object
    assert not app.image_source.data["image"]
    with pytest.raises(ValueError,match="logarithmic"):
        app.export()
    app.highres_auto_limits.value=False
    app.highres_low.value=.01
    app.highres_high.value=1
    assert np.isnan(app.frame.layer.image).all()  # nonpositive values are masked, never invented
    assert path.read_bytes()==before
    assert app.export().is_file()


@pytest.mark.parametrize("opacity", [0, 30, 100])
@pytest.mark.parametrize("categorical", [False, True])
def test_png_colorbar_uses_background_opacity_and_matching_underlay(products, monkeypatch, opacity, categorical):
    from matplotlib.figure import Figure
    from matplotlib.colors import to_rgba
    if categorical:
        np.arange(12, dtype="<i4").tofile(products / "basin.bin")
    app = Explorer(products, products.parent / "alpha-colorbar")
    if categorical:
        app.variable.value = "basin"
    else:
        app.raster_type.value = "highres"
        app.highres_variable.value = "elevtn"
        app.highres_scale.value = "log"
    app.background_opacity.value = opacity
    limits = (app.mapper.low, app.mapper.high)
    captured = []
    original = Figure.colorbar

    def capture(self, *args, **kwargs):
        bar = original(self, *args, **kwargs)
        captured.append((bar, kwargs["alpha"]))
        return bar

    monkeypatch.setattr(Figure, "colorbar", capture)
    assert app.export().is_file()
    assert len(captured) == 1
    bar, alpha = captured[0]
    assert alpha == bar.alpha == bar.solids.get_alpha() == opacity / 100
    assert bar.ax.get_facecolor() == to_rgba(app.plot.background_fill_color)
    assert (bar.norm.vmin, bar.norm.vmax) == limits
    assert app.bar.scale_alpha == opacity / 100


@pytest.mark.parametrize("opacity", [0, 0.5, 1])
def test_channel_pixels_opacity_matches_browser_png_and_preserves_other_layers(products, opacity, monkeypatch):
    app = Explorer(products, products.parent / "channel-opacity")
    app.raster_type.value = "highres"
    app.overlay_controls["channel_pixels"].value = True
    slider = app.overlay_controls["channel_pixels_opacity"]
    assert slider in app.overlay_styles.objects and not slider.disabled
    assert slider.start == 0 and slider.end == 1 and slider.value == 1
    base = app.frame.images[0][0].copy()
    original = rgba(app.frame.images[1][0]).copy()
    app.inspect(11.25, 21.75)
    selection, extent, plot = app.selection, app.extent, app.plot
    slider.value = opacity
    channel = rgba(app.frame.images[1][0])
    np.testing.assert_array_equal(channel[..., :3], original[..., :3])
    np.testing.assert_array_equal(channel[..., 3], np.rint(original[..., 3].astype(float) * opacity))
    np.testing.assert_array_equal(app.frame.images[0][0], base)
    np.testing.assert_array_equal(app.channel_image_source.data["image"][0], app.frame.images[1][0][::-1])
    assert app.selection is selection and app.extent == extent and app.plot is plot
    images = []
    original_imshow = Axes.imshow
    def capture(ax, image, *args, **kwargs):
        images.append(np.array(image).copy())
        return original_imshow(ax, image, *args, **kwargs)
    monkeypatch.setattr(Axes, "imshow", capture)
    assert app.export().is_file()
    np.testing.assert_array_equal(images[1], channel)
    app.overlay_controls["channel_pixels"].value = False
    assert slider.disabled and slider.value == opacity
    app.overlay_controls["channel_pixels"].value = True
    assert not slider.disabled and slider.value == opacity
    saved = app.settings()
    app.load(json.dumps(saved).encode())
    assert slider.value == opacity
    saved["layers"]["overlays"].pop("channel_pixels_opacity")
    app.load(json.dumps(saved).encode())
    assert slider.value == 1  # Older JSON remains opaque.


@pytest.mark.parametrize("value", [-0.1, 1.1, True, "0.5", float("nan"), float("inf")])
def test_channel_pixel_opacity_invalid_json_does_not_mutate(products, value):
    app = Explorer(products, products.parent / "channel-opacity-invalid")
    before = app.settings()
    bad = app.settings()
    bad["layers"]["overlays"]["channel_pixels_opacity"] = value
    with pytest.raises(ValueError, match="Channel Pixels opacity"):
        app.load(json.dumps(bad).encode())
    assert app.settings() == before

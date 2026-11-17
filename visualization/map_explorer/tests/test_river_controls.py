"""Independent area encodings, legacy Gallery colors and pixel-size arrow handoff."""

import json
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest
from matplotlib import colormaps
from matplotlib.axes import Axes
from matplotlib.colors import to_hex

from app import Explorer
from map_products import AREA_COLORS, AREA_PALETTES, RIVER_GRADIENTS, area_style
from test_v2 import products


def reference():
    areas = np.array([1, 10, 100, 1000, 10000, 100000, 1000000, 0, np.nan], float)
    network = SimpleNamespace(_areas=areas, link_index=np.arange(9), flexible=np.arange(9) % 2 == 1)
    return network, SimpleNamespace(), np.arange(9)


@pytest.mark.parametrize("palette", AREA_PALETTES)
def test_quantile_palette_and_explicit_gallery_exception(palette):
    n, r, ids = reference()
    widths, colors, legend, _ = area_style(
        n, r, ids, classification="quartiles", area_palette=palette, color_area=True, scale_width=True
    )
    np.testing.assert_allclose(widths[:7], [1, 1, 5 / 3, 7 / 3, 7 / 3, 3, 3])
    assert len(set(colors[:7])) == 4 and colors[-1] == "#888888"
    if palette in RIVER_GRADIENTS:
        assert colors[0].lower() == RIVER_GRADIENTS[palette][0].lower()
        assert colors[6].lower() == RIVER_GRADIENTS[palette][-1].lower()
    elif palette != "shade_rainbow":
        assert colors[0] == to_hex(colormaps[palette](0.0))
        assert colors[6] == to_hex(colormaps[palette](1.0))
    old = area_style(
        n,
        r,
        ids,
        classification="quartiles",
        area_palette=palette,
        color_area=True,
        area_color_style="gallery_quartiles",
    )[1]
    assert old[0] == AREA_COLORS[0] and old[6] == AREA_COLORS[3]
    assert any("31.6" in label for label in legend)  # 10**1.5, not equal log intervals


@pytest.mark.parametrize("mapping", ["continuous", "six_log"])
def test_manual_colors_clip_without_changing_width_or_links(mapping):
    n, r, ids = reference()
    kw = dict(classification=mapping, color_area=True, scale_width=True, area_palette="plasma")
    w, c, _, _ = area_style(n, r, ids, **kw)
    w2, c2, labels, _ = area_style(n, r, ids, area_limits=[10, 1000], **kw)
    np.testing.assert_array_equal(w2, w)
    assert len(c2) == len(ids) and c2[0] == c2[1] and c2[3] == c2[6]
    assert not np.array_equal(c2, c) and any("Color:" in x for x in labels)
    if mapping == "six_log":
        np.testing.assert_allclose(w[:7], [1, 1.4, 1.8, 2.2, 2.6, 3, 3])
    else:
        np.testing.assert_allclose(w[:7], [1, 4 / 3, 5 / 3, 2, 7 / 3, 8 / 3, 3])
    subset = np.array([2, 4, 6])
    ws, cs, _, _ = area_style(n, r, subset, area_limits=[10, 1000], **kw)
    np.testing.assert_array_equal(ws, w2[subset])
    np.testing.assert_array_equal(cs, c2[subset])
    uniform = area_style(
        n,
        r,
        ids,
        classification=mapping,
        scale_width=True,
        color_area=False,
        distinguish=False,
        color="#123456",
        area_limits=[100, 200],
    )[0:2]
    np.testing.assert_array_equal(uniform[0], w)
    assert set(uniform[1]) == {"#123456"}
    typed = area_style(n, r, ids, scale_width=False, distinguish=True, color="#123456", flexible_color="#abcdef")[1]
    assert list(typed[:2]) == ["#123456", "#abcdef"]


def test_reference_population_ignores_seam_duplicates_and_invalid_endpoints():
    n, r, _ = reference()
    n.link_index = np.array([0, 1, 2, 2])
    area_style(n, r, np.arange(4), classification="quartiles", color_area=True)
    assert n._area_summary[0] == 3
    np.testing.assert_array_equal(n._area_summary[3], [0.5, 1, 1.5])


def test_conditional_controls_preferences_and_default_width(products):
    app = Explorer(products, products.parent / "out")
    assert app.width_mode.value == "upstream_area" and app.classification.value == "continuous"
    assert app.color.visible and app.flex_color.visible and not app.river_ui.area_colors.visible
    app.color_mode.value = "uniform"
    assert app.color.name == "All Links Color" and not app.flex_color.visible
    assert len(set(app.frame.main["color"])) == 1 and len(set(app.frame.main["width"])) > 1
    app.color.value = "#123456"
    assert set(app.frame.main["color"]) == {"#123456"}
    app.width_mode.value = "uniform"
    assert not app.classification.visible
    app.color_mode.value = "upstream_area"
    assert not app.color.visible and not app.flex_color.visible and app.river_ui.area_colors.visible
    assert app.classification.visible
    app.area_palette.value = "turbo"
    app.river_ui.auto.value = False
    app.river_ui.high.value = 10
    app.river_ui.low.value = 1
    selected = app.selection
    extent = app.extent
    app.color_mode.value = "connection_type"
    app.color_mode.value = "upstream_area"
    assert app.area_palette.value == "turbo" and app.network_options()["area_limits"] == [1, 10]
    assert app.selection is selected and app.extent == extent
    for method in ("quartiles", "fixed"):
        app.classification.value = method
        assert app.river_ui.auto.disabled and app.river_ui.low.disabled and app.river_ui.high.disabled
    app.classification.value = "six_log"
    assert not app.river_ui.low.disabled


@pytest.mark.parametrize("size", [0, 5, 10, 20])
def test_arrow_size_direction_and_png_pixel_conversion(products, monkeypatch, size):
    app = Explorer(products, products.parent / "out")
    app.arrow_size.value = size
    arrows = app.frame.arrows
    if size == 0:
        assert not len(arrows["x"])
        return
    assert np.all(arrows["size"] == size)
    m = app.frame.main
    np.testing.assert_allclose(arrows["x"], m["x0"] + 0.68 * (m["x1"] - m["x0"]))
    cosine = np.cos(np.deg2rad(sum(app.extent[2:]) / 2))
    angle = np.arctan2(m["y1"] - m["y0"], (m["x1"] - m["x0"]) * cosine) - np.pi / 2
    np.testing.assert_array_equal(arrows["angle"], angle)
    captured = []
    original = Axes.scatter

    def capture(self, *args, **kwargs):
        if isinstance(kwargs.get("marker"), tuple):
            captured.append(kwargs["s"])
        return original(self, *args, **kwargs)

    monkeypatch.setattr(Axes, "scatter", capture)
    assert app.export().is_file()
    np.testing.assert_allclose(captured, np.full(len(arrows["x"]), (size * 72 / 160) ** 2))
    app.arrows.value = False
    assert app.arrow_size.value == 0 and not len(app.frame.arrows["x"])
    app.arrows.value = True
    assert app.arrow_size.value == 7


def test_arrow_density_diagnostic_keeps_all_physical_links(products):
    app = Explorer(products, products.parent / "out")
    n = app.network
    n.x0 = np.repeat(n.x0, 300)
    n.y0 = np.repeat(n.y0, 300)
    n.x1 = np.repeat(n.x1, 300)
    n.y1 = np.repeat(n.y1, 300)
    n.link_index = np.repeat(n.link_index, 300)
    app.arrow_size.value = 20
    assert len(app.frame.main["x0"]) > 600 and not len(app.frame.arrows["x"])
    assert any("600" in message and "zoom" in message for message in app.frame.diagnostics)


@pytest.mark.parametrize(
    "field,value",
    [
        ("area_limits", [0, 10]),
        ("area_limits", [2, 1]),
        ("area_limits", [1, float("nan")]),
        ("area_color_style", "unknown"),
        ("area_palette", "unknown"),
        ("arrow_size", 21),
        ("arrow_size", -1),
    ],
)
def test_invalid_settings_rejected_before_mutation(products, field, value):
    app = Explorer(products, products.parent / "out")
    before = app.settings()
    data = app.settings()
    data["layers" if field == "arrow_size" else "network_options"][field] = value
    with pytest.raises(ValueError):
        app.load(json.dumps(data).encode())
    assert app.settings() == before


def test_roundtrip_legacy_arrow_and_palette_semantics(products):
    app = Explorer(products, products.parent / "out")
    app.color_mode.value = "upstream_area"
    app.area_palette.value = "cividis"
    app.arrow_size.value = 10
    app.river_ui.auto.value = False
    app.river_ui.high.value = 20
    app.river_ui.low.value = 1
    data = app.settings()
    app.load(json.dumps(data).encode())
    assert app.settings() == data
    data["network_options"].pop("area_limits")
    data["network_options"].pop("area_color_style")
    data["network_options"]["classification"] = "quartiles"
    data["network_options"]["area_palette"] = "viridis"
    data["layers"].pop("arrow_size")
    data["layers"]["arrows"] = True
    app.load(json.dumps(data).encode())
    assert app.arrow_size.value == 7 and app.river_ui.color_style == "gallery_quartiles"
    app.area_palette.value = "plasma"
    assert app.river_ui.color_style == "palette"
    data = app.settings()
    data["layers"].pop("arrow_size")
    data["layers"]["arrows"] = False
    app.load(json.dumps(data).encode())
    assert app.arrow_size.value == 0


ROOT = Path(__file__).resolve().parents[3]


@pytest.mark.skipif(not (ROOT / "map/mekong_15min/params.txt").exists(), reason="Mekong unavailable")
def test_mekong_gallery_exceptions_and_custom_palette(tmp_path):
    app = Explorer(ROOT / "map/mekong_15min", tmp_path)
    app.apply_preset("p01-f03a", use_gallery_extent=True)
    assert set(app.frame.main["color"]) <= set(AREA_COLORS)
    assert app.river_ui.color_style == "palette" and app.area_palette.value == "blue_navy" and app.arrow_size.value == 7
    app.area_palette.value = "plasma"
    assert not set(app.frame.main["color"]) <= set(AREA_COLORS)
    assert "Custom" in app.preset_status.object
    app.apply_preset("p01-f02c")
    assert app.river_ui.color_style == "gallery_continuous" and app.classification.value == "six_log"
    assert len(set(app.frame.main["color"])) > 6
    assert any("Color: continuous" in label for label in app.frame.legend)
    assert len(set(app.frame.main["width"])) <= 6 and app.arrow_size.value == 0
    app.area_palette.value = "turbo"
    assert app.river_ui.color_style == "palette" and len(set(app.frame.main["color"])) <= 6


def test_fixed_legacy_retains_historical_range_and_unknown_endpoint_style():
    n, r, ids = reference()
    widths, colors, labels, _ = area_style(
        n, r, ids, classification="fixed", color_area=True, scale_width=True, area_limits=[100, 1000]
    )
    np.testing.assert_allclose(widths[:7], [0.5, 1, 1.5, 2, 2.5, 3, 3.5])
    assert widths[-1] == 0.5 and colors[-1] == colors[0]
    assert any("1–1e+06" in label for label in labels)

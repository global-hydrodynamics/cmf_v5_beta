"""Explorer-specific coordinate, assignment, color and explicit-selection contracts.

Small analytical inputs expose affine Mercator distortion, unassigned extremes,
unit confusion, and saved-state regressions that widget-only tests would miss.
"""

import json
from pathlib import Path

import numpy as np
import pytest
from matplotlib import colormaps
from matplotlib.colors import to_hex
from bokeh.events import RangesUpdate

from app import Explorer
from basemap import tile_plan, world_pixel, DEFAULT_URL
from config import load_settings
from hires import assignment, discover_tiles
from map_layers import make_layer, validate_palette_range
from map_reader import MapReader
from background_style import highres_layer
from test_v2 import products
from test_selection_modes import split_assignment


@pytest.mark.parametrize("lat", [0, 15, 45, 75, -60])
@pytest.mark.parametrize("span", [1, 12])
def test_geographic_rows_exact_mercator_alignment(lat, span):
    extent = (100, 100 + span, lat - span / 2, lat + span / 2)
    p = tile_plan(extent, (800, 600))
    assert len(p["tiles"]) <= 32
    for row in (0, 137, 599):
        latitude = extent[3] - (row + 0.5) * (extent[3] - extent[2]) / 600
        # Independently invert the tile mosaic row coordinate. An affine
        # tile-in-latitude implementation cannot satisfy this at high latitudes.
        north_y = world_pixel(extent[0], extent[3], p["zoom"])[1]
        origin = np.floor(north_y / 256) * 256
        y = p["rows"][row] + origin
        recovered = np.rad2deg(np.arctan(np.sinh(np.pi * (1 - 2 * y / (256 * 2 ** p["zoom"])))))
        assert recovered == pytest.approx(latitude, abs=1e-10)
    assert all(t["url"].startswith("https://tile.openstreetmap.org/") for t in p["tiles"])


def test_basemap_plan_limits_and_provider():
    p = tile_plan((170, 190, -10, 10), (1000, 700))
    assert len(p["tiles"]) <= 32 and p["extent"] == [170, 190, -10, 10]
    assert all(0 <= int(t["url"].split("/")[-2]) < 2 ** p["zoom"] for t in p["tiles"])
    with pytest.raises(ValueError, match="HTTPS"):
        tile_plan((0, 10, 0, 10), (400, 400), "http://example.com/{z}/{x}/{y}.png")
    assert tile_plan((0, 10, 0, 10), (400, 400), "http://127.0.0.1:5011/{z}/{x}/{y}.png")["tiles"]


@pytest.mark.parametrize("scale", ["linear", "log"])
@pytest.mark.parametrize("palette", ["gray", "gray_r", "viridis"])
@pytest.mark.parametrize("interval", [[0, 1], [0, 0.5], [0.4, 1], [0.5, 1]])
def test_palette_crop_preserves_physical_values_and_ticks(map_dir, scale, palette, interval):
    reader = MapReader(map_dir)
    original = make_layer(reader, "uparea", scale, palette)
    cropped = make_layer(reader, "uparea", scale, palette, palette_range=interval)
    np.testing.assert_array_equal(cropped.image, original.image)
    assert (cropped.low, cropped.high, cropped.logarithmic) == (original.low, original.high, original.logarithmic)
    assert cropped.palette == [
        to_hex(colormaps[palette](interval[0] + i / 255 * (interval[1] - interval[0]))) for i in range(256)
    ]


@pytest.mark.parametrize("interval", [[0, 0], [1, 0], [-0.1, 1], [0, 1.1], [float("nan"), 1], [False, 1]])
def test_invalid_palette_rejected(interval):
    with pytest.raises(ValueError):
        validate_palette_range(interval)


def test_gallery_transfer_before_crop_and_defaults(products):
    reader = MapReader(products)
    tile = discover_tiles(products, [])["fine/tile"]
    coarse = make_layer(reader, "uparea")
    a = highres_layer(
        np.array([[1.0, 2.0]]),
        reader,
        tile,
        "elevtn",
        "uparea",
        coarse,
        dict(palette="gallery", scale="gallery", limits=[0, 10]),
    )
    b = highres_layer(
        np.array([[1.0, 2.0]]),
        reader,
        tile,
        "elevtn",
        "uparea",
        coarse,
        dict(palette="gallery", scale="gallery", limits=[0, 10], palette_range=[0, 0.5]),
    )
    t = np.linspace(0, 1, 256)
    assert a.palette == [to_hex(colormaps["gray"](0.16 + 0.42 * np.sqrt(v))) for v in t]
    assert b.palette == [to_hex(colormaps["gray"]((0.16 + 0.42 * np.sqrt(v)) * 0.5)) for v in t]
    assert (a.low, a.high) == (b.low, b.high) == (0, 10)


def test_assigned_only_full_tile_population(products):
    reader = MapReader(products)
    tile = discover_tiles(products, [])["fine/tile"]
    codes = tile.mmap("catmxy").copy()
    codes[:, 0, :6] = np.array([[-999, -9999, 99, 1, 2, 1], [-999, -9999, 1, -999, 99, 1]])
    codes.tofile(tile.files["catmxy"])
    values = np.arange(48, dtype="<f4").reshape(6, 8)
    values[0, :5] = [1e9, -1e9, 1e9, 1e9, 1e9]
    values[0, 5] = np.nan
    values[1, 0] = -9999
    values[1, 1] = 0
    values.tofile(tile.files["elevtn"])
    tile._maps.clear()
    valid, _, _ = assignment(*codes, reader.geometry)
    expected = values[valid & np.isfinite(values) & (values != -9999)]
    assert tile.percentiles("elevtn") == pytest.approx(np.percentile(expected, [2, 98]))
    assert tile.percentiles("elevtn", positive=True) == pytest.approx(np.percentile(expected[expected > 0], [2, 98]))
    before = dict(tile._stats)
    tile.subset((11, 12, 21, 22), max_side=2)
    assert tile.percentiles("elevtn") == pytest.approx(np.percentile(expected, [2, 98])) and tile._stats == before
    tile.files.pop("catmxy")
    with pytest.raises(ValueError, match="manual limits"):
        tile.percentiles("elevtn")


def test_explicit_selection_legacy_state_and_native_fields(split_assignment):
    root, codes = split_assignment
    d = root / "fine"
    np.full((6, 8), 12.5, dtype="<f4").tofile(d / "tile.uparea.bin")
    np.full((6, 8), 17.25, dtype="<f4").tofile(d / "tile.rivwth.bin")
    levels = np.full((6, 8), 42, dtype="i1")
    levels[0, 0] = -9
    levels.tofile(d / "tile.catmz100.bin")
    app = Explorer(root, root.parent / "exports")
    assert app.point_select.value == "catchment" and app.cell_inspector.pixel_section.active == []
    info = app.inspect(11.25, 22.25)
    assert app.selected == (1, 0) and app.selection.native_pixel == (1, 2)
    assert info["native hires uparea [km²]"] == 12.5 and info["native hires rivwth [m]"] == 17.25
    assert "Unavailable" in app.cell_inspector.pixel.object and "Native fldhgt" in app.cell_inspector.pixel.object
    for mode in ("coarse", "elevtn", "catchment", "none"):
        app.background.value = mode
        assert app.selected == (1, 0)
    app.point_select.value = "grid"
    assert app.selected == (0, 1)
    app.point_select.value = "catchment"
    assert app.selected == (1, 0)
    info = app.inspect(10.25, 22.75)
    assert app.selected is None and info["native hires catmz100 [stored code]"] == -9
    saved = app.settings()
    saved.pop("point_select")
    saved.pop("basemap")
    saved["layers"]["background"] = "coarse"
    saved.pop("background_ui")
    legacy = load_settings(json.dumps(saved).encode(), app.reader)
    assert legacy["point_select"] == "grid" and legacy["basemap"] == dict(show=False, opacity=1)
    saved["layers"]["background"] = "elevtn"
    assert load_settings(json.dumps(saved).encode(), app.reader)["point_select"] == "catchment"
    saved["version"] = 1
    assert load_settings(json.dumps(saved).encode(), app.reader)["point_select"] == "grid"


def test_ui_palette_rollback_roundtrip_basemap_and_reapply(products):
    app = Explorer(products, products.parent / "exports")
    ui = app.background_ui
    app.palette.value = "gray"
    original = app.frame.layer.palette
    ui.coarse_palette_max.value = 0.5
    assert app.frame.layer.palette != original and app.mapper.palette == app.frame.layer.palette
    ui.coarse_palette_min.value = 0.8
    assert ui.coarse_palette_min.value == 0 and "previous range retained" in ui.color_note.object
    app.inspect(11.25, 21.75)
    boundary = app.selection.boundary
    app.show_osm.value = True
    app.osm_opacity.value = 35
    assert app.basemap_renderer.glyph.global_alpha == 0.35 and app.frame.background_opacity == 1
    saved = app.settings()
    app.load(json.dumps(saved).encode())
    assert app.settings() == saved
    app.map_aspect.value = "landscape"
    app._navigation(RangesUpdate(app.plot, x0=10.5, x1=13, y0=20.2, y1=22.2))
    center = ((app.extent[0] + app.extent[1]) / 2, (app.extent[2] + app.extent[3]) / 2)
    app.apply_aspect_button.clicks += 1
    assert ((app.extent[0] + app.extent[1]) / 2, (app.extent[2] + app.extent[3]) / 2) == pytest.approx(center)
    extent = app.extent
    app.apply_aspect_button.clicks += 1
    assert app.extent == pytest.approx(extent) and app.selection.boundary is boundary
    assert app.export().is_file() and "Online basemap excluded" in app.status.object


def test_new_session_prefers_assignment_source(products):
    original = products / "fine/tile.catmxy.bin"
    original.rename(products / "fine/assigned.catmxy.bin")
    location=products/"fine/location.txt"
    location.write_text(location.read_text().replace("1 narea", "2 narea",1))
    with location.open("a") as stream:
        stream.write("2 assigned 10 14 20 23 8 6 0.5\n")
    app = Explorer(products, products.parent / "exports")
    assert app.hires_source.value == "fine/assigned" and app.point_select.value == "catchment"
    app.inspect(11.25, 21.75)
    assert app.selected == (1, 1)

"""Two-stage background UI contracts and unchanged scientific rendering."""

import json
from pathlib import Path

import numpy as np
import pytest

from app import Explorer
from hires import Tile
from map_layers import make_layer
from scene import Scene
from test_v2 import products


def add_coarse(products):
    np.arange(-4, 8, dtype="<f4").reshape(3, 4).tofile(products / "elevtn.bin")
    np.array([[1, 2, 3, 1], [2, 3, 1, 2], [3, 1, 2, 3]], dtype="<i4").tofile(products / "basin.bin")


def test_independent_variables_profiles_and_visibility(products):
    add_coarse(products)
    app = Explorer(products, products.parent / "exports")
    assert app.raster_type.value == "coarse"
    assert app.coarse_variable.visible and not app.highres_variable.visible
    app.palette.value = "magma"
    app.auto_limits.value = False
    app.low.value, app.high.value = 1, 100
    app.coarse_variable.value = "elevtn"
    app.palette.value = "terrain"
    assert app.layer.label.startswith("elevtn")
    app.coarse_variable.value = "uparea"
    assert (app.palette.value, app.auto_limits.value, app.low.value, app.high.value) == ("magma", False, 1, 100)
    app.raster_type.value = "highres"
    assert app.background.value == "catchment" and app.variable.value == "uparea"
    assert app.highres_variable.visible and not app.coarse_variable.visible
    assert app.frame.layer.logarithmic and not app.highres_scale.disabled and not app.highres_palette.disabled
    app.highres_variable.value = "flddif"
    app.highres_palette.value = 'pale_terrain'
    assert app.highres_palette.visible and app.background_ui.highres_colors.visible
    assert not app.background_ui.coarse_colors.visible
    app.raster_type.value = "coarse"
    assert app.coarse_variable.value == "uparea" and app.palette.value == "magma"
    app.coarse_variable.value = "elevtn"
    assert app.palette.value == "terrain"
    app.raster_type.value = "highres"
    assert app.highres_variable.value == "flddif" and app.highres_palette.value == "pale_terrain"
    app.no_background.value = True
    assert app.background.value == "none" and not app.frame.images
    app.no_background.value = False
    assert app.background.value == "flddif"
    app.raster_type.value = "coarse"
    app.coarse_variable.value = "basin"
    assert app.scale.disabled and app.auto_limits.disabled and not app.layer.logarithmic
    assert app.layer.categories.tolist() == [1, 2, 3]


@pytest.mark.parametrize("mode", ["coarse", "catchment", "elevtn", "flddif", "difference", "none"])
def test_ui_matches_existing_scene_and_native_selection(products, mode):
    app = Explorer(products, products.parent / "exports")
    extent = app.extent
    options = app.scene_options()
    options["background"] = mode
    coarse = make_layer(app.reader, "uparea")
    expected = Scene(app.reader).build(extent, "uparea", coarse, app.network, options)
    network = app.network_choice.value
    overlays = {key: widget.value for key, widget in app.overlay_controls.items()}
    if mode == "none":
        app.no_background.value = True
    elif mode != "coarse":
        app.raster_type.value = "highres"
        app.highres_variable.value = mode
    assert app.background.value == mode
    if mode in ('elevtn','flddif','difference'):
        assert ('tile.'+('elevtn' if mode=='difference' else mode)+'.bin') in app.status.object
    assert app.extent == extent and app.network_choice.value == network
    assert {key: widget.value for key, widget in app.overlay_controls.items()} == overlays
    assert len(app.frame.images) == len(expected.images)
    for (actual, edges), (reference, reference_edges) in zip(app.frame.images, expected.images):
        np.testing.assert_array_equal(actual, reference)
        assert edges == reference_edges
    if mode == "coarse":
        assert app.layer.image[0, 0] == 1.0  # source m² → display km²
    app.inspect(11.25, 21.75)
    assert app.selected == (1, 1) and app.selection.boundary is not None
    app.overlay_controls["catchment_boundaries"].value = True
    assert any("assignment boundaries" in entry[3] for entry in app.frame.overlays)


def test_tile_availability_fallback_and_source_selection(products):
    app = Explorer(products, products.parent / "exports")
    tile = app.scene.tiles["fine/tile"]
    app.scene.tiles["partial"] = Tile(
        "partial",
        tile.directory,
        tile.prefix,
        tile.geometry,
        {key: path for key, path in tile.files.items() if key != "flddif"},
    )
    app.scene.tiles["empty"] = Tile("empty", tile.directory, tile.prefix, tile.geometry, {})
    app.hires_source.options = list(app.scene.tiles)
    app.raster_type.value = "highres"
    app.highres_variable.value = "flddif"
    app.inspect(11.25, 21.75)
    app.hires_source.value = "partial"
    assert "flddif" not in app.highres_variable.options.values()
    assert app.highres_variable.value == "catchment"
    assert "flddif" in app.background_ui.notice.object and "using" in app.background_ui.notice.object
    assert app.selection.tile_key == 'partial' and app.selection.boundary is not None
    app.highres_variable.value = "difference"
    app.hires_source.value = "fine/tile"
    assert app.highres_variable.value == "difference"
    app.hires_source.value = "empty"
    assert not app.highres_variable.options
    assert app.background.value == "none" and app.no_background.value
    assert app.hires_source.visible  # source can be recovered independently
    app.hires_source.value = "fine/tile"
    assert "catchment" in app.highres_variable.options.values()
    app.no_background.value = False
    app.raster_type.value = "coarse"
    assert app.hires_source.visible  # native selection is still independent


def test_missing_uparea_and_terrain_requirements(products):
    (products / "uparea.bin").unlink()
    np.ones((3, 4), dtype="<f4").tofile(products / "elevtn.bin")
    (products / "fine/tile.elevtn.bin").unlink()
    app = Explorer(products, products.parent / "exports")
    assert not app.highres_variable.options  # catmxy without uparea, flddif without elevtn
    assert list(app.raster_type.options.values()) == ["coarse"]
    assert "No supported" in app.background_ui.notice.object
    app.inspect(11.25, 21.75)
    assert app.selection.boundary is not None  # catmxy selection needs no uparea


def test_legacy_and_new_json_round_trip(products):
    add_coarse(products)
    app = Explorer(products, products.parent / "exports")
    app.coarse_variable.value = "basin"
    app.raster_type.value = "highres"
    app.highres_variable.value = "flddif"
    app.terrain_palette.value = "pale_terrain"
    saved = app.settings()
    other = Explorer(products, products.parent / "exports-2")
    other.load(json.dumps(saved).encode())
    assert other.settings() == saved
    other.raster_type.value = "coarse"
    assert other.coarse_variable.value == "basin"
    other.raster_type.value = "highres"
    assert other.highres_variable.value == "flddif"
    # Legacy v3-created settings use JSON v2. Preserve non-uparea catchment
    # fields under a visible compatibility option instead of replacing the field.
    legacy = app.settings()
    legacy.pop("background_ui")
    legacy.update(variable="basin", scale="auto", limits=None, palette="viridis")
    legacy["layers"]["background"] = "catchment"
    other.load(json.dumps(legacy).encode())
    assert other.highres_variable.value == "catchment:basin"
    assert other.variable.value == "basin" and len(other.frame.layer.categories) == 3
    assert any("legacy inherited basin" in label for label in other.highres_variable.options)
    for mode in ("coarse", "catchment", "elevtn", "flddif", "difference", "none"):
        state = app.settings()
        state.pop("background_ui")
        state.update(variable="uparea", palette="viridis", scale="auto", limits=None)
        state["layers"]["background"] = mode
        other.load(json.dumps(state).encode())
        assert other.background.value == mode
    state = app.settings()
    state.update(version=1)
    state.pop("layers")
    other.load(json.dumps(state).encode())
    assert other.raster_type.value == "coarse" and other.background.value == "coarse"


ROOT = Path(__file__).resolve().parents[3]


@pytest.mark.skipif(not (ROOT / "map/mekong_15min/params.txt").exists(), reason="Mekong unavailable")
def test_mekong_hierarchy_all_modes_and_f05e(tmp_path):
    app = Explorer(ROOT / "map/mekong_15min", tmp_path)
    app.set_extent((104.5, 107, 9.5, 12))
    for variable in app.coarse_variable.options.values():
        app.coarse_variable.value = variable
        assert app.layer is not None and "Error" not in app.status.object
    app.raster_type.value = "highres"
    assert set(app.highres_variable.options.values()) == {"catchment", "elevtn", "flddif", "difference"}
    for variable in app.highres_variable.options.values():
        app.highres_variable.value = variable
        app.inspect(105.8, 10.8)
        assert app.selected == (96, 62) and app.selection.boundary.pixel_count == 295
    expected = app.apply_preset("p01-f05e")
    assert app.settings() == expected
    assert app.highres_variable.value == "difference" and app.terrain_palette.value == "pale_terrain"
    assert app.export().is_file()


def test_json_ui_validation_and_missing_saved_variable(products):
    app = Explorer(products, products.parent / "exports")
    state = app.settings()
    state["background_ui"]["raster_type"] = "highres"
    before = app.settings()
    with pytest.raises(ValueError, match="disagrees"):
        app.load(json.dumps(state).encode())
    assert app.settings() == before
    app.scene.tiles["fine/tile"].files.pop("flddif")
    legacy = app.settings()
    legacy.pop("background_ui")
    legacy["layers"]["background"] = "flddif"
    app.load(json.dumps(legacy).encode())
    assert app.background.value == "catchment"
    assert "Saved high-resolution variable flddif unavailable" in app.background_ui.notice.object
    assert app.highres_variable.value == "catchment"


def test_legacy_linear_catchment_is_explicit_and_preserved(products):
    app = Explorer(products, products.parent / "exports")
    state = app.settings()
    state.pop("background_ui")
    state['layers'].pop('highres_style',None)  # legacy files predate independent fine styling
    state["layers"]["background"] = "catchment"
    state["scale"] = "linear"
    app.load(json.dumps(state).encode())
    assert app.background.value == "catchment" and not app.frame.layer.logarithmic
    assert "Custom linear normalization" in app.background_ui.color_note.object

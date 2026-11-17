"""Startup-only defaults reuse the Gallery method without changing its definition."""

import json
from pathlib import Path
from unittest.mock import Mock

import app as app_module
from app import Explorer, create_app
from test_v2 import products


def test_startup_preset_and_overland_then_saved_user_settings(products):
    (products / "nextxy_noedge.bin").write_bytes((products / "nextxy.bin").read_bytes())
    app = Explorer(products, products.parent / "startup-exports")
    extent = app.extent
    canonical = dict(app.preset_library.presets["p01-f04b"][0])
    app.apply_startup_defaults()
    assert app.preset_choice.value == "p01-f04b"
    assert app._applied_preset == "p01-f04b"
    assert app.background.value == "catchment"
    assert app.overlay_controls["channel_pixels"].value
    assert app.overlay_controls["overland"].value
    assert app.extent == extent  # Mekong Gallery extent is outside this synthetic map
    assert "Custom (modified from p01-f04b)" in app.preset_status.object
    assert app.preset_library.presets["p01-f04b"][0] == canonical
    assert not canonical["overland"]
    assert any("Overland bifurcations" in o.label for o in app.frame.overlays)
    state = app.settings()
    state["layers"]["overlays"]["overland"] = False
    app.load(json.dumps(state).encode())
    assert not app.overlay_controls["overland"].value
    app.apply_preset("p01-f04b")
    assert not app.overlay_controls["overland"].value  # explicit Gallery unchanged


def test_startup_missing_products_keeps_map_usable(map_dir):
    app = Explorer(map_dir, map_dir.parent / "startup-exports")
    plot = app.plot
    before = app.settings()
    app.apply_startup_defaults()
    assert app.plot is plot and app.settings() == before
    assert "Startup p01-f04b unavailable" in app.preset_status.object
    assert app.frame is not None


def test_all_launchers_use_startup_factory(monkeypatch):
    instance = Mock()
    constructor = Mock(return_value=instance)
    monkeypatch.setattr(app_module, "Explorer", constructor)
    assert create_app("map") is instance.view
    instance.apply_startup_defaults.assert_called_once_with()


def test_real_mekong_startup_extent_and_reference(tmp_path):
    root = Path(__file__).resolve().parents[3] / "map/mekong_15min"
    app = Explorer(root, tmp_path)
    app.apply_startup_defaults()
    assert tuple(app.extent) == (104.5, 107, 9.5, 12)
    assert app.frame.layer.low == 445.22297599999996
    assert app.frame.layer.high == 174590.73843199998
    assert app.overlay_controls["overland"].value
    assert any("Overland bifurcations" in o.label and len(o.segments) > 0 for o in app.frame.overlays)


def test_startup_without_gallery_metadata_keeps_map(map_dir):
    app = Explorer(map_dir, map_dir.parent / "startup-exports")
    app.preset_library.presets = {}
    app.apply_startup_defaults()
    assert "Gallery metadata is missing" in app.preset_status.object
    assert app.frame is not None

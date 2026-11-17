"""Headwater-only display decluttering never rewrites scientific connectivity."""
import json
from types import SimpleNamespace

import numpy as np
import pytest

from app import Explorer
from river_network import automatic_detail
from test_v2 import products


def test_only_native_headwaters_hide_with_strict_trigger_and_periodic_pieces():
    # Native graph: 0,1 ->3 ->5 ->6 and 2 ->4 ->5. Only 0,1,2 are headwaters.
    network = SimpleNamespace(
        geometry=SimpleNamespace(nx=8, ny=1),
        rows=np.zeros(6, dtype=int), cols=np.arange(6),
        dest_rows=np.zeros(6, dtype=int), dest_cols=np.array([3, 3, 4, 5, 5, 6]),
        link_index=np.array([0, 1, 2, 3, 4, 5, 0]),
    )
    original = network.dest_cols.copy()
    ids = np.arange(7)
    kept, text = automatic_detail(network, ids, threshold=2)
    np.testing.assert_array_equal(kept, [3, 4, 5])
    np.testing.assert_array_equal(network._headwater_links, [True, True, True, False, False, False])
    np.testing.assert_array_equal(network.dest_cols, original)
    assert "3 headwater cells > threshold 2" in text and "Display only" in text
    # Exact threshold does not trigger; seam fragments do not double-count heads.
    unchanged, _ = automatic_detail(network, ids, threshold=3)
    np.testing.assert_array_equal(unchanged, ids)
    zoom, _ = automatic_detail(network, np.array([0, 1]), threshold=2)
    np.testing.assert_array_equal(zoom, [0, 1])
    # Incoming links outside view still count: clipped upstream nodes are not new heads.
    interior, _ = automatic_detail(network, np.array([3, 4, 5]), threshold=0)
    np.testing.assert_array_equal(interior, [3, 4, 5])


def test_detail_settings_roundtrip_legacy_and_selection(products):
    app = Explorer(products, products.parent / "detail-out")
    assert app.river_ui.detail.value == "auto" and app.river_ui.budget.value == 5000
    app.apply_preset("p01-f04b")
    assert app.river_ui.detail.value == "auto" and app.river_ui.budget.value == 5000
    app.inspect(11.25, 21.75)
    selection, plot, extent = app.selection, app.plot, app.extent
    app.river_ui.detail.value = "all"
    assert app.river_ui.budget.disabled
    assert app.selection is selection and app.plot is plot and app.extent == extent
    saved = app.settings()
    app.load(json.dumps(saved).encode())
    assert app.river_ui.detail.value == "all"
    saved["layers"].pop("network_detail")
    saved["layers"].pop("network_budget")
    app.river_ui.detail.value = "auto"
    app.load(json.dumps(saved).encode())
    assert app.river_ui.detail.value == "all"  # Earlier saved views preserve full networks.
    assert "All links" in app.river_ui.detail_note.object


@pytest.mark.parametrize("key,value", [("network_detail", "bad"), ("network_budget", True),
                                         ("network_budget", 999), ("network_budget", 20001),
                                         ("network_budget", 5000.5)])
def test_invalid_detail_settings_rejected_before_mutation(products, key, value):
    app = Explorer(products, products.parent / "detail-invalid")
    before = app.settings()
    data = app.settings()
    data["layers"][key] = value
    with pytest.raises(ValueError):
        app.load(json.dumps(data).encode())
    assert app.settings() == before


def test_scene_detail_keeps_style_reference_and_export_geometry(products, monkeypatch):
    app = Explorer(products, products.parent / "detail-scene")
    options = app.scene_options()
    options.update(network_detail="auto", network_budget=0)
    auto = app.scene.build(app.extent, app.variable.value, app.layer, app.network, options)
    assert len(auto.main["x0"]) < len(app.network.visible(app.extent))
    exported = app.scene.build(app.extent, app.variable.value, app.layer, app.network, options, max_side=2400)
    for key in auto.main:
        np.testing.assert_array_equal(auto.main[key], exported.main[key])
    assert "Auto detail" in auto.network_detail_note
    assert any("Display only" in label and "omitted headwater" in label for label in auto.legend)
    options["network_detail"] = "all"
    full = app.scene.build(app.extent, app.variable.value, app.layer, app.network, options)
    assert len(full.main["x0"]) == len(app.network.visible(app.extent))
    assert not any("Auto detail" in text for text in full.diagnostics)
    reference = {
        tuple(full.main[key][i] for key in ("x0", "y0", "x1", "y1")):
        (full.main["color"][i], full.main["width"][i]) for i in range(len(full.main["x0"]))
    }
    for i in range(len(auto.main["x0"])):
        key = tuple(auto.main[name][i] for name in ("x0", "y0", "x1", "y1"))
        assert (auto.main["color"][i], auto.main["width"][i]) == reference[key]

"""Complete nextxy display and exact Gallery Blue→Navy color anchors."""

import ast
import json
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest
from matplotlib.colors import to_rgba
from netCDF4 import Dataset

from app import Explorer
from config import load_settings
from conftest import write_network
from map_products import AREA_COLORS, RIVER_GRADIENTS, area_style

ROOT = Path(__file__).resolve().parents[3]


def test_blue_navy_is_exact_gallery_quartet_in_all_mappings():
    expected = ("#5E88BE", "#4F80BF", "#285A9B", "#103A70")
    assert RIVER_GRADIENTS["blue_navy"] == AREA_COLORS == expected
    scripts = ROOT / "visualization/river_map/script"
    for filename, field in [
        ("f04_rivmap_catchment.py", "MAIN_COLORS"),
        ("f03a-vector_river_map-upstream_area.py", "AREA_COLORS"),
    ]:
        module = ast.parse((scripts / filename).read_text())
        value = next(
            ast.literal_eval(n.value)
            for n in module.body
            if isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == field for t in n.targets)
        )
        assert value == expected
    for mapping in ["quartiles", "continuous"]:
        network = SimpleNamespace(
            _areas=np.array([1.0, 10.0, 100.0, 1000.0]), link_index=np.arange(4), flexible=np.zeros(4, bool)
        )
        _, colors, _, _ = area_style(
            network, SimpleNamespace(), np.arange(4), classification=mapping, area_palette="blue_navy", color_area=True
        )
        np.testing.assert_allclose([to_rgba(c) for c in colors], [to_rgba(c) for c in expected])

    # A saved Gallery continuous transfer must remain continuous even when its
    # base palette is Blue→Navy; its five legend samples must remain valid.
    network = SimpleNamespace(
        _areas=np.array([1.0, 2.0, 100.0, 1000.0]), link_index=np.arange(4), flexible=np.zeros(4, bool)
    )
    _, colors, _, swatches = area_style(
        network, SimpleNamespace(), np.arange(4), classification="quartiles",
        area_palette="blue_navy", area_color_style="gallery_continuous", color_area=True
    )
    assert len(swatches) == 5
    assert to_rgba(colors[1]) not in [to_rgba(c) for c in expected]


def test_legacy_network_json_migrates_with_explicit_notice(map_dir):
    write_network(map_dir)
    (map_dir / "nextxy_noedge.bin").write_bytes((map_dir / "nextxy.bin").read_bytes())
    app = Explorer(map_dir, map_dir.parent / "network-exports")
    assert app.network_choice.options == ["off", "nextxy"]
    old = app.settings()
    old["network"] = "nextxy_noedge"
    result = load_settings(json.dumps(old).encode(), app.reader)
    assert result["network"] == "nextxy"
    assert any("nextxy_noedge" in note and "nextxy" in note for note in result["_warnings"])
    app.load(json.dumps(old).encode())
    assert app.network_choice.value == "nextxy" and "Legacy nextxy_noedge" in app.status.object


def test_missing_complete_nextxy_does_not_substitute_noedge(map_dir):
    write_network(map_dir)
    (map_dir / "nextxy.bin").rename(map_dir / "nextxy_noedge.bin")
    app = Explorer(map_dir, map_dir.parent / "network-exports")
    assert app.network_choice.options == ["off"]
    old = app.settings()
    old["network"] = "nextxy_noedge"
    result = load_settings(json.dumps(old).encode(), app.reader)
    assert result["network"] == "off" and result["_warnings"]
    data = app.inspect(10.5, 22.5)
    assert "network product" not in data


def test_mekong_complete_network_and_canonical_presets(tmp_path):
    path = ROOT / "map/mekong_15min"
    with Dataset(path / "netcdf/nextxy.nc") as d:
        x = np.ma.asarray(d["nextx"][:]).filled(-9999)
        y = np.ma.asarray(d["nexty"][:]).filled(-9999)
    expected = (x >= 1) & (x <= 80) & (y >= 1) & (y <= 120)
    assert int(expected.sum()) == 6152
    app = Explorer(path, tmp_path)
    assert app.network_choice.options == ["off", "nextxy"]
    for row, _ in app.preset_library.presets.values():
        assert row["network_source"] in ("off", "nextxy")
    for identity in ["p01-f03a", "p01-f04b"]:
        app.apply_preset(identity, True)
        assert app.network.product == "nextxy" and len(app.network.rows) == 6152
        assert app.river_ui.palette.value == "blue_navy" and app.river_ui.color_style == "palette"
        assert set(app.frame.main["color"]) <= set(AREA_COLORS)
        assert "Gallery preset" in app.preset_status.object and "Custom" not in app.preset_status.object

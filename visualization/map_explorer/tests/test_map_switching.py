"""Map-switch transactions, independent sessions and current-map scientific I/O."""

import json
from pathlib import Path
from unittest.mock import Mock

import numpy as np
import pytest
from bokeh.document import Document

from app import create_app
from map_datasets import DEFAULT_MAP, REPOSITORY, discover_maps, resolve_map
from map_session import ExplorerSession
from test_hires_netcdf import write_product
from test_v2 import products
from map_reader import Geometry


def make_map(path, nx=4, ny=3, west=10, north=23, step=1, offset=0, hires=False):
    path.mkdir(parents=True)
    east, south = west + nx * step, north - ny * step
    (path / "params.txt").write_text(f"{nx}\n{ny}\n2\n{step}\n{west}\n{east}\n{south}\n{north}\n")
    values = (np.arange(1, nx * ny + 1).reshape(ny, nx) + offset).astype("<f4") * 1e6
    values.tofile(path / "uparea.bin")
    x, y = np.tile(np.arange(1, nx + 1), (ny, 1)), np.tile(np.arange(1, ny + 1)[:, None], (1, nx))
    dx = np.minimum(x + 1, nx).astype("<i4")
    dy = y.astype("<i4")
    dx[:, -1] = dy[:, -1] = -9
    np.stack([dx, dy]).tofile(path / "nextxy.bin")
    lon = (west + (x - .5) * step + .01).astype("<f4")
    lat = (north - (y - .5) * step - .01).astype("<f4")
    np.stack([lon, lat]).tofile(path / "lonlat.bin")
    if hires:
        directory = path / "fine_nc"
        directory.mkdir()
        (directory / "location.txt").write_text(
            f"1 narea\narea name west east south north nx ny step\n1 tile {west} {east} {south} {north} {nx*2} {ny*2} {step/2}\n"
        )
        geometry = Geometry(nx * 2, ny * 2, 1, step / 2, west, east, south, north)
        assignments = np.full((2, ny * 2, nx * 2), 2, dtype="<i2")
        write_product(directory, "catmxy", assignments, geometry, "1")
        write_product(directory, "elevtn", np.arange(nx * ny * 4, dtype="<f4").reshape(ny*2, nx*2), geometry, "m")
    return path


@pytest.fixture
def maps(tmp_path):
    repo = tmp_path / "repository 日本"
    a = make_map(repo / "map/mekong_15min")
    b = make_map(repo / "map/別の map", 2, 2, 130, 35, .25, 100, hires=True)
    return repo, a, b


def session(maps, **kwargs):
    repo, a, b = maps
    return ExplorerSession(repository=repo, output_dir=repo.parent / "exports", **kwargs)


def test_default_and_repo_relative_paths_are_cwd_independent(maps, monkeypatch, tmp_path):
    repo, a, b = maps
    monkeypatch.chdir(tmp_path)
    assert resolve_map() == DEFAULT_MAP.resolve()
    assert resolve_map("map/別の map", repo) == b.resolve()
    s = session(maps)
    assert s.active.reader.path == a
    assert s.directory.value == str(a)
    assert s.load_map("map/別の map")
    assert s.active.reader.path == b
    assert s.active.reader.geometry.extent == (130, 130.5, 34.5, 35)
    assert s.active._applied_preset is None
    assert "NetCDF" in s.status.object
    assert not s.active.scene.tiles["fine/tile"]._maps


def test_discovery_is_shallow_and_excludes_invalid_core_products(maps):
    repo, a, b = maps
    make_map(repo / "map/tools")
    make_map(repo / "map/tmp_work")
    make_map(repo / "map/outer/nested")
    bad = repo / "map/bad"
    bad.mkdir()
    (bad / "params.txt").write_text("bad")
    empty = repo / "map/empty"
    empty.mkdir()
    (empty / "params.txt").write_text((a / "params.txt").read_text())
    assert {m.path for m in discover_maps(repo)} == {a, b}


def test_dropdown_and_path_edit_require_explicit_load(maps):
    s = session(maps)
    old = s.active
    s.available.value = str(maps[2])
    assert s.directory.value == str(maps[2]) and s.active is old
    s.directory.value = str(maps[1])
    assert s.active is old
    assert not s.load_map()
    assert "already loaded" in s.status.object


def test_absolute_external_unicode_path_and_failed_load_preserves_active(maps, tmp_path):
    s = session(maps)
    old = s.active
    old.inspect(10.5, 22.5)
    selection = old.selection
    for path in [tmp_path / "missing", tmp_path, maps[0] / "map/broken"]:
        if path.name == "broken":
            path.mkdir()
            (path / "params.txt").write_text("not geometry")
        assert not s.load_map(path)
        assert s.active is old and old.selection is selection and not old._closed
    empty = tmp_path / "no core products"
    empty.mkdir()
    (empty / "params.txt").write_text((maps[1] / "params.txt").read_text())
    assert not s.load_map(empty)
    assert s.active is old
    external = make_map(tmp_path / "external maps/別の 地図", 3, 2, -5, 8, .5, 200)
    assert s.load_map(external)
    assert s.active.reader.path == external
    assert s.available.value is None


def test_repeated_switch_resets_scientific_state_and_retains_app_controls(maps):
    s = session(maps)
    old = s.active
    old.inspect(10.5, 22.5)
    old.show_osm.value = True
    old.panel_mode.value = "Inspector"
    old.background.value = "none"
    assert s.load_map(maps[2])
    new = s.active
    assert new.reader.geometry.nx == 2 and new.reader is not old.reader
    assert new.selected is None and new.selection.clicked is None and not hasattr(new, "_last_click")
    assert new.pins.pins == [] and new._selection_indexes == {}
    assert new.network is not old.network and old.network is None
    assert old._closed and not old.reader._cache and not old._networks
    assert not new.show_osm.value and new.background.value == "coarse"
    assert new.panel_mode.value == "Inspector"
    assert s.controls in new.view.objects and s.controls not in old.view.objects
    new.point_select.value = "grid"
    info = new.inspect(130.125, 34.875)
    assert new.selected == (0, 0)
    assert info["ix (1-based)"] == 1 and info["iy (1-based)"] == 1
    assert float(new.reader.read_cell("uparea", 0, 0)) == 101e6
    assert "101" in new.selection_summary.object
    assert f"{np.float32(130.135):.5f}" in new.selection_summary.object
    new.point_select.value = "catchment"
    new.inspect(130.0625, 34.9375)
    assert new.selection.geographic_cell == (0, 0) and new.selected == (0, 0)
    assert new.point_select.value == "grid" and new.selection.boundary is None
    assert s.load_map(maps[1])
    assert s.active.reader.path == maps[1] and s.active.selected is None
    assert s.active.reader.geometry.nx == 4 and float(s.active.reader.read_cell("uparea", 0, 0)) == 1e6


def test_pins_require_confirmation_and_failure_never_discards(maps):
    s = session(maps)
    old = s.active
    old.inspect(10.5, 22.5)
    old.pins.add()
    assert not s.load_map(maps[2])
    assert s.confirmation.visible and s.active is old and len(old.pins.pins) == 1
    s.cancel_switch()
    assert not s.confirmation.visible and len(old.pins.pins) == 1
    assert not s.load_map(maps[0] / "missing", confirm_pins=True)
    assert len(old.pins.pins) == 1
    assert s.load_map(maps[2], confirm_pins=True)
    assert not old.pins.pins and not s.active.pins.pins
    assert not s.confirmation.visible


def test_export_and_json_always_refer_to_current_map(maps):
    s = session(maps)
    settings = s.active.settings()
    assert s.load_map(maps[2])
    current = s.active
    before = current.settings()
    with pytest.raises(ValueError, match="another map"):
        current.load(json.dumps(settings).encode())
    assert current.settings() == before
    current.load(json.dumps(before).encode())
    png = current.export()
    assert maps[2].name in png.name and png.parent == Path(s.output_dir)
    assert not png.is_relative_to(current.reader.path)
    from PIL import Image
    with Image.open(png) as image:
        assert image.width > 500 and image.height > 500
    assert json.loads(current.save().read_text())["map_path"] == str(current.reader.path)


def test_independent_sessions_and_loading_guard(maps):
    a, b = session(maps), session(maps)
    a._loading = True
    assert not a.load_map(maps[2]) and a.active.reader.path == maps[1]
    a._loading = False
    assert a.load_map(maps[2])
    assert b.active.reader.path == maps[1] and not b.active._closed
    assert a.active.plot is not b.active.plot


def test_bokeh_view_replacement_detaches_old_plot_and_cancels_callbacks(maps):
    s = session(maps)
    document = Document()
    root = s.view.get_root(document)
    document.add_root(root)
    old = s.active
    assert old.plot.document is document
    callback = document.add_next_tick_callback(lambda: None)
    old._pending_callbacks.append((document, callback))
    assert s.load_map(maps[2])
    assert s.active.plot.document is document and old.plot.document is None
    assert callback not in document.session_callbacks
    called = Mock()
    old._guard(called)
    old._schedule(called)
    called.assert_not_called()
    assert len(document.roots) == 1
    s.close()


def test_no_dialog_desktop_defaults_and_explicit_map(maps, monkeypatch):
    import app
    import launch_desktop as launcher
    monkeypatch.setattr(launcher.importlib.util, "find_spec", lambda name: True)
    monkeypatch.setattr(launcher, "choose_map", Mock(side_effect=AssertionError("no automatic dialog")))
    seen = []
    monkeypatch.setattr(app, "main", lambda: seen.append(list(launcher.sys.argv)))
    assert launcher.main(["--no-browser"]) == 0
    assert seen[-1][1] == str(DEFAULT_MAP.resolve())
    assert launcher.main([str(maps[2]), "--no-browser"]) == 0
    assert seen[-1][1] == str(maps[2])


def test_factory_registers_bokeh_compatible_session_cleanup(maps, monkeypatch):
    import panel as pn
    import map_session
    document = Document()
    instance = Mock()
    monkeypatch.setattr(map_session, "ExplorerSession", Mock(return_value=instance))
    monkeypatch.setattr(pn.state, "on_session_destroyed", document.on_session_destroyed)
    assert create_app(maps[1]) is instance.view
    assert len(document.session_destroyed_callbacks) == 1
    next(iter(document.session_destroyed_callbacks))(None)
    instance.close.assert_called_once()


def test_failed_view_mount_rolls_back_active_controls_and_keeps_pins(maps):
    s = session(maps)
    document = Document()
    document.add_root(s.view.get_root(document))
    old = s.active
    old.inspect(10.5, 22.5)
    old.pins.add()
    def fail_once(event):
        s.host.param.unwatch(watcher)
        raise RuntimeError("simulated view mount failure")
    watcher = s.host.param.watch(fail_once, "objects")
    assert not s.load_map(maps[2], confirm_pins=True)
    assert s.active is old and not old._closed
    assert s.host.objects == [old.view]
    assert s.controls in old.view.objects
    assert len(old.pins.pins) == 1
    assert "simulated view mount failure" in s.status.object
    assert old.plot.document is document and len(document.roots) == 1


def test_map_dataset_drawer_is_opt_in_and_independent_of_settings(maps):
    s = session(maps)
    old = s.active
    plot = old.plot
    old.inspect(10.5, 22.5)
    selected = old.selected
    extent = old.extent
    assert not s.dataset_toggle.value and not s.controls.visible
    assert old.header_bar.objects[-2:] == [s.dataset_toggle, old.settings_toggle]
    assert s.controls not in old.visualization_panel.objects
    old.settings_toggle.value = False
    old.panel_mode.value = "Inspector"
    s.dataset_toggle.value = True
    assert s.controls.visible and not old.settings_panel.visible
    assert old.plot is plot and old.selected == selected and old.extent == extent
    s.dataset_toggle.value = False
    assert not s.controls.visible
    s.dataset_toggle.value = True
    assert s.load_map(maps[2])
    assert s.controls.visible and s.dataset_toggle.value
    assert s.dataset_toggle in s.active.header_bar.objects
    assert s.dataset_toggle not in old.header_bar.objects
    assert s.active.panel_mode.value == "Inspector"
    assert not s.active.settings_panel.visible
    s.dataset_toggle.value = False
    assert not s.controls.visible


def test_switch_applies_p04b_to_other_supported_maps_without_gallery_extent(products, tmp_path):
    import shutil
    from map_reader import MapReader
    alternate = tmp_path.parent / f"{tmp_path.name}-other map"
    shutil.copytree(products, alternate)
    s = ExplorerSession(products, output_dir=tmp_path.parent / f"{tmp_path.name}-exports")
    assert s.active._applied_preset == "p01-f04b"
    s.active.background.value = "none"
    assert s.load_map(alternate)
    app = s.active
    assert app._applied_preset == app.preset_choice.value == "p01-f04b"
    assert app.extent == MapReader(alternate).geometry.extent
    assert app.background.value == "catchment"
    assert all(app.overlay_controls[name].value for name in ("channel_pixels", "channel", "overland"))
    assert "Gallery preset p01-f04b applied" in app.preset_status.object
    s.close()

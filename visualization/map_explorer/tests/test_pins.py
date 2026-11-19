"""Pins use exact stored identity, shared scientific snapshots and independent UI state."""

import csv
import io
from types import SimpleNamespace
from unittest.mock import Mock

import numpy as np
import pytest

from app import Explorer
from pins import csv_bytes, letter, scalar
from test_v2 import products
from conftest import install_test_cogs


@pytest.fixture
def app(products, tmp_path_factory):
    install_test_cogs(products)
    result = Explorer(products, output_dir=tmp_path_factory.mktemp("pin-exports"))
    result.background.value = "catchment"
    return result


def add(app, x=10.75, y=22.25, name=""):
    app.inspect(x, y)
    app.pins.name.value = name
    return app.pins.add()


def test_pin_crud_unicode_duplicates_identity_and_positions(app):
    p = add(app, name='  観測点, "一"\n二行  ')
    assert p.name == '観測点, "一"\n二行'
    assert p.clicked == (10.75, 22.25)
    assert p.cell == app.selected
    assert app.pins.source.data["x"] == [10.75]
    app.inspect(10.8, 22.3)  # same target/mode; click floats are not duplicate keys
    assert app.pins.add().id == p.id
    assert len(app.pins.pins) == 1
    app.pins.name.value = "Renamed"
    app.pins.rename()
    assert app.pins.pins[0].id == p.id
    assert app.pins.source.data["name"] == ["Renamed"]
    assert "Renamed" in app.pins.core.object
    selected = app.selected
    app.pins.delete()
    assert app.pins.active is None
    assert not app.pins.pins and not app.pins.source.data["x"]
    assert app.selected == selected
    assert add(app).id != p.id


def test_grid_and_catchment_same_coordinate_are_distinct(app):
    first = add(app)
    app.background.value = "coarse"
    second = app.pins.add()
    assert first.id != second.id
    assert first.clicked == second.clicked
    assert [p.mode for p in app.pins.pins] == ["catchment", "grid"]


def test_unassigned_and_invalid_cannot_be_pinned(app):
    for x in (10.25, 10.75):
        app.inspect(x, 22.75)
        with pytest.raises(ValueError, match="valid Grid"):
            app.pins.add()
    assert not app.pins.pins


def test_revisit_cross_grid_restores_assignment_not_containment(app):
    path = app.reader.path / "fine/tile.catmxy.bin"
    raw = np.fromfile(path,dtype="<i2").reshape(2,6,8)
    raw[:,1,1]=[4,3]
    raw.tofile(path)
    install_test_cogs(app.reader.path)
    app.scene.tiles = __import__("hires").discover_tiles(app.reader.path,[])
    app.render_view()
    p = add(app)
    assert p.cell == (2, 3)
    assert app.reader.geometry.cell(*p.clicked) == (0, 0)
    app.background.value = "coarse"
    app.inspect(11.5, 21.5)
    app.pins.select(p.id)
    assert app.point_select.value == "grid" and "adjust zoom" in app.pins.message.object
    app.background.value = "catchment"
    app.pins.select(p.id)
    assert app.selected == (2, 3)
    assert app.point_select.value == "catchment"
    assert app.selection.clicked == p.clicked
    assert app.selection.boundary.pixel_count >= 1


def test_source_changes_refuse_revisit_without_mutating_selection(app):
    p = add(app)
    app.inspect(11.75, 21.25)
    before = app.selection
    path = app.reader.path / "params.txt"
    path.write_text(path.read_text() + "\n")
    with pytest.raises(ValueError, match="source changed"):
        app.pins.select(p.id)
    assert app.selection is before


def test_missing_source_refuses_revisit(app):
    p = add(app)
    tile = app.scene.tiles[p.tile]
    tile.files["catmxy"].unlink()
    with pytest.raises(ValueError, match="source unavailable"):
        app.pins.select(p.id)


def test_comparison_shared_data_units_layers_and_caching(app, monkeypatch):
    p = add(app)
    rec = p.record()
    assert rec["uparea_km2"] == app.reader.read_cell("uparea", *p.cell) * 1e-6
    assert rec["outlet_lon"] == pytest.approx(10.6)
    assert rec["outlet_lat"] == pytest.approx(22.4)
    for _, column, key, factor in __import__("pins").FIELDS:
        if key in p.values:
            assert rec[column] == scalar(p.values[key], factor)
    app.pins.comparison.active = [0]
    app.pins.profile_group.active = [0]
    monkeypatch.setattr(app.scene, "build", Mock(side_effect=AssertionError("Scene rebuilt")))
    monkeypatch.setattr(app.reader, "read_cell", Mock(side_effect=AssertionError("Source reread")))
    app.pins.name.value = "測点"
    app.pins.rename()
    app.pins.include.value = []
    assert len(app.pins.matrix()[0]) == 1
    assert app.pins.comparison.active == [0]
    assert app.pins.profile_group.active == [0]
    app.pins.include.value = [p.id]
    assert p.values == app.pins.pins[0].values
    assert len(app.pins.matrix("profiles")) == len(p.values.get("fldhgt [m]") or []) + 1


def test_csv_bom_quoting_inclusion_missing_and_unique_headers(app):
    first = add(app, name='日本語,"quoted"\nline')
    second = add(app, 11.75, 21.25, name=first.name)
    path = app.pins.export()
    raw = path.read_bytes()
    assert raw.startswith(b"\xef\xbb\xbf")
    records = list(csv.DictReader(io.StringIO(raw.decode("utf-8-sig"))))
    assert records[0]["pin_name"] == first.name
    assert records[0]["ctmare_km2"] == ""  # missing is never zero
    assert records[0]["river_ix"] == str(first.cell[1] + 1)
    app.pins.include.value = [second.id]
    matrix = list(csv.reader(io.StringIO(app.pins.export(True).read_text(encoding="utf-8-sig"))))
    assert len(matrix[0]) == 2 and second.id in matrix[0][1] and first.id not in matrix[0][1]
    assert all(len(row) == 2 for row in matrix)
    assert len(list(csv.reader(io.StringIO(app.pins.export().read_text(encoding="utf-8-sig"))))) == 3
    app.pins.include.value = [first.id, second.id]
    assert len(set(app.pins.matrix()[0])) == 3


def test_navigation_modes_presets_do_not_reset_pins_or_plot(app):
    p = add(app)
    plot = app.plot
    app.set_extent((11, 12, 20, 21))
    span = np.diff(np.array(app.extent).reshape(2, 2), axis=1).ravel()
    app.pins.select(p.id)
    np.testing.assert_allclose(np.diff(np.array(app.extent).reshape(2, 2), axis=1).ravel(), span)
    app.panel_mode.value = "Inspector"
    app.panel_mode.value = "Visualization"
    app.show_osm.value = True
    assert app.pins.pins[0].id == p.id and app.plot is plot
    assert "pins" not in app.settings()
    assert app.pins.comparison in app.map_region.objects
    assert app.pins.view in app.inspector_panel.objects


def test_marker_tap_uses_saved_identity_and_does_not_ordinary_inspect(app, monkeypatch):
    p = add(app)
    real = app.inspect
    calls = []

    def inspect(*args, **kwargs):
        calls.append(kwargs)
        return real(*args, **kwargs)

    monkeypatch.setattr(app, "inspect", inspect)
    app._tap(SimpleNamespace(x=p.clicked[0], y=p.clicked[1]))
    assert len(calls) == 1 and "network_product" in calls[0]
    assert app.pins.active == p.id


def test_png_receives_same_pin_coordinates_independently_of_selection(app, monkeypatch):
    p = add(app)
    capture = Mock(return_value=app.output_dir / "test.png")
    monkeypatch.setattr("app.export_scene", capture)
    app.export()
    assert capture.call_args.kwargs["pins"]["x"] == [p.clicked[0]]
    assert capture.call_args.kwargs["pins"]["y"] == [p.clicked[1]]
    assert capture.call_args.args[-2] is app.selection.boundary
    assert capture.call_args.args[-1] is app.selection.coarse_outline


def test_tens_of_pins_no_arbitrary_cap(app):
    # Distinct session targets, generated without additional raster fixtures.
    from dataclasses import replace

    p = add(app)
    app.pins.pins = [replace(p, id=f"pin-{i:04}", label=letter(i), name=f"Pin {i}") for i in range(1, 61)]
    app.pins.refresh()
    assert len(app.pins.matrix()[0]) == 61
    assert len(app.pins.source.data["x"]) == 60
    assert letter(26) == "Z" and letter(27) == "AA" and letter(60) == "BH"


def test_widget_callbacks_schedule_bokeh_mutations_and_visible_errors(app, monkeypatch):
    p = add(app)
    queued = []
    monkeypatch.setattr(app, "_schedule", queued.append)
    app.pins.include.value = []
    assert len(queued) == 1 and app.pins.pins[0].included
    queued.pop()()
    assert not app.pins.pins[0].included
    app.pins._list_changed(SimpleNamespace(new=p.id))
    assert len(queued) == 1
    queued.pop()()
    app.pins._action(lambda: (_ for _ in ()).throw(ValueError("Source missing")))
    queued.pop()()
    assert "Source missing" in app.pins.message.object


def test_scroll_panel_children_do_not_shrink_over_open_inspector(app):
    assert app.inspector_panel.styles["flex-shrink"] == "0"
    assert app.inspector_panel.styles["max-height"] == "none"
    assert app.cell_inspector.view.styles["max-height"] == "none"
    assert app.cell_inspector.view.styles["flex-shrink"] == "0"
    assert app.pins.view.styles["flex-shrink"] == "0"

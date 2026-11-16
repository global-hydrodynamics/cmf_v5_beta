"""Independent scientific oracles for Inspector profiles, IDs and graph counts."""

from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest
from netCDF4 import Dataset

from app import Explorer
from conftest import write_network
from inspector import InspectorProducts, UpstreamIndex
from map_reader import MapReader
from test_v2 import products


def graph(dest):
    g = SimpleNamespace(nx=len(dest), ny=1)
    x = np.array([v + 1 if v is not None else -9 for v in dest])[None, :]
    y = np.where(x > 0, 1, -9)
    return UpstreamIndex(x, y, g)


def reverse_oracle(dest):
    incoming = [set() for _ in dest]
    for node, target in enumerate(dest):
        if target is not None:
            incoming[target].add(node)
    result = []
    for target in range(len(dest)):
        reached = {target}
        pending = [target]
        while pending:
            for node in incoming[pending.pop()] - reached:
                reached.add(node)
                pending.append(node)
        result.append(len(reached) - 1)
    return result, [len(group) for group in incoming]


@pytest.mark.parametrize(
    "dest",
    [
        [2, 2, 3, None, 3, 4, None],  # source0/1 merge at2, then3;5->4->3
        [1, 2, 0, 1, 3, None],  # cycle plus two attached nodes
        [0, 0, 1, None],  # self-loop: total excludes itself, in-degree includes it
        [None, None, None],
    ],
)
def test_upstream_counts_hand_checked_trees_cycles_and_endpoints(dest):
    index = graph(dest)
    total, direct = reverse_oracle(dest)
    np.testing.assert_array_equal(index.total, total)
    np.testing.assert_array_equal(index.direct, direct)
    if len(dest) == 7:
        assert index.total[3] == 5 and index.direct[3] == 2


def test_graph_random_oracle_invalid_codes_and_long_chain():
    rng = np.random.default_rng(821)
    for _ in range(8):
        dest = [int(v) if v >= 0 else None for v in rng.integers(-2, 61, size=61)]
        index = graph(dest)
        total, direct = reverse_oracle(dest)
        np.testing.assert_array_equal(index.total, total)
        np.testing.assert_array_equal(index.direct, direct)
    index = UpstreamIndex(
        np.array([[2, 7, 1, -9999, 3]]), np.array([[1, 1, -9, -9999, 1]]), SimpleNamespace(nx=5, ny=1)
    )
    assert index.direct.tolist() == [0, 1, 1, 0, 0] and index.total.tolist() == [0, 1, 1, 0, 0]
    dest = list(range(1, 20001)) + [None]
    index = graph(dest)
    assert index.total[-1] == 20000 and index.direct[-1] == 1


def write_profile(
    root, values, dims=("layer", "lat", "lon"), rev_lat=False, rev_lon=False, units="m", dtype="f4", layer_coords=True
):
    path = root / "netcdf/fldhgt.nc"
    path.parent.mkdir(exist_ok=True)
    with Dataset(path, "w") as ds:
        ds.createDimension("lon", 4)
        ds.createDimension("lat", 3)
        ds.createDimension("layer", len(values))
        lon = np.arange(4) + 10.5
        lat = 22.5 - np.arange(3)
        ds.createVariable("lon", "f8", ("lon",))[:] = lon[::-1] if rev_lon else lon
        ds.createVariable("lat", "f8", ("lat",))[:] = lat[::-1] if rev_lat else lat
        if layer_coords:
            ds.createVariable("layer", "i4", ("layer",))[:] = np.arange(1, len(values) + 1)
        v = ds.createVariable("fldhgt", dtype, dims, fill_value=-9999)
        v.units = units
        a = values[:, ::-1, :] if rev_lat else values
        a = a[:, :, ::-1] if rev_lon else a
        v[:] = a.transpose(tuple(("layer", "lat", "lon").index(dim) for dim in dims))
    return path


@pytest.mark.parametrize(
    "dims,rev_lat,rev_lon",
    [
        (("layer", "lat", "lon"), False, False),
        (("lon", "layer", "lat"), True, True),
        (("lat", "lon", "layer"), True, False),
    ],
)
def test_native_profile_netcdf_layout_and_binary_exact_agreement(map_dir, dims, rev_lat, rev_lon):
    values = np.arange(24, dtype="<f4").reshape(2, 3, 4)
    values[:, 1, 1] = [-2, 0]
    values[:, 0, 0] = -9999
    values.tofile(map_dir / "fldhgt.bin")
    write_profile(map_dir, values, dims, rev_lat, rev_lon)
    reader = MapReader(map_dir)
    native = InspectorProducts(reader)
    assert native.profile_source.netcdf
    np.testing.assert_array_equal(native.profile(1, 1), [-2, 0])
    assert native.profile(0, 0).mask.all()
    native.profile_source.path.unlink()  # test-only synthetic file, force explicit Binary path
    binary = InspectorProducts(reader)
    assert not binary.profile_source.netcdf
    for row, col in [(1, 1), (2, 3)]:
        np.testing.assert_array_equal(binary.profile(row, col), values[:, row, col])
    assert reader.geometry.layers == 2  # Never hardcode the actual sample's ten layers.


@pytest.mark.parametrize("problem", ["units", "dtype", "layers", "size", "layer_order"])
def test_profile_contract_rejects_invalid_metadata_without_substitution(map_dir, problem):
    values = np.ones((3 if problem == "layers" else 2, 3, 4), dtype="f4")
    if problem == "size":
        (map_dir / "fldhgt.bin").write_bytes(b"1234")
    else:
        p = write_profile(
            map_dir, values, units="cm" if problem == "units" else "m", dtype="f8" if problem == "dtype" else "f4"
        )
        if problem == "layer_order":
            with Dataset(p, "a") as ds:
                ds.variables["layer"][:] = [2, 1]
    native = InspectorProducts(MapReader(map_dir))
    assert native.profile_source is None and native.profile(0, 0) is None and native.messages


def scientific_fields(root):
    for key, value, dtype in [
        ("elevtn", -3.25, "<f4"),
        ("rivwth", 0, "<f4"),
        ("rivhgt", 2, "<f4"),
        ("rivlen", 12340, "<f4"),
        ("nxtdst", 23450, "<f4"),
        ("ctmare", 2500000, "<f4"),
        ("basin", 71, "<i4"),
    ]:
        np.full((3, 4), value, dtype=dtype).tofile(root / f"{key}.bin")
    np.stack([np.full((3, 4), -1), np.zeros((3, 4))]).astype("<f4").tofile(root / "fldhgt.bin")


def test_summary_native_outlets_assignment_units_true_ids_and_accordion_state(products):
    scientific_fields(products)
    np.full((3, 4), 42, dtype="<i4").tofile(products / "subbsn-sample.bin")
    path = products / "fine/tile.catmxy.bin"
    data = np.fromfile(path, dtype="<i2").reshape(2, 6, 8)
    data[:, 2:5, 1:5] = 1
    data.tofile(path)
    app = Explorer(products, products.parent / "out")
    app.raster_type.value = "highres"
    result = app.inspect(11.000001, 21.999999)
    panel = app.cell_inspector
    assert app.selected == (0, 0) and app.selection.geographic_cell == (1, 1)
    text = panel.summary.object
    assert [
        text.index(label) for label in ["Outlet coordinates", "Upstream Area", "Unit Catchment ID", "Clicked Location"]
    ] == sorted(
        text.index(label) for label in ["Outlet coordinates", "Upstream Area", "Unit Catchment ID", "Clicked Location"]
    )
    assert "Lat 22.40000° · Lon 10.60000°" in text and "(1, 1)" in text
    assert "Lat 22.00000° · Lon 11.00000°" in text
    assert "Selection: High-resolution catmxy assignment" == panel.method.object
    for value in ["-3.25", "12.34", "23.45", "2.5"]:
        assert value in panel.geometry.object
    assert ">0<" in panel.geometry.object
    assert result["fldhgt [m]"] == [-1, 0] and result["subbsn [1]"] == 42
    assert "Basin ID · basin" in panel.connectivity.object and ">71<" in panel.connectivity.object
    assert "Subbasin ID · subbsn-sample.bin" in panel.connectivity.object and ">42<" in panel.connectivity.object
    assert panel.advanced_section.active == [] and panel.profile_section.active == []
    assert "High-resolution ix (1-based, Fortran)" in panel.advanced.object
    assert "bsncol" not in panel.geometry.object and "subcol" not in panel.geometry.object
    panel.advanced_section.active = [0]
    panel.profile_section.active = [0]
    cached = panel._graphs["nextxy"]
    app.inspect(12.25, 21.75)
    assert (
        panel.advanced_section.active == [0]
        and panel.profile_section.active == [0]
        and panel._graphs["nextxy"] is cached
    )
    app.inspect(10.25, 22.75)
    assert app.selected is None and "Unavailable" in panel.summary.object
    assert panel.advanced_section.active == [0] and "-999" in panel.advanced.object


def test_native_outlet_longitude_not_replaced_by_periodic_render_wrap(tmp_path):
    (tmp_path / "params.txt").write_text("4 NX\n1 NY\n2 NLFP\n90 spacing\n0 west\n360 east\n-45 south\n45 north\n")
    np.ones((1, 4), dtype="<f4").tofile(tmp_path / "uparea.bin")
    np.array([[[-179, 1, 2, 3]], [[0, 0, 0, 0]]], dtype="<f4").tofile(tmp_path / "lonlat.bin")
    app = Explorer(tmp_path, tmp_path.parent / "out")
    info = app.inspect(45, 0)
    assert app.scene.products.outlets[0][0, 0] == 181
    assert info["source outlet longitude"] == -179
    assert "Lon -179.00000°" in app.cell_inspector.summary.object


def test_bifurcation_incidence_first_valid_dedup_matches_renderer(products):
    app = Explorer(products, products.parent / "out")
    panel = app.cell_inspector
    bif = app.scene.products.bifurcations
    assert len(bif["ids"]) == 2 and bif["stats"]["duplicates"] == 1
    inc, out = panel.bifurcation_counts["Channel"]
    assert out[0] == 1 and inc[1] == 1 and out.sum() == 1
    inc, out = panel.bifurcation_counts["Overland"]
    assert out[1] == 1 and inc[11] == 1 and out.sum() == 1
    app.inspect(11.5, 22.5)
    assert (
        "Incoming 1 · Outgoing 0" in panel.connectivity.object
        and "Incoming 0 · Outgoing 1" in panel.connectivity.object
    )


def test_unavailable_ids_endpoints_and_selected_network_when_hidden(map_dir):
    write_network(map_dir)
    app = Explorer(map_dir, map_dir.parent / "out")
    app.inspect(12.5, 22.5)
    panel = app.cell_inspector
    assert "terminal / boundary" in panel.connectivity.object
    assert "Subbasin ID ·" not in panel.connectivity.object and "subcol is a display-color" in panel.connectivity.object
    assert "Unavailable" in panel.summary.object and "Unavailable" in panel.profile.object
    assert panel.method.object == "Selection: Geographic coarse-grid containment"
    app.inspect(13.5, 22.5)
    assert "outside this map" in panel.connectivity.object
    app.inspect(11.5, 20.5)
    assert "self link" in panel.advanced.object
    app.inspect(12.5, 21.5)
    assert "missing / unassigned" in panel.connectivity.object


ROOT = Path(__file__).resolve().parents[3]


@pytest.mark.skipif(not (ROOT / "map/mekong_15min/params.txt").exists(), reason="Mekong unavailable")
def test_mekong_profile_ids_graph_counts_outlets_and_source_switch(tmp_path):
    app = Explorer(ROOT / "map/mekong_15min", tmp_path)
    app.apply_preset("p01-f04b", True)
    result = app.inspect(105.80095712381517, 10.79728379360465)
    panel = app.cell_inspector
    assert app.selected == (97, 63) and result["unit catchment assigned pixel count"] == 228
    native = np.memmap(
        app.reader.path / "fldhgt.bin", dtype="<f4", mode="r", shape=(app.reader.geometry.layers, 120, 80)
    )
    np.testing.assert_array_equal(result["fldhgt [m]"], native[:, 97, 63])
    assert len(result["fldhgt [m]"]) == 10 and result["subbsn [1]"] == 63
    assert "105.59792" in panel.summary.object and "10.82958" in panel.summary.object
    assert "798.716" in panel.summary.object
    for source in ["nextxy", "nextxy_noedge"]:
        app.representation.value = "off"
        app.network_choice.value = source
        info = app.inspect(*app.selection.clicked)
        index = panel._graphs[source]
        net = app._networks[source]
        dest = index.destination.tolist()
        total, direct = reverse_oracle([d if d >= 0 else None for d in dest])
        for node in [97 * 80 + 63, 96 * 80 + 63, int(np.argmax(index.total))]:
            assert index.total[node] == total[node] and index.direct[node] == direct[node]
        assert info["network product"] == source
    app.raster_type.value = "coarse"
    assert app.selected == (96, 63)
    assert "Geographic coarse-grid containment" in panel.method.object

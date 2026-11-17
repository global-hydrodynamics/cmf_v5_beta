"""Native NetCDF contracts: orientation, raw assignments, lazy reads and Binary parity."""

from pathlib import Path

import numpy as np
import pytest
from netCDF4 import Dataset

from hires import discover_tiles
from map_reader import MapReader
from selection import CatchmentIndex
from test_v2 import products


def write_product(directory, name, values, g, units, *, flip_y=False, flip_x=False, transpose=False):
    directory.mkdir(exist_ok=True)
    names = ("catmxx", "catmyy") if name == "catmxy" else (name,)
    path = directory / f"tile.{name}.nc"
    with Dataset(path, "w") as ds:
        ds.createDimension("lat", g.ny)
        ds.createDimension("lon", g.nx)
        for key, coords, unit in [("lat", g.lat[::-1] if flip_y else g.lat, "degrees_north"),
                                  ("lon", g.lon[::-1] if flip_x else g.lon, "degrees_east")]:
            v = ds.createVariable(key, "f8", (key,))
            v.units = unit
            v[:] = coords
        arrays = values if name == "catmxy" else [values]
        for key, values in zip(names, arrays):
            a = values[::-1] if flip_y else values
            a = a[:, ::-1] if flip_x else a
            dims = ("lon", "lat") if transpose else ("lat", "lon")
            var = ds.createVariable(key, a.dtype, dims, fill_value=-9999 if a.dtype.itemsize != 1 else -9,
                                    zlib=True, complevel=3, shuffle=True)
            var.units = units
            var[:] = a.T if transpose else a
    return path


def nc_products(root, **orientation):
    tile = discover_tiles(root, [])["fine/tile"]
    directory = root / "fine_nc"
    directory.mkdir()
    (directory / "location.txt").write_text((root / "fine/location.txt").read_text())
    for name in tile.files:
        shape = (2 if name == "catmxy" else 1, tile.geometry.ny, tile.geometry.nx)
        raw = np.asarray(tile.mmap(name)).copy().reshape(shape)
        write_product(directory, name, raw if name == "catmxy" else raw[0], tile.geometry,
                      "code" if name == "visual" else "1" if raw.dtype.kind == "i" else "m", **orientation)
    return tile


@pytest.mark.parametrize("flip_y,flip_x,transpose", [(False, False, False), (True, False, False),
                                                     (False, True, True), (True, True, True)])
def test_netcdf_preferred_native_orientation_and_binary_parity(products, flip_y, flip_x, transpose):
    binary = nc_products(products, flip_y=flip_y, flip_x=flip_x, transpose=transpose)
    messages = []
    nc = discover_tiles(products, messages)["fine/tile"]
    assert not messages and nc.storage == "NetCDF"
    assert not nc._maps  # Header discovery has not loaded or mapped any native raster.
    rows, cols = np.array([0, 2, 5]), np.array([0, 3, 7])
    for key in binary.files:
        assert nc.files[key].suffix == ".nc"
        np.testing.assert_allclose(nc.sample(key, rows, cols), binary.sample(key, rows, cols), equal_nan=True)
    assert not nc._maps
    assert nc.sample("catmxy", np.array([0]), np.array([0]))[:, 0, 0].tolist() == [-999, -999]
    np.testing.assert_allclose(nc.sample("difference", rows, cols), binary.sample("difference", rows, cols), equal_nan=True)


def test_netcdf_assignment_boundaries_percentiles_and_native_click(products):
    binary = nc_products(products)
    nc = discover_tiles(products, [])["fine/tile"]
    coarse = MapReader(products).geometry
    a, b = CatchmentIndex(binary, coarse).boundary(1, 1), CatchmentIndex(nc, coarse).boundary(1, 1)
    assert a.pixel_count == b.pixel_count
    np.testing.assert_array_equal(a.segments, b.segments)
    assert nc.percentiles("elevtn", coarse=coarse) == binary.percentiles("elevtn", coarse=coarse)
    inherited = MapReader(products).read("uparea").filled(np.nan) * 1e-6
    assert nc.percentiles("uparea", coarse=coarse, inherited=inherited) == binary.percentiles("uparea", coarse=coarse, inherited=inherited)
    from app import Explorer
    app = Explorer(products, products.parent / "nc-exports")
    app.point_select.value = "catchment"
    app.inspect(11.75, 21.75)
    native = nc.sample("catmxy", np.array([2]), np.array([3]))[:, 0, 0]
    assert app.selected == (int(native[1]) - 1, int(native[0]) - 1)
    assert app.point_select.value == "grid" and app.selection.native_pixel is None
    assert app.selection.boundary is None and not app.cell_inspector.pixel_section.visible
    assert b.pixel_count > 0  # Explicit fallback/native tooling still matches Binary scientifically.


def test_native_uparea_units_and_fill_are_not_inherited(products):
    binary = nc_products(products)
    values = np.arange(48, dtype="<f4").reshape(6, 8) * 1e6
    values[0, 0] = -9999
    write_product(products / "fine_nc", "uparea", values, binary.geometry, "m2")
    nc = discover_tiles(products, [])["fine/tile"]
    actual = nc.sample("uparea", np.array([0, 1]), np.array([0, 2]))
    assert np.isnan(actual[0, 0])
    assert actual[1, 1] == 10  # genuine native product, converted m² -> km²


def test_invalid_netcdf_metadata_never_silently_uses_binary(products):
    binary = nc_products(products)
    write_product(products / "fine_nc", "elevtn", np.ones((6, 8), dtype="<f4"), binary.geometry, "feet")
    messages = []
    tile = discover_tiles(products, messages)["fine/tile"]
    assert "elevtn" not in tile.files
    assert any("invalid NetCDF" in m and "units" in m for m in messages)


def test_binary_fallback_only_for_absent_optional_netcdf(products):
    nc_products(products)
    (products / "fine_nc/tile.visual.nc").unlink()
    tile = discover_tiles(products, [])["fine/tile"]
    assert tile.files["catmxy"].suffix == ".nc"
    assert tile.files["visual"].suffix == ".bin"
    assert tile.storage == "NetCDF + Binary optional fields"


def test_all_invalid_netcdf_fields_remove_the_unavailable_tile(products):
    nc_products(products)
    for path in (products / "fine_nc").glob("*.nc"):
        with Dataset(path, "a") as ds:
            for name, variable in ds.variables.items():
                if name not in ("lat", "lon"):
                    variable.units = "invalid units"
    messages = []
    assert "fine/tile" not in discover_tiles(products, messages)
    assert messages and all("invalid NetCDF product skipped" in text for text in messages)


@pytest.mark.parametrize("units,available", [("code", True), ("1", True), ("m", False)])
def test_visual_categorical_units_follow_registry_and_keep_legacy_support(products, units, available):
    binary = nc_products(products)
    values = np.array([[0, 1, 2, 3, 5, 7, 10, 25]] * 6, dtype="i1")
    values[0, 0] = -9
    write_product(products / "fine_nc", "visual", values, binary.geometry, units)
    messages = []
    tile = discover_tiles(products, messages)["fine/tile"]
    assert ("visual" in tile.files) == available
    if available:
        assert tile.files["visual"].suffix == ".nc"
        np.testing.assert_array_equal(tile.sample("visual", np.arange(6), np.arange(8)), values)
        assert not messages
        from scene import Scene
        from presets import PresetLibrary
        reader = MapReader(products)
        missing = PresetLibrary().missing_products("p01-f04b", reader, Scene(reader))
        assert not any("one high-resolution tile" in item for item in missing)
    else:
        assert any("expected units" in message for message in messages)


def test_categorical_code_units_do_not_relax_catmxy_assignment_contract(products):
    nc_products(products)
    with Dataset(products / "fine_nc/tile.catmxy.nc", "a") as ds:
        ds["catmxx"].units = "code"
    messages = []
    tile = discover_tiles(products, messages)["fine/tile"]
    assert "catmxy" not in tile.files
    assert any("expected units" in message for message in messages)

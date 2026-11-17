"""Exercise shipped s03 variable selections against actual NetCDF conversion."""
import re
import shutil
import struct
import subprocess
from pathlib import Path

import pytest

from map.tools.code import convert_highres_binary_to_netcdf as converter

netCDF4 = pytest.importorskip("netCDF4")
np = pytest.importorskip("numpy")

ROOT = Path(__file__).resolve().parents[3]
REGISTRY = ROOT / "variable_table/map_variables.csv"
BASE = "catmxy downxy elevtn uparea hand flddif rivwth".split()
MISSING = {"catmz100": "int8", "catmzz": "int8", "grdare": "float32", "visual": "int8"}


@pytest.mark.parametrize("source", [
    "map/tools/script_bin2nc/s03-convert_highres_netcdf.sh",
    "map/mekong_15min/script_bin2nc/s03-convert_highres_netcdf.sh",
])
def test_default_s03_adds_missing_registered_products_losslessly(tmp_path, source):
    script_text = (ROOT / source).read_text()
    variables = re.search(r'^VARS="([^"]+)"', script_text, re.M).group(1).split()
    assert set(BASE) | set(MISSING) <= set(variables)
    if "mekong_15min" in source:
        assert "flwdir" in variables
    # Run the actual shipped wrapper/converter in a small map; never touch real data.
    code = tmp_path / "map/tools/code"
    code.mkdir(parents=True)
    shutil.copyfile(ROOT / "map/tools/code/convert_highres_binary_to_netcdf.py",
                    code / "convert_highres_binary_to_netcdf.py")
    registry = tmp_path / "variable_table/map_variables.csv"
    registry.parent.mkdir()
    shutil.copyfile(REGISTRY, registry)
    map_dir = tmp_path / "map/sample"
    script_dir = map_dir / "script_bin2nc"
    script_dir.mkdir(parents=True)
    (map_dir / "params.txt").write_text("4\n3\n1\n1\n0\n4\n0\n3\n")
    script = script_dir / "s03-convert_highres_netcdf.sh"
    # Keep only concurrency small; use the real configured variable list unchanged.
    script.write_text(re.sub(r'^JOBS=.*$', 'JOBS=1', script_text, flags=re.M))
    binary = map_dir / "1min"
    binary.mkdir()
    (binary / "location.txt").write_text(
        "1 narea\niarea carea west east south north nx ny csize\n"
        "1 tile 0 4 0 3 4 3 1\n"
    )
    rows = converter.registry_rows(REGISTRY)
    originals = {}
    for variable in variables:
        selected = converter.rows_for_tile(rows, "1min", "tile", variable)
        dtype = selected[0]["dtype"]
        if variable in MISSING:
            assert dtype == MISSING[variable]
        count = 12 * int(selected[0]["record_count"])
        values = list(range(count))
        if dtype == "float32":
            values = [value + 0.25 for value in values]
        values[0] = int(selected[0]["missing_value"])
        code = {"int8": "b", "int16": "h", "int32": "i", "float32": "f"}[dtype]
        raw = struct.pack(f"<{count}{code}", *values)
        originals[variable] = raw
        (binary / f"tile.{variable}.bin").write_bytes(raw)
    # Simulate the reported state: seven products already converted.
    converter.convert_variable(map_dir, "1min", BASE, REGISTRY, False, 3, 1)
    existing = {path: path.read_bytes() for path in (map_dir / "1min_nc").glob("*.nc")}
    result = subprocess.run(["sh", str(script)], cwd=script_dir, text=True,
                            capture_output=True, timeout=30)
    assert result.returncode == 0, result.stdout + result.stderr
    assert f"Converted: {len(variables) - 7}" in result.stdout
    assert "Skipped:   7" in result.stdout
    assert all(path.read_bytes() == data for path, data in existing.items())
    assert {path.name for path in (map_dir / "1min_nc").glob("*.nc")} == {
        f"tile.{variable}.nc" for variable in variables
    }
    for variable in variables:
        selected = sorted(converter.rows_for_tile(rows, "1min", "tile", variable),
                          key=lambda row: int(row["record_index"] or "1"))
        with netCDF4.Dataset(map_dir / f"1min_nc/tile.{variable}.nc") as ds:
            actual = b""
            for row in selected:
                field = ds.variables[row["name"]]
                field.set_auto_maskandscale(False)
                assert field.dimensions == ("lat", "lon")
                assert field.dtype == np.dtype(row["dtype"])
                actual += field[:].astype(np.dtype(row["dtype"]).newbyteorder("<")).tobytes()
            assert actual == originals[variable]
    assert (map_dir / "1min_nc/location.txt").read_bytes() == (binary / "location.txt").read_bytes()
    assert all((binary / f"tile.{variable}.bin").read_bytes() == data
               for variable, data in originals.items())

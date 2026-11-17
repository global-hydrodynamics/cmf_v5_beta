"""Exercise shipped s03 variable selections against actual NetCDF conversion."""
import re
import shutil
import struct
from unittest.mock import Mock
import subprocess
from pathlib import Path

import pytest

from map.tools.code import convert_highres_binary_to_netcdf as converter
from map.tools.tests.test_bin2nc_workflow import run_tty

netCDF4 = pytest.importorskip("netCDF4")
np = pytest.importorskip("numpy")

ROOT = Path(__file__).resolve().parents[3]
REGISTRY = ROOT / "variable_table/map_variables.csv"
BASE = "catmxy downxy elevtn uparea hand flddif rivwth".split()
MISSING = {"catmz100": "int8", "catmzz": "int8", "grdare": "float32", "visual": "int8"}


@pytest.mark.parametrize("source", [
    "map/tools/script_format_conv/s03-convert_highres_netcdf.sh",
    "map/mekong_15min/script_format_conv/s03-convert_highres_netcdf.sh",
])
def test_default_s03_adds_missing_registered_products_losslessly(tmp_path, source):
    script_text = (ROOT / source).read_text()
    variables = re.search(r'^VARS="([^"]+)"', script_text, re.M).group(1).split()
    assert variables == ["all"]
    variables = converter.registered_variables(converter.registry_rows(REGISTRY))
    assert set(variables) == set(BASE) | set(MISSING) | {"flwdir"}
    if "mekong_15min" not in source:
        variables.remove("flwdir")  # Japan-like input: optional registered Binary absent.
    # Run the actual shipped wrapper/converter in a small map; never touch real data.
    code = tmp_path / "map/tools/code"
    code.mkdir(parents=True)
    shutil.copyfile(ROOT / "map/tools/code/convert_highres_binary_to_netcdf.py",
                    code / "convert_highres_binary_to_netcdf.py")
    registry = tmp_path / "variable_table/map_variables.csv"
    registry.parent.mkdir()
    shutil.copyfile(REGISTRY, registry)
    map_dir = tmp_path / "map/sample"
    script_dir = map_dir / "script_format_conv"
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
    (binary / "tile.unregistered.bin").write_bytes(b"not a registered raster")
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
    transcript = run_tty(
        script, script_dir, b"invalid\ny\n",
        f"Overwrite all {len(variables)} existing selected outputs?".encode(),
    )
    assert "Please answer y or N" in transcript
    assert "already exists. Overwrite?" not in transcript
    assert f"Converted: {len(variables)}" in transcript
    transcript = run_tty(
        script, script_dir, b"n\ny\n" + b"n\n" * (len(variables) - 1),
        f"Overwrite all {len(variables)} existing selected outputs?".encode(),
    )
    assert "already exists. Overwrite?" in transcript
    assert "Converted: 1" in transcript
    assert f"Skipped:   {len(variables) - 1}" in transcript



@pytest.mark.parametrize("answers,converted,skipped", [
    (["invalid", "y"], 2, 0),
    (["n", "y", "n"], 1, 1),
    (["", "", ""], 0, 2),
])
def test_bulk_and_individual_overwrite_decisions(tmp_path, monkeypatch, answers, converted, skipped):
    planned = []
    for name in ("a", "b"):
        output = tmp_path / f"{name}.nc"
        output.write_text("keep")
        planned.append((tmp_path / f"{name}.bin", output, {}, [], 3, False))
    monkeypatch.setattr(converter.sys.stdin, "isatty", lambda: True)
    replies = Mock(side_effect=answers)
    monkeypatch.setattr("builtins.input", replies)
    tasks, retained = converter.select_tasks(planned, False, True)
    assert len(tasks) == converted and len(retained) == skipped
    assert all(task[-1] for task in tasks)
    assert all(task[1].read_text() == "keep" for task in planned)
    assert "Overwrite all 2" in replies.call_args_list[0].args[0]
    assert replies.call_count == len(answers)


def test_noninteractive_and_force_do_not_prompt(tmp_path, monkeypatch):
    output = tmp_path / "a.nc"
    output.write_text("keep")
    planned = [(tmp_path / "a.bin", output, {}, [], 3, False)]
    monkeypatch.setattr(converter.sys.stdin, "isatty", lambda: False)
    prompt = Mock(side_effect=AssertionError("must not prompt"))
    monkeypatch.setattr("builtins.input", prompt)
    assert converter.select_tasks(planned, False, True) == ([], planned)
    tasks, skipped = converter.select_tasks(planned, True, True)
    assert len(tasks) == 1 and tasks[0][-1] and not skipped
    prompt.assert_not_called()


def test_preflight_skips_missing_and_validates_all_resolutions_before_writing(tmp_path):
    for hires in ("1min", "15sec"):
        binary = tmp_path / hires
        binary.mkdir()
        (binary / "location.txt").write_text(
            "1 narea\niarea carea west east south north nx ny csize\n1 tile 0 2 0 2 2 2 1\n"
        )
        (binary / "tile.visual.bin").write_bytes(bytes([0, 1, 2, 25]))
    variables, planned, missing = converter.plan_conversion(
        tmp_path, ["1min", "15sec"], ["all"], REGISTRY, 3
    )
    assert len(variables) == 12 and len(planned) == 2 and len(missing) == 22
    assert not (tmp_path / "1min_nc").exists()
    (tmp_path / "15sec/tile.visual.bin").write_bytes(b"bad")
    with pytest.raises(converter.ConversionError, match="bytes"):
        converter.plan_conversion(tmp_path, ["1min", "15sec"], ["all"], REGISTRY, 3)
    assert not (tmp_path / "1min_nc").exists()


def test_csv_new_variable_is_selected_without_changing_default_list():
    rows = converter.registry_rows(REGISTRY)
    added = dict(rows[-1], binary_filename="<HIRES>/<AREA>.newfield.bin")
    assert "newfield" in converter.registered_variables(rows + [added])

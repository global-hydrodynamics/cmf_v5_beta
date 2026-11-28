#!/usr/bin/env python3
"""Validate the committed Mekong map sample and its registered binary products."""
from __future__ import annotations

import csv
import fnmatch
import struct
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MAP = ROOT / "map" / "mekong_15min"
REGISTRY = ROOT / "variable_table" / "map_variables.csv"
DTYPE_BYTES = {"int8": 1, "int16": 2, "int32": 4, "float32": 4}
sys.path.insert(0, str(ROOT / "map" / "tools" / "code"))
from map_metadata import read_diminfo_nml, read_nml_values


def read_map_dimensions() -> dict[str, int]:
    """Read base-map dimensions from standard v5 params.nml metadata."""
    geometry = read_nml_values(MAP / "params.nml")
    return {"NX": geometry.nx, "NY": geometry.ny, "NLFP": geometry.nlfp}


def read_input_dimensions(path: Path) -> dict[str, int]:
    """Read runoff-grid dimensions and INPN from a v5 diminfo descriptor."""
    info = read_diminfo_nml(path)
    return {
        "INPNX": info.nxin,
        "INPNY": info.nyin,
        "INPN": info.inpn,
    }


def registry_rows() -> list[dict[str, str]]:
    with REGISTRY.open(newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


def rows_for_sample_file(path: Path, rows: list[dict[str, str]]) -> list[dict[str, str]]:
    """Resolve Binary products from the registry's standard NetCDF names."""
    matches = []
    exact = []
    for row in rows:
        if row.get("product_kind") not in {"binary_map", "binary_mult"}:
            continue
        filename = row["filename"]
        patterns = []
        for item in filename.split(";"):
            item = item.strip()
            if item.endswith(".nc"):
                item = item[:-3] + ".bin"
            patterns.append(item.replace("<ROFFTAG>", "*"))
        if path.name in patterns:
            exact.append(row)
            continue
        if any(fnmatch.fnmatchcase(path.name, pattern) for pattern in patterns):
            matches.append(row)
            continue
        prefix = "<HIRES>/<AREA>."
        if filename.startswith(prefix) and path.parent.name == "1min":
            suffix = filename[len(prefix):]
            if suffix.endswith(".nc"):
                suffix = suffix[:-3] + ".bin"
            if path.name == f"{path.parent.name}.{suffix}":
                matches.append(row)
    if not exact and not matches and path.name.startswith("upbasin-") and path.suffix == ".bin":
        matches = [row for row in rows if row["filename"] == "upbasin.nc"]
    return exact or matches


def validate_registered_binary_size(
    path: Path,
    rows: list[dict[str, str]],
    dims: dict[str, int],
    map_root: Path,
) -> bool:
    """Validate a registry-listed binary; return False for user-added files."""
    matches = rows_for_sample_file(path, rows)
    if not matches:
        return False

    expected_size = 0
    for row in matches:
        dtype = row["dtype"].strip().lower()
        if dtype not in DTYPE_BYTES:
            raise AssertionError(f"unsupported dtype {dtype!r} for {path.name}")
        variables = [name.strip() for name in row["dimensions"].split(",") if name.strip()]
        product = 1
        for variable in variables:
            if variable == "INPN":
                descriptor = map_root / path.name.replace("inpmat_", "diminfo_").replace(".bin", ".nml")
                if not descriptor.is_file():
                    raise AssertionError(f"paired input descriptor missing: {descriptor.name}")
                variable_size = read_input_dimensions(descriptor)["INPN"]
            else:
                if variable not in dims:
                    raise AssertionError(f"unresolved dimension {variable!r} for {path.name}")
                variable_size = dims[variable]
            product *= variable_size
        expected_size += product * DTYPE_BYTES[dtype]

    actual_size = path.stat().st_size
    if actual_size != expected_size:
        raise AssertionError(f"{path.name}: registry size mismatch (expected {expected_size}, got {actual_size})")
    return True


class MekongSampleTests(unittest.TestCase):
    """Check current sample products without freezing the full generated inventory."""

    def test_standard_runoff_pair_uses_diminfo_name_and_matching_geometry(self) -> None:
        dims = read_map_dimensions()
        descriptor = MAP / "diminfo_test-1deg.nml"
        info = read_diminfo_nml(descriptor)
        input_dims = read_input_dimensions(descriptor)

        self.assertEqual(dims, {"NX": 80, "NY": 120, "NLFP": 10})
        self.assertEqual(input_dims, {"INPNX": 360, "INPNY": 180, "INPN": 4})
        self.assertEqual([info.west, info.east, info.north, info.south], [90.0, 110.0, 35.0, 5.0])
        self.assertEqual([info.westin, info.eastin, info.northin, info.southin, info.olatin],
                         [-180.0, 180.0, 90.0, -90.0, "NtoS"])
        self.assertEqual(info.inpmat_file, "inpmat_test-1deg.nc")
        self.assertGreater((MAP / info.inpmat_file).stat().st_size, 0)

    def test_era5land_registry_pair_uses_same_diminfo_convention(self) -> None:
        rows = registry_rows()
        descriptor_rows = [r for r in rows if r["category_id"] == "23" and r["name"] == "diminfo_<ROFFTAG>"]
        matrix_rows = [r for r in rows if r["category_id"] == "23" and r["filename"] == "inpmat_<ROFFTAG>.nc"]
        self.assertEqual(len(descriptor_rows), 1)
        self.assertEqual(descriptor_rows[0]["filename"], "diminfo_<ROFFTAG>.nml")
        self.assertEqual([r["name"] for r in matrix_rows], ["inpx", "inpy", "inpa"])
        self.assertEqual([r["dtype"] for r in matrix_rows], ["int32", "int32", "float32"])
        self.assertEqual([r["record_index"] for r in matrix_rows], ["1", "2", "3"])
        self.assertEqual({r["dimensions"] for r in matrix_rows}, {"NX,NY,INPN"})
        self.assertFalse(any(r["filename"].startswith(("diminfo_test-1deg", "inpmat_test-1deg")) for r in rows))
        self.assertTrue(all(not r["sample_availability"] for r in descriptor_rows + matrix_rows))
        self.assertFalse(any("E2O" in r["filename"] for r in rows))
        self.assertFalse(any("repo-mek_1deg" in r["filename"] for r in rows))
        # Validate the layout in a temporary tiny model map; no real ERA5 matrix is claimed.
        with tempfile.TemporaryDirectory(prefix="cmf-era5-matrix-") as temporary:
            fixture = Path(temporary)
            from map_metadata import DimInfo, write_diminfo_nml
            descriptor = fixture / "diminfo_test-runoff.nml"
            write_diminfo_nml(descriptor, DimInfo(
                2, 3, 10, -1, 1, 1.5, -1.5, "inpmat_test-runoff.bin",
                3600, 1801, 1, -180, 180, 90.05, -90.05, "NtoS"))
            binary = fixture / "inpmat_test-runoff.bin"
            binary.write_bytes(bytes(2 * 3 * (4 + 4 + 4)))
            self.assertEqual(read_input_dimensions(descriptor), {"INPNX": 3600, "INPNY": 1801, "INPN": 1})
            self.assertTrue(validate_registered_binary_size(binary, rows, {"NX": 2, "NY": 3, "NLFP": 10}, fixture))

    def test_core_multirecord_and_multilayer_files(self) -> None:
        dims = read_map_dimensions()
        cells = dims["NX"] * dims["NY"]
        expected = {
            "nextxy.bin": 2 * cells * 4,
            "nextxy_noedge.bin": 2 * cells * 4,
            "downxy.bin": 2 * cells * 4,
            "lonlat.bin": 2 * cells * 4,
            "fldhgt.bin": dims["NLFP"] * cells * 4,
        }
        for name, size in expected.items():
            with self.subTest(name=name):
                self.assertEqual((MAP / "binary" / name).stat().st_size, size)

        self.assertEqual(len(struct.unpack(f"<{2*cells}i", (MAP / "binary" / "nextxy.bin").read_bytes())), 2 * cells)
        self.assertEqual(len(struct.unpack(f"<{dims['NLFP']*cells}f", (MAP / "binary" / "fldhgt.bin").read_bytes())), dims["NLFP"] * cells)

    def test_required_base_and_high_resolution_products_are_present(self) -> None:
        required_base = {
            "nextxy.nc", "ctmare.nc", "elevtn.nc", "nxtdst.nc", "rivlen.nc", "fldhgt.nc",
            "basin.nc", "width.nc", "rivwth.nc", "rivhgt.nc", "rivman.nc",
            "inpmat_test-1deg.nc", "diminfo_test-1deg.nml",
        }
        actual_base = {path.name for path in MAP.iterdir() if path.is_file()}
        self.assertTrue(required_base <= actual_base, f"missing base-map products: {sorted(required_base - actual_base)}")

        required_high = {
            "1min.catmxy.nc", "1min.downxy.nc", "1min.elevtn.nc", "1min.uparea.nc",
        }
        actual_high = {path.name for path in (MAP / "1min").glob("1min.*.nc")}
        self.assertTrue(required_high <= actual_high, f"missing high-resolution products: {sorted(required_high - actual_high)}")

    def test_named_river_analysis_sample_products_match_network_and_registry(self) -> None:
        dims = read_map_dimensions()
        cells = dims["NX"] * dims["NY"]
        binary = MAP / "binary"
        nextx = struct.unpack("<" + "i" * cells, (binary / "nextxy.bin").read_bytes()[:cells * 4])
        subbasins = struct.unpack("<" + "i" * cells, (binary / "subbsn-sample.bin").read_bytes())
        colors = struct.unpack("<" + "i" * cells, (binary / "subcol-sample.bin").read_bytes())
        self.assertTrue(all(value == -9999 for value, downstream in zip(subbasins, nextx) if downstream == -9999))
        self.assertTrue(all(value >= 0 for value, downstream in zip(subbasins, nextx) if downstream != -9999))
        self.assertIn(0, subbasins)
        self.assertTrue(any(value > 0 for value in subbasins))
        self.assertTrue(all(value == -9999 or 0 <= value <= 10 for value in colors))

        rows = registry_rows()
        # Concrete variants resolve through standard definitions in s90, not
        # duplicate registry rows; retain the scientific sample checks above.
        for name in ("subbsn", "subcol"):
            self.assertEqual(rows_for_sample_file(binary / f"{name}-sample.bin", rows), [])
            standard = rows_for_sample_file(binary / f"{name}.bin", rows)
            self.assertEqual(len(standard), 1)
            self.assertEqual(standard[0]["name"], name)
            self.assertEqual(standard[0]["dtype"], "int32")
            self.assertEqual(standard[0]["dimensions"], "NX,NY")
            self.assertEqual(standard[0]["missing_value"], "-9999")

    def test_sample_binary_sizes_match_registry_types_and_dimensions(self) -> None:
        dims = read_map_dimensions()
        with (MAP / "1min" / "location.csv").open(newline="", encoding="utf-8") as stream:
            reader = csv.DictReader(stream)
            location = {key.strip(): value.strip() for key, value in next(reader).items()}
        dims["NX_HIRES"] = int(location["nx"])
        dims["NY_HIRES"] = int(location["ny"])

        rows = registry_rows()
        # Analysis examples write user outputs under this ignored directory.
        # Other user-created binaries may be present; only registered products
        # are subject to registry-based type, dimension, and size checks.
        binary_paths = sorted(
            path for path in MAP.rglob("*.bin")
            if "out_analysis" not in path.relative_to(MAP).parts
        )
        self.assertTrue(binary_paths, "no binary map products found")
        validated_count = 0
        for path in binary_paths:
            relative = path.relative_to(MAP)
            with self.subTest(path=str(relative)):
                try:
                    validated = validate_registered_binary_size(path, rows, dims, MAP)
                except AssertionError as error:
                    self.fail(str(error))
                if not validated:
                    continue

                self.assertGreater(path.stat().st_size, 0)
                self.assertLess(path.stat().st_size, 100 * 1024 * 1024)
                validated_count += int(validated)

        self.assertGreater(validated_count, 0, "no registry-listed binaries were validated")

    def test_registered_binary_size_check_allows_user_files_and_rejects_bad_size(self) -> None:
        dims = {"NX": 2, "NY": 1}
        rows = [{"filename": "registered.bin", "product_kind": "binary_map",
                 "dtype": "int32", "dimensions": "NX,NY"}]
        with tempfile.TemporaryDirectory() as temp_dir:
            sample_dir = Path(temp_dir)
            registered = sample_dir / "registered.bin"
            unregistered = sample_dir / "user-added.bin"
            registered.write_bytes(bytes(8))
            unregistered.write_bytes(bytes(3))

            self.assertTrue(validate_registered_binary_size(registered, rows, dims, sample_dir))
            self.assertFalse(validate_registered_binary_size(unregistered, rows, dims, sample_dir))

            # A registered product must still fail when its stored size is incorrect.
            registered.write_bytes(bytes(7))
            with self.assertRaisesRegex(AssertionError, "registry size mismatch"):
                validate_registered_binary_size(registered, rows, dims, sample_dir)

    def test_required_metadata_files_exist(self) -> None:
        for name in ("params.nml", "bifori.csv", "diminfo_test-1deg.nml"):
            with self.subTest(path=name):
                self.assertTrue((MAP / name).is_file())

        with (MAP / "1min" / "location.csv").open(newline="", encoding="utf-8") as stream:
            reader = csv.DictReader(stream)
            locations = [{key.strip(): value.strip() for key, value in row.items()}
                         for row in reader]
        self.assertEqual(len(locations), 1)
        self.assertEqual(locations[0]["nx"], "1200")
        self.assertEqual(locations[0]["ny"], "1800")


if __name__ == "__main__":
    unittest.main(verbosity=2)

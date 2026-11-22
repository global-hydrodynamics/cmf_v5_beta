"""Focused scientific/data-contract tests for the native-GFM workflow."""

import importlib.util
from pathlib import Path
import tempfile
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import sys
import unittest
from unittest.mock import patch
import numpy as np
import rasterio
from rasterio.transform import from_origin
from rasterio.warp import Resampling
from rasterio.windows import Window

PYTHON_DIR = Path(__file__).resolve().parents[1] / "script"
sys.path.insert(0, str(PYTHON_DIR))
import gfm_common as common


def load(name, filename):
    spec = importlib.util.spec_from_file_location(name, PYTHON_DIR / filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


download = load("gfm_download", "s01-download_gfm.py")
convert = load("gfm_convert", "s02-convert_gfm_3sec.py")


class MasksAndMosaic(unittest.TestCase):
    def block(self, shape=(2, 2)):
        x = np.zeros((8, *shape), dtype="uint16")
        x[5:7] = 255
        return x

    def test_reference_only_is_not_observed(self):
        missing = np.full((2, 2), 255, dtype="uint8")
        ref = np.ones((2, 2), dtype="uint8")
        x = self.block()
        common.merge_observation(x, missing, missing, ref, np.zeros_like(ref), 1)
        self.assertFalse(x[2].any())
        self.assertFalse(x[3].any())
        self.assertTrue((x[5] == 1).all())
        self.assertFalse(x[7].any())

    def test_joint_validity_and_quality(self):
        f = np.array([[0, 1], [255, 0]], dtype="uint8")
        w = np.array([[0, 1], [0, 255]], dtype="uint8")
        e = np.array([[0, 1], [0, 0]], dtype="uint8")
        valid, observed = common.code_masks(f, w, np.zeros_like(f), e)
        np.testing.assert_array_equal(valid, [[True, False], [False, False]])
        self.assertTrue(observed.all())

    def test_duplicate_conflict_does_not_double_count(self):
        one = np.ones((2, 2), dtype="uint8")
        zero = np.zeros_like(one)
        x = self.block()
        common.merge_observation(x, one, one, zero, zero, 1)
        stat = common.merge_observation(x, zero, zero, zero, zero, 2)
        self.assertEqual(stat["duplicate_candidates"], 4)
        self.assertEqual(stat["conflicting_flood"], 4)
        self.assertEqual(int(x[2].sum()), 4)
        self.assertEqual(int(x[0].sum()), 4)
        self.assertTrue((x[7] == 1).all())

    def test_later_valid_replaces_earlier_exclusion(self):
        zero = np.zeros((2, 2), dtype="uint8")
        one = np.ones_like(zero)
        x = self.block()
        common.merge_observation(x, zero, zero, zero, one, 1)
        self.assertTrue((x[4] == 1).all())
        self.assertFalse(x[2].any())
        common.merge_observation(x, one, one, zero, zero, 2)
        self.assertTrue((x[2] == 1).all())
        self.assertTrue((x[7] == 2).all())
        self.assertFalse(x[4].any())
        self.assertTrue((x[6] == 0).all())

    def test_unexpected_native_code_rejected(self):
        a = np.array([[2]], dtype="uint8")
        z = np.zeros_like(a)
        with self.assertRaisesRegex(ValueError, "unexpected native codes"):
            common.code_masks(a, z, z, z)

    def test_orbit_and_datatake_identity(self):
        def item(platform, orbit):
            return dict(
                id="test",
                properties={"datetime": "2021-07-15T05:49:37Z"},
                links=[
                    dict(
                        rel="derived_from",
                        href=f"https://example/{platform}_IW_GRDH_1SDV_20210715T054937_20210715T055002_{orbit}_049389",
                    )
                ],
            )

        self.assertEqual(
            common.parse_source(item("S1A", "038784"))["pass_id"],
            "S1A_o038784_dt049389",
        )
        self.assertNotEqual(
            common.parse_source(item("S1A", "038784"))["pass_id"],
            common.parse_source(item("S1B", "027808"))["pass_id"],
        )
        bad = item("S1A", "038784")
        bad["links"] = []
        with self.assertRaises(ValueError):
            common.parse_source(bad)
        bad = item("S1A", "038784")
        bad["properties"]["datetime"] = "2021-07-15T05:49:38Z"
        with self.assertRaises(ValueError):
            common.parse_source(bad)


class FileContracts(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="cmf-gfm-contract-")
        self.root = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def write(self, name, data, transform, crs="EPSG:4326", nodata=None):
        p = self.root / name
        with rasterio.open(
            p,
            "w",
            driver="GTiff",
            count=data.shape[0],
            height=data.shape[1],
            width=data.shape[2],
            dtype=str(data.dtype),
            crs=crs,
            transform=transform,
            nodata=nodata,
        ) as dst:
            dst.write(data)
        return p

    def test_area_support_not_raw_code_average(self):
        step = convert.STEP
        data = np.zeros((8, 4, 4), dtype="uint16")
        data[0, 0, 0] = 1
        data[1, 0, :2] = 1
        data[2, 0, :2] = 1
        source = self.write("binary.tif", data, from_origin(4, 52, step / 2, step / 2))
        result = []
        for band in [1, 2, 3]:
            p = self.root / f"warp{band}.tif"
            convert.warp_band(
                source,
                band,
                p,
                from_origin(4, 52, step, step),
                2,
                2,
                Resampling.average,
            )
            with rasterio.open(p) as src:
                result.append(src.read(1))
        self.assertAlmostEqual(result[0][0, 0], 0.25)
        self.assertAlmostEqual(result[2][0, 0], 0.5)
        self.assertAlmostEqual(result[0][0, 0] / result[2][0, 0], 0.5)
        self.assertAlmostEqual(result[1][0, 0] / result[2][0, 0], 1)
        self.assertEqual(
            result[2][0, 1], 0
        )  # unknown observation, not a valid dry fraction
        fractions = np.divide(
            result[0],
            result[2],
            out=np.full((2, 2), common.NODATA),
            where=result[2] > 0,
        )
        self.assertEqual(fractions[0, 1], common.NODATA)

    def test_source_ids_follow_fractional_support_at_edges(self):
        # Each target pixel has four fine cells: a tiny sliver is still traceable.
        step = convert.STEP
        data = np.zeros((8, 4, 4), dtype="uint16")
        data[2, 0, :2] = 1
        data[7, 0, 0] = 1
        data[7, 0, 1] = 2
        native = self.write(
            "native_owner.tif", data, from_origin(4, 52, step / 2, step / 2)
        )
        out = self.root / "output"
        out.mkdir()
        scratch = self.root / "scratch"
        scratch.mkdir()
        grid = from_origin(4, 52, step, step)
        convert.warp_band(
            native,
            3,
            out / "rhine3sec.valid_fraction.tif",
            grid,
            2,
            2,
            Resampling.average,
        )
        info = convert.source_owners(
            native, [{"index": 1}, {"index": 2}], scratch, out, grid, 2, 2
        )
        with rasterio.open(out / "rhine3sec.source_item_min.tif") as src:
            np.testing.assert_array_equal(src.read(1), [[1, 0], [0, 0]])
        with rasterio.open(out / "rhine3sec.source_item_max.tif") as src:
            np.testing.assert_array_equal(src.read(1), [[2, 0], [0, 0]])
        self.assertLessEqual(info["support_sum_max_abs_error"], 1e-6)

    def test_adjacent_native_tiles_have_no_gap_or_overlap(self):
        left = self.write(
            "left.tif",
            np.zeros((1, 2, 2), dtype="uint8"),
            from_origin(100, 200, 20, 20),
            "EPSG:3857",
        )
        right = self.write(
            "right.tif",
            np.ones((1, 2, 2), dtype="uint8"),
            from_origin(140, 200, 20, 20),
            "EPSG:3857",
        )
        t = from_origin(100, 200, 20, 20)
        x = np.zeros((8, 2, 4), dtype="uint16")
        x[5:7] = 255
        for index, p in enumerate([left, right], 1):
            with rasterio.open(p) as src:
                a = convert.native_window(src, Window(0, 0, 4, 2), t)
            common.merge_observation(
                x,
                a,
                a,
                np.where(a == 255, 255, 0).astype("uint8"),
                np.where(a == 255, 255, 0).astype("uint8"),
                index,
            )
        np.testing.assert_array_equal(x[0], [[0, 0, 1, 1], [0, 0, 1, 1]])
        self.assertTrue((x[2] == 1).all())
        np.testing.assert_array_equal(x[7], [[1, 1, 2, 2], [1, 1, 2, 2]])
        with rasterio.open(left) as src:
            with self.assertRaisesRegex(ValueError, "half-pixel"):
                convert.native_window(
                    src, Window(0, 0, 2, 2), from_origin(110, 200, 20, 20)
                )

    def test_protected_old_symlink_cannot_be_output(self):
        (self.root / "old/source").mkdir(parents=True)
        (self.root / "source").symlink_to("old/source")
        with self.assertRaises(ValueError):
            common.protect_old(self.root / "source/new", self.root)
        self.assertEqual(
            common.protect_old(self.root / "data/new", self.root),
            (self.root / "data/new").resolve(),
        )

    def test_existing_download_reused_without_network(self):
        p = self.root / "cached.tif"
        p.write_bytes(b"cached-bytes")
        asset = dict(
            path=p.name,
            expected_bytes=p.stat().st_size,
            sha256=common.sha256(p),
            url="https://invalid.example/no-network",
        )
        with patch.object(
            download.requests, "get", side_effect=AssertionError("Network was used")
        ):
            result = download.download_asset(asset, self.root, True)
        self.assertTrue(result["reused"])
        self.assertEqual(result["transferred_bytes"], 0)
        asset["sha256"] = "bad"
        with self.assertRaises(ValueError):
            download.download_asset(asset, self.root, True)
        self.assertEqual(p.read_bytes(), b"cached-bytes")

    def test_partial_download_resumes_exact_original_bytes(self):
        source = self.write(
            "source.tif",
            np.ones((1, 8, 8), dtype="uint8"),
            from_origin(0, 1, 0.01, 0.01),
            nodata=255,
        )
        blob = source.read_bytes()
        calls = []

        class Handler(BaseHTTPRequestHandler):
            def do_GET(self):
                offset = int(
                    self.headers.get("Range", "bytes=0-").split("=")[1].split("-")[0]
                )
                calls.append(offset)
                self.send_response(206 if offset else 200)
                self.send_header("Content-Length", str(len(blob) - offset))
                if offset:
                    self.send_header(
                        "Content-Range", f"bytes {offset}-{len(blob) - 1}/{len(blob)}"
                    )
                self.end_headers()
                self.wfile.write(blob[offset:])

            def log_message(self, *args):
                pass

        server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            half = len(blob) // 2
            (self.root / "download.tif.part").write_bytes(blob[:half])
            a = dict(
                path="download.tif",
                expected_bytes=len(blob),
                url=f"http://127.0.0.1:{server.server_port}/source.tif",
            )
            result = download.download_asset(a, self.root, False)
            self.assertEqual(calls, [half])
            self.assertEqual(result["transferred_bytes"], len(blob) - half)
            self.assertEqual((self.root / "download.tif").read_bytes(), blob)
        finally:
            server.shutdown()
            server.server_close()
            thread.join()

    def test_actual_cama_one_minute_centres_subdivide_twenty(self):
        m = SCRIPTS.parents[2] / "map/glb_15min"
        if not (m / "1min_nc/location.txt").exists():
            self.skipTest("actual global one-minute map not installed")
        t, w, h, meta = convert.cama_grid(m, common.DEFAULT_BBOX)
        self.assertEqual((w, h), (4800, 3600))
        self.assertTrue(meta["netcdf_centres_verified"])
        self.assertEqual(meta["coarse_window"], [11040, 11280, 2280, 2460])
        self.assertAlmostEqual(t.c, 4)
        self.assertAlmostEqual(t.f, 52)
        self.assertAlmostEqual(t.c + w * t.a, 8)
        self.assertAlmostEqual(t.f + h * t.e, 49)


if __name__ == "__main__":
    unittest.main(verbosity=2)

#!/usr/bin/env python3
"""Read local 3-second products, verify scientific contracts and compare replays."""

from __future__ import annotations
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import sys
import time
import numpy as np
import rasterio

sys.path.insert(0, str(Path(__file__).resolve().parent))
from gfm_common import NODATA, protect_old, run_metrics, save_json
import importlib.util

spec = importlib.util.spec_from_file_location(
    "gfm_converter", Path(__file__).with_name("s02-convert_gfm_3sec.py")
)
converter = importlib.util.module_from_spec(spec)
spec.loader.exec_module(converter)


def validate(args):
    start = time.monotonic()
    out = args.output.resolve()
    metadata = json.loads((out / "provenance.json").read_text())
    grid, width, height, alignment = converter.cama_grid(
        args.cama_map, metadata["bbox"]
    )
    paths = sorted(out.glob("rhine3sec.*.tif"))
    expected = {
        "flood_fraction",
        "water_fraction",
        "valid_fraction",
        "observed_fraction",
        "excluded_fraction",
        "reference_water",
        "exclusion_mask",
        "source_item_min",
        "source_item_max",
        "flooded_support",
        "water_support",
        "valid_support",
        "cell_area",
    }
    assert {p.name[10:-4] for p in paths} == expected
    # Reuse CaMa's actual location reader, not a second interpretation of its schema.
    sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "map/tools/code"))
    from convert_highres_binary_to_netcdf import read_location

    loc = read_location(out / "location.txt")
    assert len(loc) == 1 and loc[0]["nx"] == width and loc[0]["ny"] == height
    assert np.isclose(loc[0]["resolution"], 1 / 1200, rtol=0, atol=1e-18)
    from contextlib import ExitStack

    counts = Counter()
    hashes = {n: hashlib.sha256() for n in expected}
    comparisons = {}
    with ExitStack() as stack:
        readers = {p.name[10:-4]: stack.enter_context(rasterio.open(p)) for p in paths}
        replay = (
            {
                n: stack.enter_context(
                    rasterio.open(args.compare_output / (f"rhine3sec.{n}.tif"))
                )
                for n in expected
            }
            if args.compare_output
            else {}
        )
        for n, r in readers.items():
            assert r.crs.to_epsg() == 4326 and r.shape == (height, width)
            assert np.allclose(tuple(r.transform), tuple(grid), rtol=0, atol=1e-12)
            assert r.transform.a > 0 and r.transform.e < 0
        valid_bbox = None
        flood_bbox = None
        for win in converter.windows(width, height, 256):
            a = {n: r.read(1, window=win) for n, r in readers.items()}
            for n, v in a.items():
                hashes[n].update(v.tobytes())
                if replay:
                    b = replay[n].read(1, window=win)
                    assert np.array_equal(v, b), f"Replay differs: {n}, {win}"
            vf, ff, wf = a["valid_fraction"], a["flood_fraction"], a["water_fraction"]
            good = vf > 0
            assert np.array_equal(ff != NODATA, good) and np.array_equal(
                wf != NODATA, good
            )
            for n in ["valid_fraction", "observed_fraction", "excluded_fraction"]:
                assert np.all((a[n] >= 0) & (a[n] <= 1 + 8 * np.finfo("float32").eps))
            assert np.all(
                (ff[good] >= 0) & (ff[good] <= 1 + 8 * np.finfo("float32").eps)
            )
            assert np.all(
                (wf[good] >= 0) & (wf[good] <= 1 + 8 * np.finfo("float32").eps)
            )
            assert np.all(vf + a["excluded_fraction"] <= a["observed_fraction"] + 1e-6)
            tol = 16 * np.finfo("float32").eps * float(a["cell_area"].max())
            assert np.max(np.abs(a["valid_support"] - vf * a["cell_area"])) <= tol
            assert np.all(a["flooded_support"] <= a["valid_support"] + tol)
            assert np.all(a["water_support"] <= a["valid_support"] + tol)
            assert (
                np.max(
                    np.abs(
                        ff[good] * a["valid_support"][good] - a["flooded_support"][good]
                    ),
                    initial=0,
                )
                <= tol
            )
            assert np.all(np.isin(a["reference_water"], [0, 1, 2, 255]))
            assert np.all(np.isin(a["exclusion_mask"], [0, 1, 255]))
            lo, hi = a["source_item_min"], a["source_item_max"]
            assert np.all(lo[good] >= 1) and np.all(
                hi[good] <= len(metadata["source_items"])
            )
            assert np.all(lo[good] <= hi[good])
            counts["cells"] += ff.size
            counts["valid_cells"] += int(good.sum())
            counts["missing_cells"] += int((~good).sum())
            positive = good & (ff > 0)
            counts["positive_flood_cells"] += int(positive.sum())
            assert not np.any((~good) & ((lo > 0) | (hi > 0)))
            counts["source_owner_nonzero_without_valid"] += int(
                np.count_nonzero((~good) & ((lo > 0) | (hi > 0)))
            )
            for mask, name in [(good, "valid"), (positive, "flood")]:
                rr, cc = np.where(mask)
                if rr.size:
                    box = [
                        int(cc.min() + win.col_off),
                        int(rr.min() + win.row_off),
                        int(cc.max() + win.col_off),
                        int(rr.max() + win.row_off),
                    ]
                    old = valid_bbox if name == "valid" else flood_bbox
                    value = (
                        box
                        if old is None
                        else [
                            min(old[0], box[0]),
                            min(old[1], box[1]),
                            max(old[2], box[2]),
                            max(old[3], box[3]),
                        ]
                    )
                    if name == "valid":
                        valid_bbox = value
                    else:
                        flood_bbox = value
        native = metadata["native_statistics"]
        assert (
            native["valid_candidates"]
            == native["unique_valid_native_pixels"] + native["duplicate_candidates"]
        )
        for name, r in replay.items():
            assert r.shape == (height, width) and r.crs.to_epsg() == 4326
            comparisons[name] = "bitwise identical decoded arrays"

    def geo(box):
        if box is None:
            return None
        x0, y0, x1, y1 = box
        return [
            grid.c + (x0 + 0.5) * grid.a,
            grid.f + (y1 + 0.5) * grid.e,
            grid.c + (x1 + 0.5) * grid.a,
            grid.f + (y0 + 0.5) * grid.e,
        ]

    result = run_metrics(
        start,
        pass_id=metadata["pass_metadata"]["pass_id"],
        result="PASS",
        counts=dict(counts),
        valid_percent=100 * counts["valid_cells"] / counts["cells"],
        valid_pixel_centre_bbox=geo(valid_bbox),
        flood_pixel_centre_bbox=geo(flood_bbox),
        alignment=alignment,
        native_overlap=native,
        decoded_sha256={n: h.hexdigest() for n, h in hashes.items()},
        replay=comparisons,
        output_files=len(paths),
    )
    path = protect_old(args.report, args.work_dir)
    save_json(path, result)
    print(json.dumps(result, indent=2))


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--compare-output", type=Path)
    p.add_argument("--report", type=Path, required=True)
    p.add_argument("--work-dir", type=Path, default=Path.home() / "work/Atlantis")
    p.add_argument(
        "--cama-map",
        type=Path,
        default=Path(__file__).resolve().parents[3] / "map/glb_15min",
    )
    validate(p.parse_args())


if __name__ == "__main__":
    main()

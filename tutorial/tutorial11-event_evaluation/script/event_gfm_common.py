"""Shared contracts for the Tutorial 11 native-GFM acquisition and 3-second tile."""

from __future__ import annotations
import hashlib
import json
import os
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

LAYERS = (
    "ensemble_flood_extent",
    "ensemble_water_extent",
    "reference_water_mask",
    "exclusion_mask",
)
DEFAULT_BBOX = (4.0, 49.0, 8.0, 52.0)
DEFAULT_DATE = "2021-07-15"
NODATA = -9999.0
SOURCE_PATTERN = re.compile(
    r"^(S1[ABCD])_IW_GRD\w_1\w{3}_(\d{8}T\d{6})_(\d{8}T\d{6})_(\d{6})_([0-9A-F]{6})(?:_|$)"
)


def sha256(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def save_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n")
    os.replace(temporary, path)


def protect_old(path, work):
    path, old = Path(path).resolve(), (Path(work) / "old").resolve()
    if path == old or path.is_relative_to(old):
        raise ValueError(f"Output points inside protected old/: {path}")
    return path


def parse_source(item):
    """Use the Sentinel-1 orbit/datatake identity, never a time-cluster guess."""
    links = [x["href"] for x in item.get("links", []) if x.get("rel") == "derived_from"]
    names = [x.rstrip("/").split("/")[-1] for x in links]
    matches = [(n, SOURCE_PATTERN.match(n)) for n in names]
    matches = [(n, m) for n, m in matches if m]
    if len(matches) != 1:
        raise ValueError(
            f"{item['id']}: one verifiable Sentinel-1 source identifier required"
        )
    name, m = matches[0]
    platform, start, end, orbit, datatake = m.groups()
    stamp = datetime.fromisoformat(
        item["properties"]["datetime"].replace("Z", "+00:00")
    )
    source_start = datetime.strptime(start, "%Y%m%dT%H%M%S").replace(
        tzinfo=timezone.utc
    )
    if stamp != source_start:
        raise ValueError(
            f"{item['id']}: GFM datetime and Sentinel-1 source start disagree"
        )
    return dict(
        source_id=name,
        source_href=links[names.index(name)],
        platform=platform,
        absolute_orbit=int(orbit),
        datatake=datatake,
        pass_id=f"{platform}_o{orbit}_dt{datatake}",
        start_utc=source_start.isoformat(),
        end_utc=datetime.strptime(end, "%Y%m%dT%H%M%S")
        .replace(tzinfo=timezone.utc)
        .isoformat(),
    )


def run_metrics(start, **extra):
    try:
        import resource

        rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        rss = int(rss if sys.platform == "darwin" else rss * 1024)
    except (ImportError, AttributeError):
        rss = None
    return dict(
        finished_utc=utc_now(),
        wall_seconds=time.monotonic() - start,
        peak_process_rss_bytes=rss,
        **extra,
    )


def code_masks(flood, water, reference, exclusion):
    """Conservative joint validity; reference-only pixels are never observations."""
    import numpy as np

    for name, array, allowed in [
        ("flood", flood, [0, 1, 255]),
        ("water", water, [0, 1, 255]),
        ("reference", reference, [0, 1, 2, 255]),
        ("exclusion", exclusion, [0, 1, 255]),
    ]:
        bad = ~np.isin(array, allowed)
        if np.any(bad):
            raise ValueError(
                f"{name}: unexpected native codes {np.unique(array[bad]).tolist()}"
            )
    f_known, w_known = flood != 255, water != 255
    observed = f_known | w_known
    valid = f_known & w_known & (exclusion == 0)
    return valid, observed


def merge_observation(mosaic, flood, water, reference, exclusion, index):
    """Update one block once per native cell: earliest valid Item wins.

    Bands (zero-based): flooded, water, valid, observed, excluded, reference,
    exclusion, valid-source-owner. Categories 255 are unknown; owner 0 is none.
    """
    import numpy as np

    valid, observed = code_masks(flood, water, reference, exclusion)
    duplicate = valid & (mosaic[7] != 0)
    take = valid & (mosaic[7] == 0)
    stats = dict(
        valid_candidates=int(valid.sum()),
        duplicate_candidates=int(duplicate.sum()),
        conflicting_flood=int(
            np.count_nonzero(duplicate & (mosaic[0] != (flood == 1)))
        ),
        conflicting_water=int(
            np.count_nonzero(duplicate & (mosaic[1] != (water == 1)))
        ),
    )
    mosaic[0][take] = flood[take] == 1
    mosaic[1][take] = water[take] == 1
    mosaic[2][take] = 1
    mosaic[7][take] = index
    mosaic[3][observed] = 1
    mosaic[4][take] = 0
    mosaic[4][observed & (exclusion == 1) & (mosaic[7] == 0)] = 1
    ref_take = (reference != 255) & (mosaic[5] == 255)
    mosaic[5][ref_take] = reference[ref_take]
    quality_take = observed & ((mosaic[6] == 255) | take)
    mosaic[6][quality_take] = exclusion[quality_take]
    return stats

"""Native catmxy selection; computational cells and unit catchments differ.

A unit catchment is the stored set of fine pixels assigned to a river cell,
not its coarse geographic rectangle or a newly delineated watershed. catmxy
supplies assignments; nextxy only supplies downstream connectivity. Missing
pairs have no inferred assignment. Sampled display pixels never define selection.
"""

from __future__ import annotations

from collections import OrderedDict
from dataclasses import dataclass

import numpy as np

from hires import assignment


@dataclass(frozen=True)
class CatchmentBoundary:
    segments: np.ndarray
    pixel_count: int
    # Native row/column bounds, exclusive stops. Never a geographic cell box.
    bounds: tuple[int, int, int, int]


@dataclass(frozen=True)
class SelectionState:
    kind: str = "none"
    clicked: tuple[float, float] | None = None
    tile_key: str | None = None
    native_pixel: tuple[int, int] | None = None
    river_cell: tuple[int, int] | None = None
    boundary: CatchmentBoundary | None = None
    status: str = "No selection"
    # Regular computational-cell geometry, distinct from native catchment edges.
    coarse_outline: np.ndarray | None = None


def coarse_cell_outline(geometry, row, col):
    """Four exact params.txt cell edges; inputs are Python zero-based indices."""
    west = geometry.west + col * geometry.resolution
    east = west + geometry.resolution
    north = geometry.north - row * geometry.resolution
    south = north - geometry.resolution
    result = np.array(
        [
            [[west, north], [east, north]],
            [[east, north], [east, south]],
            [[east, south], [west, south]],
            [[west, south], [west, north]],
        ]
    )
    result.flags.writeable = False
    return result


def merge_edges(edges):
    """Merge collinear integer-grid runs, preserving every hole/component."""
    if not len(edges):
        return np.empty((0, 3), dtype=np.int64)
    a = np.asarray(edges, dtype=np.int64).reshape(-1, 3)
    a = a[np.lexsort((a[:, 1], a[:, 0]))]
    # Each edge is (constant coordinate, run start, run end). Only truly
    # contiguous edges merge; gaps must never become artificial connectors.
    new = np.r_[True, (a[1:, 0] != a[:-1, 0]) | (a[1:, 1] != a[:-1, 2])]
    starts = np.flatnonzero(new)
    stops = np.r_[starts[1:] - 1, len(a) - 1]
    return np.column_stack((a[starts, 0], a[starts, 1], a[stops, 2]))


class CatchmentIndex:
    """Lazy sparse block index plus a bounded cache of complete native outlines.

    The first valid selection scans one tile, in bounded chunks. Later clicks
    read only that assignment's bounding box, not the entire global raster.
    Index/counts and exposed edges reflect catmx AND catmy, never nextxy.
    """

    def __init__(self, tile, coarse, cache_size=24, block_pixels=500000):
        self.tile, self.coarse = tile, coarse
        self.cache_size, self.block_pixels = cache_size, block_pixels
        self._index = None
        self._boundaries = OrderedDict()

    def _build_index(self):
        g = self.tile.geometry
        data = self.tile.mmap("catmxy")
        index = {}
        step = max(1, self.block_pixels // g.nx)
        for start in range(0, g.ny, step):
            x, y = data[:, start : min(g.ny, start + step), :]
            valid, _, _ = assignment(x, y, self.coarse)
            rows, cols = np.where(valid)
            labels = (y[valid].astype("i8") - 1) * self.coarse.nx + x[valid].astype("i8") - 1
            unique, inverse, counts = np.unique(labels, return_inverse=True, return_counts=True)
            if not len(unique):
                continue
            rmin = np.full(len(unique), g.ny, dtype="i8")
            rmax = np.full(len(unique), -1, dtype="i8")
            cmin = np.full(len(unique), g.nx, dtype="i8")
            cmax = np.full(len(unique), -1, dtype="i8")
            np.minimum.at(rmin, inverse, rows + start)
            np.maximum.at(rmax, inverse, rows + start)
            np.minimum.at(cmin, inverse, cols)
            np.maximum.at(cmax, inverse, cols)
            for label, r0, r1, c0, c1, count in zip(unique, rmin, rmax, cmin, cmax, counts):
                previous = index.get(int(label))
                value = (int(r0), int(r1) + 1, int(c0), int(c1) + 1, int(count))
                if previous is not None:
                    value = (
                        min(previous[0], value[0]),
                        max(previous[1], value[1]),
                        min(previous[2], value[2]),
                        max(previous[3], value[3]),
                        previous[4] + value[4],
                    )
                index[int(label)] = value
        self._index = index

    def boundary(self, row, col):
        if not (0 <= row < self.coarse.ny and 0 <= col < self.coarse.nx):
            raise ValueError("Selected assignment is outside coarse dimensions")
        label = row * self.coarse.nx + col
        if label in self._boundaries:
            self._boundaries.move_to_end(label)
            return self._boundaries[label]
        if self._index is None:
            self._build_index()
        if label not in self._index:
            raise ValueError("No native pixels have this assignment in the selected tile")
        r0, r1, c0, c1, count = self._index[label]
        g = self.tile.geometry
        data = self.tile.mmap("catmxy")
        horizontal, vertical = [], []
        step = max(1, self.block_pixels // max(1, c1 - c0))
        for start in range(r0, r1, step):
            stop = min(r1, start + step)
            # Include actual neighbors beyond the selected bounding box and
            # block boundaries. Only true tile borders have no neighbor.
            rr0, rr1 = max(0, start - 1), min(g.ny, stop + 1)
            cc0, cc1 = max(0, c0 - 1), min(g.nx, c1 + 1)
            a, b = data[:, rr0:rr1, cc0:cc1]
            mask = (a == col + 1) & (b == row + 1)
            padded = np.pad(mask, ((rr0 - (start - 1), (stop + 1) - rr1), (cc0 - (c0 - 1), (c1 + 1) - cc1)))
            center = padded[1:-1, 1:-1]
            for exposure, offset in [(center & ~padded[:-2, 1:-1], 0), (center & ~padded[2:, 1:-1], 1)]:
                r, c = np.where(exposure)
                horizontal.append(merge_edges(np.column_stack((r + start + offset, c + c0, c + c0 + 1))))
            for exposure, offset in [(center & ~padded[1:-1, :-2], 0), (center & ~padded[1:-1, 2:], 1)]:
                r, c = np.where(exposure)
                vertical.append(merge_edges(np.column_stack((c + c0 + offset, r + start, r + start + 1))))
        h, v = merge_edges(np.concatenate(horizontal)), merge_edges(np.concatenate(vertical))
        horizontal_segments = np.stack(
            (
                np.column_stack((g.west + h[:, 1] * g.resolution, g.north - h[:, 0] * g.resolution)),
                np.column_stack((g.west + h[:, 2] * g.resolution, g.north - h[:, 0] * g.resolution)),
            ),
            axis=1,
        )
        vertical_segments = np.stack(
            (
                np.column_stack((g.west + v[:, 0] * g.resolution, g.north - v[:, 1] * g.resolution)),
                np.column_stack((g.west + v[:, 0] * g.resolution, g.north - v[:, 2] * g.resolution)),
            ),
            axis=1,
        )
        segments = np.concatenate((horizontal_segments, vertical_segments))
        segments.flags.writeable = False
        result = CatchmentBoundary(segments, count, (r0, r1, c0, c1))
        self._boundaries[label] = result
        while len(self._boundaries) > self.cache_size:
            self._boundaries.popitem(last=False)
        return result

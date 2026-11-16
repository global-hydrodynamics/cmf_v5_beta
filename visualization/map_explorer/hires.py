"""Read native high-resolution tiles and scientific display quantities read-only."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import tempfile

import numpy as np

from map_reader import Geometry


def neighbor_difference(values):
    """Maximum valid eight-neighbor absolute elevation difference [m], NOT slope."""
    a = np.ma.asarray(values).astype(float).filled(np.nan)
    a[a == -9999] = np.nan
    result = np.full(a.shape, np.nan)
    ny, nx = a.shape
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            if not (dy or dx):
                continue
            src = (slice(max(0, dy), min(ny, ny + dy)), slice(max(0, dx), min(nx, nx + dx)))
            dst = (slice(max(0, -dy), min(ny, ny - dy)), slice(max(0, -dx), min(nx, nx - dx)))
            delta = np.abs(a[src] - a[dst])
            result[src] = np.fmax(result[src], delta)
    return np.ma.masked_invalid(result)


def assignment(x, y, geometry):
    valid_x = (x >= 1) & (x <= geometry.nx)
    valid_y = (y >= 1) & (y <= geometry.ny)
    valid = valid_x & valid_y
    land = (x == -999) & (y == -999)
    invalid = (valid_x != valid_y) | ((x == -999) != (y == -999))
    invalid |= ((x > 0) | (y > 0)) & ~valid
    return valid, land, invalid


@dataclass
class Tile:
    key: str
    directory: Path
    prefix: str
    geometry: Geometry
    files: dict = field(default_factory=dict)
    _maps: dict = field(default_factory=dict, repr=False)
    _stats: dict = field(default_factory=dict, repr=False)
    _centroids: object = field(default=None, repr=False)

    def mmap(self, name):
        if name not in self.files:
            raise ValueError(f"{self.key}: missing {name}")
        if name not in self._maps:
            dtype, records = ("<i2", 2) if name == "catmxy" else ("i1", 1) if name == "visual" else ("<f4", 1)
            g = self.geometry
            self._maps[name] = np.memmap(self.files[name], dtype=dtype, mode="r", shape=(records, g.ny, g.nx))
        return self._maps[name]

    def sample(self, name, rows, cols):
        if name == "difference":
            # Read eight actual native neighbors of sampled pixels, never the
            # neighbors in a downsampled image. This preserves the definition.
            base = self.sample("elevtn", rows, cols)
            result = np.full(base.shape, np.nan)
            g = self.geometry
            for dy in (-1, 0, 1):
                for dx in (-1, 0, 1):
                    if not (dy or dx):
                        continue
                    rr, cc = rows + dy, cols + dx
                    valid = (rr[:, None] >= 0) & (rr[:, None] < g.ny) & (cc[None, :] >= 0) & (cc[None, :] < g.nx)
                    neighbor = self.sample("elevtn", np.clip(rr, 0, g.ny - 1), np.clip(cc, 0, g.nx - 1))
                    delta = np.abs(base - neighbor)
                    result = np.fmax(result, np.where(valid, delta, np.nan))
            return result
        data = self.mmap(name)
        result = np.array(data[:, rows[:, None], cols[None, :]])
        if name in ("elevtn", "flddif"):
            a = result[0].astype(float)
            a[(a == -9999) | ~np.isfinite(a)] = np.nan
            return a
        return result if name == "catmxy" else result[0]

    def subset(self, extent, max_side=1200):
        g = self.geometry
        w, e, s, n = extent
        c0, c1 = max(0, int(np.floor((w - g.west) / g.resolution))), min(
            g.nx, int(np.ceil((e - g.west) / g.resolution))
        )
        r0, r1 = max(0, int(np.floor((g.north - n) / g.resolution))), min(
            g.ny, int(np.ceil((g.north - s) / g.resolution))
        )
        if r1 <= r0 or c1 <= c0:
            return None

        def centers(start, stop):
            count = min(stop - start, max_side)
            return start + ((np.arange(count) + 0.5) * (stop - start) / count).astype(int)

        return (
            centers(r0, r1),
            centers(c0, c1),
            (
                g.west + c0 * g.resolution,
                g.west + c1 * g.resolution,
                g.north - r1 * g.resolution,
                g.north - r0 * g.resolution,
            ),
            (r1 - r0 <= max_side and c1 - c0 <= max_side),
        )

    def percentiles(self, name):
        """Exact full-tile P2/P98, bounded RAM and disposable disk workspace."""
        if name not in self._stats:
            g = self.geometry
            block = max(1, 500000 // g.nx)
            with tempfile.TemporaryFile() as stream:
                stream.truncate(g.nx * g.ny * 8)
                work = np.memmap(stream, dtype="f8", mode="r+", shape=(g.nx * g.ny,))
                count = 0
                for start in range(0, g.ny, block):
                    values = self.sample(name, np.arange(start, min(g.ny, start + block)), np.arange(g.nx))
                    finite = values[np.isfinite(values)]
                    work[count : count + finite.size] = finite
                    count += finite.size
                if not count:
                    raise ValueError(f"{self.key}: no valid {name} values")
                low, high = np.percentile(work[:count], (2, 98), overwrite_input=True)
                del work
            self._stats[name] = float(low), float(high if high > low else low + 1)
        return self._stats[name]

    def centroids(self, coarse, river):
        """Native pixel-center mean per assigned coarse cell, over the full tile."""
        if self._centroids is None:
            g = self.geometry
            size = coarse.nx * coarse.ny
            counts, sx, sy = np.zeros(size), np.zeros(size), np.zeros(size)
            for start in range(0, g.ny, max(1, 500000 // g.nx)):
                rows = np.arange(start, min(g.ny, start + max(1, 500000 // g.nx)))
                x, y = self.sample("catmxy", rows, np.arange(g.nx))
                valid, _, _ = assignment(x, y, coarse)
                rr, cc = np.where(valid)
                labels = (y[valid].astype("i8") - 1) * coarse.nx + x[valid].astype("i8") - 1
                keep = river.ravel()[labels]
                labels, rr, cc = labels[keep], rr[keep], cc[keep]
                counts += np.bincount(labels, minlength=size)
                sx += np.bincount(labels, weights=g.west + (cc + 0.5) * g.resolution, minlength=size)
                sy += np.bincount(labels, weights=g.north - (rows[rr] + 0.5) * g.resolution, minlength=size)
            lon = np.divide(sx, counts, out=np.full(size, np.nan), where=counts > 0)
            lat = np.divide(sy, counts, out=np.full(size, np.nan), where=counts > 0)
            self._centroids = lon, lat, counts
        return self._centroids


def discover_tiles(map_dir, messages):
    """Discover named records in map-local location.txt files; no 1min constant."""
    root = Path(map_dir)
    tiles = {}
    for location in sorted(root.rglob("location.txt")):
        try:
            lines = location.read_text().splitlines()
            count = int(lines[0].split()[0])
            records = [line.split() for line in lines[2:] if line.strip()]
            if len(records) != count:
                raise ValueError("area count disagrees with location records")
            for fields in records:
                _, name, w, e, s, n, nx, ny, step = fields[:9]
                nx, ny, step = int(nx), int(ny), float(step)
                w, e, s, n = map(float, (w, e, s, n))
                if (
                    nx <= 0
                    or ny <= 0
                    or not np.isfinite([w, e, s, n, step]).all()
                    or step <= 0
                    or w >= e
                    or s >= n
                    or s < -90
                    or n > 90
                    or not np.isclose(e - w, nx * step, rtol=0, atol=1e-5)
                    or not np.isclose(n - s, ny * step, rtol=0, atol=1e-5)
                ):
                    raise ValueError("inconsistent high-resolution geometry")
                # Prefix is a filename, never a relative escape from MAP_DIR.
                if Path(name).name != name or name in (".", ".."):
                    raise ValueError("invalid area filename prefix")
                g = Geometry(nx, ny, 1, step, w, e, s, n)
                key = str((location.parent / name).relative_to(root))
                tile = Tile(key, location.parent, name, g)
                for field_name, bytes_per_pixel in [("catmxy", 4), ("visual", 1), ("elevtn", 4), ("flddif", 4)]:
                    path = location.parent / f"{name}.{field_name}.bin"
                    if path.is_file():
                        if path.stat().st_size == nx * ny * bytes_per_pixel:
                            tile.files[field_name] = path
                        else:
                            messages.append(f"{path.name}: wrong declared Binary size; skipped")
                if tile.files:
                    tiles[key] = tile
        except (OSError, ValueError, IndexError) as exc:
            messages.append(f"{location}: unsupported tile metadata: {exc}")
    return tiles


def catchment_edges(x, y, valid, edges):
    """True native assignment-pair boundaries, not contours of inherited values."""
    w, e, s, n = edges
    ny, nx = x.shape
    xx, yy = np.linspace(w, e, nx + 1), np.linspace(n, s, ny + 1)
    changed = valid[:, :-1] & valid[:, 1:] & ((x[:, :-1] != x[:, 1:]) | (y[:, :-1] != y[:, 1:]))
    r, c = np.where(changed)
    vertical = np.stack([np.column_stack([xx[c + 1], yy[r]]), np.column_stack([xx[c + 1], yy[r + 1]])], axis=1)
    changed = valid[:-1] & valid[1:] & ((x[:-1] != x[1:]) | (y[:-1] != y[1:]))
    r, c = np.where(changed)
    horizontal = np.stack([np.column_stack([xx[c], yy[r + 1]]), np.column_stack([xx[c + 1], yy[r + 1]])], axis=1)
    return np.concatenate([vertical, horizontal])

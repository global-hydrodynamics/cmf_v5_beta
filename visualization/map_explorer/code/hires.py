"""Read native high-resolution tiles and scientific display quantities read-only."""

from __future__ import annotations

from dataclasses import dataclass, field
import csv
from pathlib import Path
import tempfile
import hashlib
import json
import os

import numpy as np

from map_reader import Geometry
from hires_netcdf import NetCDFSource
from hires_cog import COGSource, RasterCache, sampling, signature


EXACT_STATS_MAX_PIXELS = 50_000_000
SPARSE_STATS_STRATA = 12
SPARSE_STATS_PATCH = 16


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
    coarse_geometry: object = field(default=None, repr=False)
    netcdf: dict = field(default_factory=dict, repr=False)
    cog: dict = field(default_factory=dict, repr=False)

    @property
    def storage(self):
        if self.cog:
            return "COG" if len(self.cog) == len(self.files) else "COG + explicit optional fallback"
        count = sum(path.suffix == ".nc" for path in self.files.values())
        return "NetCDF" if count == len(self.files) and count else "NetCDF + Binary optional fields" if count else "Binary"

    def mmap(self, name):
        if name in self.files and self.files[name].suffix in (".nc", ".tif"):
            raise ValueError("NetCDF/COG sources use native block sampling, not a full-array mmap")
        if name not in self.files:
            raise ValueError(f"{self.key}: missing {name}")
        if name not in self._maps:
            dtype, records = (
                ("<i2", 2) if name == "catmxy" else ("i1", 1) if name in ("visual", "catmz100") else ("<f4", 1)
            )
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
        rows, cols = np.asarray(rows, dtype=int), np.asarray(cols, dtype=int)
        if name in self.cog:
            result = self.cog[name].read(rows, cols)
        elif name in self.files and self.files[name].suffix == ".nc":
            if name not in self.netcdf:
                self.netcdf[name] = NetCDFSource.open(self.files[name], name, self.geometry)
            result = self.netcdf[name].read(rows, cols)
        else:
            data = self.mmap(name)
            result = np.array(data[:, rows[:, None], cols[None, :]])
        if name in ("elevtn", "flddif", "uparea", "rivwth"):
            a = result[0].astype(float)
            a[(a == -9999) | ~np.isfinite(a)] = np.nan
            return a
        return result if name == "catmxy" else result[0]

    def display_plan(self, name, extent, screen):
        source = self.cog.get("elevtn" if name == "difference" else name)
        return sampling(self.geometry, extent, screen, source.overviews) if source else None

    def display(self, name, plan):
        value = self.cog[name].display(plan)
        return value if name == "catmxy" else value[0]

    @property
    def source_identity(self):
        return tuple((name, source.identity) for name, source in sorted(self.cog.items()))

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

    @property
    def sparse_statistics(self):
        return self.geometry.nx * self.geometry.ny > EXACT_STATS_MAX_PIXELS

    def _sparse_percentiles(self, name, coarse, quantiles, inherited, positive):
        """Approximate display limits from fixed native patches across the whole tile.

        Equal raster strata approximate pixel-frequency weighting (not physical area).
        At most12x12 patches of16x16 pixels are read; ocean/missing/invalid paired
        assignments are excluded. Neither viewport nor COG overviews define samples.
        """
        g = self.geometry
        row_edges = np.linspace(0, g.ny, min(SPARSE_STATS_STRATA, g.ny) + 1, dtype=int)
        col_edges = np.linspace(0, g.nx, min(SPARSE_STATS_STRATA, g.nx) + 1, dtype=int)
        samples = []
        assigned_count = 0
        for r0, r1 in zip(row_edges[:-1], row_edges[1:]):
            height = min(SPARSE_STATS_PATCH, r1 - r0)
            start_row = r0 + (r1 - r0 - height) // 2
            rows = np.arange(start_row, start_row + height)
            for c0, c1 in zip(col_edges[:-1], col_edges[1:]):
                width = min(SPARSE_STATS_PATCH, c1 - c0)
                start_col = c0 + (c1 - c0 - width) // 2
                cols = np.arange(start_col, start_col + width)
                x, y = self.sample('catmxy', rows, cols)
                valid, _, _ = assignment(x, y, coarse)
                assigned_count += int(valid.sum())
                if not valid.any():
                    continue
                values = (self.sample(name, rows, cols)[valid] if inherited is None
                          else inherited[y[valid] - 1, x[valid] - 1])
                samples.append(values[np.isfinite(values) & ((values > 0) if positive else True)])
        if not assigned_count:
            raise ValueError(f'{self.key}: sparse sample has no valid native assignments; use Manual limits')
        values = np.concatenate(samples)
        return tuple(map(float, np.percentile(values, quantiles))) if values.size else (np.nan, np.nan)

    def percentiles(self, name, positive=False, allow_empty=False, coarse=None, *, quantiles=(5, 95), inherited=None):
        """Assigned-pixel display percentiles: exact on small tiles, sparse on large tiles.

        Inherited fields repeat coarse values for each valid native assignment
        in the reference population (or sparse sample), not once per coarse cell. The positive flag remains
        for helper compatibility; no Auto path uses it. Auto includes all valid
        finite values in its P5/P95 population before the nonpositive Log fallback.
        """
        if self.cog and "catmxy" not in self.cog:
            raise ValueError("Exact COG statistics require compatible native catmxy COG; use Manual limits or explicit NetCDF fallback")
        coarse = coarse or self.coarse_geometry
        if coarse is None or "catmxy" not in self.files:
            raise ValueError(
                f"{self.key}: automatic limits require native catmxy and coarse map geometry; use manual limits"
            )
        inherited_id = None if inherited is None else hashlib.sha256(np.ascontiguousarray(inherited).tobytes()).hexdigest()
        policy = (f"assigned-pixel-sparse-patches-{SPARSE_STATS_STRATA}-{SPARSE_STATS_PATCH}-v1"
                  if self.sparse_statistics else "assigned-pixel-p5-p95-cog-v1")
        key = (name, bool(positive), tuple(quantiles), policy, inherited_id,
               coarse.nx, coarse.ny, self.source_identity)
        cache_path = None
        if self.cog:
            digest = hashlib.sha256(repr((self.key, key)).encode()).hexdigest()
            cache_root = Path(os.environ.get("CMF_EXPLORER_STATS_CACHE", str(Path(tempfile.gettempdir()) / "cmf-explorer-native-stats")))
            cache_path = cache_root / (digest + ".json")
            if key not in self._stats and cache_path.is_file():
                try:
                    values = json.loads(cache_path.read_text())
                    if len(values) == 2 and all(isinstance(v, (int, float)) for v in values):
                        self._stats[key] = tuple(values)
                except (ValueError, OSError):
                    pass
        if key not in self._stats and self.sparse_statistics:
            self._stats[key] = self._sparse_percentiles(name, coarse, quantiles, inherited, positive)
        if key not in self._stats:
            g = self.geometry
            block = max(1, 500000 // g.nx)
            with tempfile.TemporaryFile() as stream:
                stream.truncate(g.nx * g.ny * 8)
                work = np.memmap(stream, dtype="f8", mode="r+", shape=(g.nx * g.ny,))
                count = 0
                assigned_count = 0
                for start in range(0, g.ny, block):
                    rows = np.arange(start, min(g.ny, start + block))
                    x, y = self.sample("catmxy", rows, np.arange(g.nx))
                    valid, _, _ = assignment(x, y, coarse)
                    if inherited is None:
                        values = self.sample(name, rows, np.arange(g.nx))
                    else:
                        values = np.full(valid.shape, np.nan)
                        values[valid] = inherited[y[valid] - 1, x[valid] - 1]
                    assigned_count += int(valid.sum())
                    finite = values[valid & np.isfinite(values) & ((values > 0) if positive else True)]
                    work[count : count + finite.size] = finite
                    count += finite.size
                if not assigned_count:
                    raise ValueError(
                        f"{self.key}: no valid native catmxy assignments for automatic limits; use manual limits"
                    )
                if count:
                    low, high = np.percentile(work[:count], quantiles, overwrite_input=True)
                else:
                    low = high = np.nan  # Let a Log display choose its documented fallback, not fake percentiles.
                del work
            self._stats[key] = float(low), float(high if tuple(quantiles) != (2, 98) or high > low else low + 1)
        if cache_path is not None and not cache_path.exists():
            try:
                cache_path.parent.mkdir(parents=True, exist_ok=True)
                with tempfile.NamedTemporaryFile(mode="w", dir=cache_path.parent, delete=False) as stream:
                    json.dump(self._stats[key], stream)
                    temporary = stream.name
                os.replace(temporary, cache_path)
            except OSError:
                pass  # A read-only cache directory never invalidates exact in-memory statistics.
        if not allow_empty and not np.isfinite(self._stats[key]).all():
            raise ValueError(f"{self.key}: no {'positive ' if positive else ''}valid {name} values")
        return self._stats[key]

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
    """Discover standard CSV inventories and explicit legacy tile descriptors."""
    root = Path(map_dir)
    tiles = {}
    cog_cache = RasterCache()
    locations = list(root.rglob('location.csv'))
    locations.extend(path for path in root.rglob('location.txt')
                     if not (path.parent / 'location.csv').is_file())
    for location in sorted(locations, key=lambda p: (p.parent.name.endswith("_nc"), str(p))):
        try:
            if location.suffix.lower() == '.csv':
                with location.open(newline='', encoding='utf-8-sig') as stream:
                    reader = csv.DictReader(stream)
                    if tuple(field.strip() for field in (reader.fieldnames or ())) != (
                        'iarea', 'carea', 'west', 'east', 'south', 'north', 'nx', 'ny', 'csize'
                    ):
                        raise ValueError('invalid location.csv header')
                    records = [{key.strip(): (value or '').strip() for key, value in row.items()
                                if key is not None} for row in reader]
            else:
                lines = [line.split() for line in location.read_text().splitlines() if line.strip()]
                count = int(lines[0][0])
                records = [dict(zip(('iarea', 'carea', 'west', 'east', 'south', 'north', 'nx', 'ny', 'csize'), row))
                           for row in lines[2:]]
                if len(records) != count:
                    raise ValueError('legacy area count disagrees with location records')
            for record in records:
                name = record['carea']
                w, e, s, n = (float(record[field]) for field in ('west', 'east', 'south', 'north'))
                nx, ny, step = int(record['nx']), int(record['ny']), float(record['csize'])
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
                relative = location.parent.relative_to(root)
                if relative.parts and relative.parts[0] == 'binary':
                    relative = Path(*relative.parts[1:])
                # Keep legacy JSON/tile identities stable while preferring _nc
                # products for the same declared native geometry and prefix.
                canonical = relative.with_name(relative.name[:-3]) if relative.name.endswith("_nc") else relative
                key = str(canonical / name)
                tile = tiles.get(key)
                if tile is not None and tile.geometry != g:
                    raise ValueError(f"{key}: Binary/NetCDF native geometries disagree")
                data_directory = root / canonical
                if not data_directory.is_dir():
                    data_directory = root / 'binary' / canonical
                if tile is None:
                    tile = Tile(key, data_directory, name, g, coarse_geometry=Geometry.read(root))
                for field_name, bytes_per_pixel in [
                    ("catmxy", 4),
                    ("visual", 1),
                    ("elevtn", 4),
                    ("flddif", 4),
                    ("catmz100", 1),
                    ("uparea", 4),
                    ("rivwth", 4),
                ]:
                    nc_path = root / canonical / f"{name}.{field_name}.nc"
                    path = root / 'binary' / canonical / f"{name}.{field_name}.bin"
                    legacy_binary_path = location.parent / f"{name}.{field_name}.bin"
                    if not path.is_file() and legacy_binary_path.is_file():
                        path = legacy_binary_path
                    cog_path = root / "COG" / canonical / f"{name}.{field_name}.tif"
                    if cog_path.is_file():
                        try:
                            source = COGSource.open(cog_path, field_name, g, cog_cache, root / canonical.with_name(canonical.name + "_nc") / f"{name}.{field_name}.nc")
                            tile.files[field_name] = cog_path
                            tile.cog[field_name] = source
                            tile.netcdf.pop(field_name, None)
                            continue  # Valid COG discovery must not open the high-resolution NetCDF.
                        except (OSError, ValueError) as exc:
                            messages.append(f"{cog_path}: invalid/incompatible COG; explicit fallback: {exc}")
                    if field_name in tile.cog:
                        continue
                    if nc_path.is_file():
                        try:
                            source = NetCDFSource.open(nc_path, field_name, g)
                            tile.files[field_name] = nc_path
                            tile.netcdf[field_name] = source
                        except (OSError, ValueError, KeyError) as exc:
                            tile.files.pop(field_name, None)
                            tile.netcdf.pop(field_name, None)
                            messages.append(f"{nc_path}: invalid NetCDF product skipped: {exc}")
                    elif path.is_file() and field_name not in tile.netcdf:
                        if path.stat().st_size == nx * ny * bytes_per_pixel:
                            tile.files[field_name] = path
                        else:
                            messages.append(f"{path.name}: wrong declared Binary size; skipped")
                if tile.files:
                    tiles[key] = tile
                else:
                    tiles.pop(key, None)
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

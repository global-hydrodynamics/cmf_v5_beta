"""Lazy native-pixel reads from registered high-resolution NetCDF products."""

from dataclasses import dataclass
from pathlib import Path

import numpy as np
from netCDF4 import Dataset

from map_reader import canonical_units


@dataclass(frozen=True)
class NetCDFSource:
    path: Path
    names: tuple
    dimensions: tuple
    reverse_y: bool
    reverse_x: bool
    shape: tuple
    factor: float
    missing: tuple

    @classmethod
    def open(cls, path, name, geometry):
        """Validate metadata/coordinates only; never read a full raster at discovery."""
        with Dataset(path, "r") as ds:
            axes = []
            for candidates, expected, units in [
                (("lat", "latitude"), geometry.lat, "degrees_north"),
                (("lon", "longitude"), geometry.lon, "degrees_east"),
            ]:
                key = next((k for k in candidates if k in ds.variables), None)
                if key is None:
                    raise ValueError(f"{path.name}: missing {candidates[0]} coordinate")
                var = ds[key]
                if var.ndim != 1 or canonical_units(getattr(var, "units", "")) != units:
                    raise ValueError(f"{path.name}: invalid {key} coordinate metadata")
                values = np.ma.asarray(var[:]).filled(np.nan)
                tol = max(1e-5, geometry.resolution * 1e-4)
                if len(values) != len(expected) or not np.isfinite(values).all():
                    raise ValueError(f"{path.name}: invalid {key} coordinate length/values")
                if np.allclose(values, expected, atol=tol, rtol=0):
                    reverse = False
                elif np.allclose(values[::-1], expected, atol=tol, rtol=0):
                    reverse = True
                else:
                    raise ValueError(f"{path.name}: {key} disagrees with native location.txt pixel centers")
                axes.append((var.dimensions[0], reverse))
            if name == "catmxy":
                names = next((pair for pair in (("catmxx", "catmyy"), ("catmx", "catmy"))
                              if all(k in ds.variables for k in pair)), None)
                if names is None:
                    raise ValueError(f"{path.name}: missing paired catmxx/catmyy (or catmx/catmy)")
            else:
                names = (name,)
            dtype = np.dtype("i2" if name == "catmxy" else "i1" if name in ("visual", "catmz100") else "f4")
            factor = 1.0
            missing = []
            for key in names:
                if key not in ds.variables:
                    raise ValueError(f"{path.name}: missing {key}")
                var = ds[key]
                if var.ndim != 2 or set(var.dimensions) != {a[0] for a in axes}:
                    raise ValueError(f"{path.name}:{key}: expected exactly native lat/lon dimensions")
                if var.dtype.kind != dtype.kind or var.dtype.itemsize != dtype.itemsize:
                    raise ValueError(f"{path.name}:{key}: expected {dtype}, found {var.dtype}")
                if any(hasattr(var, attr) for attr in ("scale_factor", "add_offset")):
                    raise ValueError(f"{path.name}:{key}: packed/scaled data are unsupported")
                actual = canonical_units(getattr(var, "units", "1" if dtype.kind == "i" else ""))
                expected = "1" if dtype.kind == "i" else "km2" if name == "uparea" else "m"
                if name == "uparea" and actual == "m2":
                    factor = 1e-6  # Native uparea is displayed as km²; never inherit coarse values here.
                elif actual != expected:
                    raise ValueError(f"{path.name}:{key}: expected units {expected}, found {actual}")
                codes = tuple(float(v) for attr in ("_FillValue", "missing_value")
                              for v in np.atleast_1d(getattr(var, attr, [])))
                if name == "catmxy" and any(v > 0 for v in codes):
                    raise ValueError(f"{path.name}:{key}: positive missing assignment code is unsupported")
                missing.append(codes)
            return cls(Path(path), tuple(names), tuple(a[0] for a in axes), axes[0][1], axes[1][1],
                       (geometry.ny, geometry.nx), factor, tuple(missing))

    def read(self, rows, cols):
        # netCDF4 orthogonal 1-D indexing reads precisely the requested native
        # rows/columns, unlike NumPy's paired advanced indices. No display-image
        # interpolation is used to identify catmxy assignments.
        rr = self.shape[0] - 1 - rows if self.reverse_y else rows
        cc = self.shape[1] - 1 - cols if self.reverse_x else cols
        values = []
        with Dataset(self.path, "r") as ds:
            for name, missing in zip(self.names, self.missing):
                var = ds[name]
                var.set_auto_maskandscale(False)
                transpose = var.dimensions != self.dimensions
                raw = np.asarray(var[cc, rr] if transpose else var[rr, cc])
                if transpose:
                    raw = raw.T
                if raw.dtype.kind == "f":
                    raw = raw.astype(float)
                    mask = ~np.isfinite(raw) | (raw == -9999)
                    for code in missing:
                        mask |= raw == code
                    raw[mask] = np.nan
                    raw *= self.factor
                values.append(raw)
        return np.stack(values)

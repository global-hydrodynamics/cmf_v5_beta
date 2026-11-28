# SPDX-License-Identifier: Apache-2.0
"""Read and write CaMa-Flood map geometry and runoff-mapping metadata."""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
import math
from pathlib import Path

import f90nml
import numpy as np


@dataclass(frozen=True)
class MapGeometry:
    nx: int
    ny: int
    nlfp: int
    resolution: float
    west: float
    east: float
    south: float
    north: float

    def values(self) -> tuple[int | float, ...]:
        return (self.nx, self.ny, self.nlfp, self.resolution,
                self.west, self.east, self.south, self.north)


@dataclass(frozen=True)
class DimInfo:
    """CaMa-Flood model geometry and paired runoff-grid mapping metadata."""
    nx: int
    ny: int
    nlfp: int
    west: float
    east: float
    north: float
    south: float
    inpmat_file: str
    nxin: int
    nyin: int
    inpn: int
    westin: float
    eastin: float
    northin: float
    southin: float
    olatin: str

    def values(self) -> tuple[int | str | float, ...]:
        """Return fields in DIMINFO group order followed by INPUTDIM group order."""
        return (self.nx, self.ny, self.nlfp, self.west, self.east, self.north,
                self.south, self.inpmat_file, self.nxin, self.nyin, self.inpn,
                self.westin, self.eastin, self.northin, self.southin, self.olatin)


def geometry_paths(path: str | Path) -> tuple[Path, Path]:
    """Return authoritative Namelist and legacy TXT candidates for a map path."""
    target = Path(path)
    directory = target.parent if target.name in {"params.nml", "params.txt"} else target
    return directory / "params.nml", directory / "params.txt"


def has_map_geometry(path: str | Path) -> bool:
    nml_path, txt_path = geometry_paths(path)
    return nml_path.is_file() or txt_path.is_file()


def read_legacy_values(path: str | Path) -> tuple[tuple[str, ...], MapGeometry]:
    """Read the first eight numeric records and retain their exact decimal tokens."""
    source = Path(path)
    tokens = []
    try:
        for line_no, line in enumerate(source.read_text(encoding="utf-8").splitlines(), 1):
            line = line.split("!!", 1)[0].split("#", 1)[0].strip()
            if not line:
                continue
            token = line.split()[0]
            try:
                Decimal(token)
            except InvalidOperation as exc:
                raise ValueError(f"{source}:{line_no}: expected a numeric map-geometry value") from exc
            tokens.append(token)
            if len(tokens) == 8:
                break
    except OSError as exc:
        raise ValueError(f"Cannot read legacy map geometry {source}: {exc}") from exc
    if len(tokens) != 8:
        raise ValueError(f"{source} must provide NX, NY, NLFP, resolution, west, east, south, north")
    try:
        geometry = _validated_geometry(
            int(tokens[0]), int(tokens[1]), int(tokens[2]),
            *(float(value) for value in tokens[3:]), source=source,
        )
    except (ValueError, OverflowError) as exc:
        raise ValueError(f"{source}: invalid map geometry: {exc}") from exc
    if any(Decimal(value) != Decimal(str(integer)) for value, integer in zip(tokens[:3], geometry.values()[:3])):
        raise ValueError(f"{source}: NX, NY, and NLFP must be integers")
    return tuple(tokens), geometry


def read_nml_values(path: str | Path) -> MapGeometry:
    """Read GRID and DOMAIN geometry through the standard f90nml reader."""
    source = Path(path)
    try:
        data = f90nml.read(source)
    except (OSError, ValueError, TypeError) as exc:
        raise ValueError(f"Cannot read map geometry {source}: {exc}") from exc
    try:
        grid = data["grid"]
        domain = data["domain"]
        nx, ny, nlfp = (grid[name] for name in ("nx", "ny", "nlfp"))
        resolution = grid["resolution"]
        west, east, south, north = (domain[name] for name in ("west", "east", "south", "north"))
    except (KeyError, TypeError) as exc:
        raise ValueError(f"{source}: required &GRID and &DOMAIN geometry values are missing") from exc
    if any(type(value) is not int for value in (nx, ny, nlfp)):
        raise ValueError(f"{source}: GRID NX, NY, and NLFP must be integers")
    numeric = (resolution, west, east, south, north)
    if any(type(value) not in (int, float) for value in numeric):
        raise ValueError(f"{source}: resolution and domain bounds must be real numbers")
    return _validated_geometry(nx, ny, nlfp, *(float(value) for value in numeric), source=source)


def read_map_geometry(path: str | Path) -> MapGeometry:
    """Read authoritative NML, retaining TXT-only compatibility and rejecting conflicts."""
    nml_path, txt_path = geometry_paths(path)
    if nml_path.is_file():
        geometry = read_nml_values(nml_path)
        if txt_path.is_file():
            _, legacy_geometry = read_legacy_values(txt_path)
            if legacy_geometry.values() != geometry.values():
                raise ValueError(f"Conflicting map geometry in {nml_path} and {txt_path}")
        return geometry
    if txt_path.is_file():
        return read_legacy_values(txt_path)[1]
    raise FileNotFoundError(f"No params.nml or params.txt found for map geometry at {Path(path)}")


def render_nml(geometry: MapGeometry) -> str:
    """Render the eight validated fields in the shared GRID/DOMAIN Namelist schema."""
    return (
        "! CaMa-Flood map geometry\n"
        "! params.nml\n\n"
        "&GRID\n"
        f"  NX         = {geometry.nx}       ! Number of grid cells (east-west)\n"
        f"  NY         = {geometry.ny}      ! Number of grid cells (north-south)\n"
        f"  NLFP       = {geometry.nlfp}       ! Number of floodplain layers\n"
        f"  RESOLUTION = {_real_token(geometry.resolution)} ! Grid resolution [degree]\n"
        "/\n\n"
        "&DOMAIN\n"
        f"  WEST  = {_real_token(geometry.west)} ! Western edge [degree]\n"
        f"  EAST  = {_real_token(geometry.east)} ! Eastern edge [degree]\n"
        f"  SOUTH = {_real_token(geometry.south)} ! Southern edge [degree]\n"
        f"  NORTH = {_real_token(geometry.north)} ! Northern edge [degree]\n"
        "/\n"
    )


def render_legacy(geometry: MapGeometry) -> str:
    """Render a readable, eight-record compatibility file from authoritative geometry."""
    labels = (
        "grid number (east-west)", "grid number (north-south)", "floodplain layers",
        "grid size [deg]", "west edge [deg]", "east edge [deg]",
        "south edge [deg]", "north edge [deg]",
    )
    return "".join(f"{value:>24}{label:>28}\n" for value, label in zip(geometry.values(), labels))


def write_nml(path: str | Path, geometry: MapGeometry) -> None:
    """Write geometry in the standard schema for newly generated regional maps."""
    Path(path).write_text(render_nml(geometry), encoding="utf-8")


def read_diminfo_nml(path: str | Path) -> DimInfo:
    """Read and validate the standard &DIMINFO and &INPUTDIM groups."""
    source = Path(path)
    try:
        data = f90nml.read(source)
        if set(data) != {"diminfo", "inputdim"}:
            raise ValueError(f"{source}: expected exactly &DIMINFO and &INPUTDIM groups")
        model = data["diminfo"]
        input_grid = data["inputdim"]
        model_fields = ("nx", "ny", "nlfp", "west", "east", "north", "south")
        input_fields = ("inpmat_file", "nxin", "nyin", "inpn", "westin", "eastin",
                        "northin", "southin", "olatin")
        if set(model) != set(model_fields):
            raise ValueError(f"{source}: DIMINFO must contain exactly the seven model-grid fields")
        if set(input_grid) != set(input_fields):
            raise ValueError(f"{source}: INPUTDIM must contain exactly the nine input-grid fields")
        values = [model[field] for field in model_fields]
        values.extend(input_grid[field] for field in input_fields)
    except (OSError, ValueError, TypeError, KeyError) as exc:
        raise ValueError(f"Cannot read required DIMINFO/INPUTDIM fields from {source}: {exc}") from exc
    return _validated_diminfo(*values, source=source)


def read_legacy_diminfo(path: str | Path) -> DimInfo:
    """Reject positional metadata that omits required input-grid provenance."""
    raise ValueError(
        f"{path}: legacy DIMINFO does not record separate input-grid bounds and latitude order; "
        "regenerate it with param_inpmat_generate.py using the original grid settings"
    )


def render_diminfo_nml(diminfo: DimInfo) -> str:
    """Render the canonical two-group descriptor in documented order."""
    checked = _validated_diminfo(*diminfo.values(), source="DIMINFO")
    return (
        "! CaMa-Flood model grid and runoff input-grid mapping\n"
        "! DIMINFO describes the model grid; INPUTDIM describes its runoff input.\n\n"
        "&DIMINFO\n"
        "  ! CaMa-Flood model grid\n"
        f"  NX    = {checked.nx}\n"
        f"  NY    = {checked.ny}\n"
        f"  NLFP  = {checked.nlfp}\n"
        f"  WEST  = {_real_token(checked.west)}\n"
        f"  EAST  = {_real_token(checked.east)}\n"
        f"  NORTH = {_real_token(checked.north)}\n"
        f"  SOUTH = {_real_token(checked.south)}\n"
        "/\n\n"
        "&INPUTDIM\n"
        "  ! Runoff input grid and mapping\n"
        f"  INPMAT_FILE = '{_namelist_string(checked.inpmat_file)}'\n"
        f"  NXIN    = {checked.nxin}\n"
        f"  NYIN    = {checked.nyin}\n"
        f"  INPN    = {checked.inpn}\n"
        f"  WESTIN  = {_real_token(checked.westin)}\n"
        f"  EASTIN  = {_real_token(checked.eastin)}\n"
        f"  NORTHIN = {_real_token(checked.northin)}\n"
        f"  SOUTHIN = {_real_token(checked.southin)}\n"
        f"  OLATIN  = '{checked.olatin}'\n"
        "/\n"
    )


def write_diminfo_nml(path: str | Path, diminfo: DimInfo) -> None:
    """Write a canonical v5 diminfo Namelist."""
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(render_diminfo_nml(diminfo), encoding="utf-8")


def _validated_geometry(nx, ny, nlfp, resolution, west, east, south, north, *, source):
    values = (resolution, west, east, south, north)
    if min(nx, ny, nlfp) < 1:
        raise ValueError(f"{source}: NX, NY, and NLFP must be positive")
    if any(not math.isfinite(float(value)) for value in values):
        raise ValueError(f"{source}: resolution and bounds must be finite")
    if resolution <= 0 or east <= west or north <= south:
        raise ValueError(f"{source}: invalid resolution or geographic extent")
    return MapGeometry(nx, ny, nlfp, *(float(value) for value in values))


def _validated_diminfo(nx, ny, nlfp, west, east, north, south, inpmat_file,
                       nxin, nyin, inpn, westin, eastin, northin, southin, olatin, *, source):
    model_dimensions = (nx, ny, nlfp)
    input_dimensions = (nxin, nyin, inpn)
    if any(type(value) is not int for value in model_dimensions + input_dimensions):
        raise ValueError(f"{source}: grid dimensions, NLFP, and INPN must be integers")
    if min(model_dimensions + input_dimensions) < 1:
        raise ValueError(f"{source}: grid dimensions, NLFP, and INPN must be positive")
    model_bounds = (west, east, north, south)
    input_bounds = (westin, eastin, northin, southin)
    if any(not math.isfinite(float(value)) for value in model_bounds + input_bounds):
        raise ValueError(f"{source}: model-grid and input-grid bounds must be finite")
    if east <= west or north <= south:
        raise ValueError(f"{source}: invalid model-grid extent")
    if eastin <= westin or northin <= southin:
        raise ValueError(f"{source}: invalid runoff input-grid extent")
    if not isinstance(inpmat_file, str) or not inpmat_file.strip():
        raise ValueError(f"{source}: INPMAT_FILE must be a non-empty filename")
    if Path(inpmat_file).name != inpmat_file.strip():
        raise ValueError(f"{source}: INPMAT_FILE must be a filename, not a path")
    if not isinstance(olatin, str) or olatin not in {"NtoS", "StoN"}:
        raise ValueError(f"{source}: OLATIN must be 'NtoS' or 'StoN'")
    return DimInfo(
        nx, ny, nlfp, *model_bounds, inpmat_file.strip(),
        nxin, nyin, inpn, *input_bounds, olatin,
    )


def _real_token(value: float) -> str:
    """Write the shortest decimal preserving the value's available precision."""
    token = np.format_float_positional(value, unique=True, trim="-")
    return token if any(character in token.lower() for character in (".", "e")) else token + ".0"


def _namelist_string(value: str) -> str:
    """Escape a single-quoted Fortran Namelist character value."""
    return value.replace("'", "''")

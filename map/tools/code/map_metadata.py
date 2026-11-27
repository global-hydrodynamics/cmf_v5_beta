# SPDX-License-Identifier: Apache-2.0
"""Read and write CaMa-Flood map geometry and runoff-mapping metadata."""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from io import StringIO
import math
from pathlib import Path

import f90nml


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
    """Model dimensions, runoff-grid mapping shape, paired matrix name, and bounds."""
    nx: int
    ny: int
    nlfp: int
    nxin: int
    nyin: int
    inpn: int
    inpmat_file: str
    west: float
    east: float
    north: float
    south: float

    def values(self) -> tuple[int | str | float, ...]:
        return (self.nx, self.ny, self.nlfp, self.nxin, self.nyin, self.inpn,
                self.inpmat_file, self.west, self.east, self.north, self.south)


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
    """Read and validate the maintained &DIMINFO schema with f90nml."""
    source = Path(path)
    try:
        data = f90nml.read(source)
        group = data["diminfo"]
        fields = ("nx", "ny", "nlfp", "nxin", "nyin", "inpn", "inpmat_file",
                  "west", "east", "north", "south")
        if set(group) != set(fields):
            raise ValueError(f"{source}: DIMINFO must contain exactly the eleven documented fields")
        values = [group[field] for field in fields]
    except (OSError, ValueError, TypeError, KeyError) as exc:
        raise ValueError(f"Cannot read required &DIMINFO fields from {source}: {exc}") from exc
    if any(type(value) is not int for value in values[:6]):
        raise ValueError(f"{source}: DIMINFO dimensions and INPN must be integers")
    if not isinstance(values[6], str) or not values[6].strip():
        raise ValueError(f"{source}: INPMAT_FILE must be a non-empty string")
    if any(type(value) not in (int, float) for value in values[7:]):
        raise ValueError(f"{source}: DIMINFO bounds must be real numbers")
    return _validated_diminfo(*values[:7], *(float(value) for value in values[7:]), source=source)


def read_legacy_diminfo(path: str | Path) -> DimInfo:
    """Read the eleven positional records only for explicit one-time migration."""
    source = Path(path)
    try:
        records = []
        for line_no, line in enumerate(source.read_text(encoding="utf-8").splitlines(), 1):
            value = line.split("!!", 1)[0].split("#", 1)[0].strip()
            if value:
                records.append((line_no, value))
    except OSError as exc:
        raise ValueError(f"Cannot read legacy diminfo {source}: {exc}") from exc
    if len(records) != 11:
        raise ValueError(f"{source}: expected exactly 11 non-empty legacy records")
    try:
        dimensions = [int(records[index][1].split()[0]) for index in range(6)]
        matrix_file = records[6][1]
        bounds = [float(records[index][1].split()[0]) for index in range(7, 11)]
    except (ValueError, IndexError) as exc:
        raise ValueError(f"{source}: invalid legacy diminfo record") from exc
    if any(len(records[index][1].split()) != 1 for index in range(6)):
        raise ValueError(f"{source}: dimension records must each contain one value")
    if len(matrix_file.split()) != 1 or any(
        len(records[index][1].split()) != 1 for index in range(7, 11)
    ):
        raise ValueError(f"{source}: matrix filename and bounds must each contain one value")
    return _validated_diminfo(*dimensions, matrix_file, *bounds, source=source)


def render_diminfo_nml(diminfo: DimInfo) -> str:
    """Serialize the canonical v5 &DIMINFO group through f90nml."""
    checked = _validated_diminfo(*diminfo.values(), source="DIMINFO")
    namelist = f90nml.Namelist({"diminfo": {
        "nx": checked.nx,
        "ny": checked.ny,
        "nlfp": checked.nlfp,
        "nxin": checked.nxin,
        "nyin": checked.nyin,
        "inpn": checked.inpn,
        "inpmat_file": checked.inpmat_file,
        "west": checked.west,
        "east": checked.east,
        "north": checked.north,
        "south": checked.south,
    }})
    output = StringIO()
    f90nml.write(namelist, output)
    return output.getvalue()


def write_diminfo_nml(path: str | Path, diminfo: DimInfo) -> None:
    """Write a canonical v5 diminfo Namelist."""
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    checked = _validated_diminfo(*diminfo.values(), source="DIMINFO")
    namelist = f90nml.Namelist({"diminfo": {
        "nx": checked.nx, "ny": checked.ny, "nlfp": checked.nlfp,
        "nxin": checked.nxin, "nyin": checked.nyin, "inpn": checked.inpn,
        "inpmat_file": checked.inpmat_file, "west": checked.west,
        "east": checked.east, "north": checked.north, "south": checked.south,
    }})
    f90nml.write(namelist, destination, force=True)


def _validated_geometry(nx, ny, nlfp, resolution, west, east, south, north, *, source):
    values = (resolution, west, east, south, north)
    if min(nx, ny, nlfp) < 1:
        raise ValueError(f"{source}: NX, NY, and NLFP must be positive")
    if any(not math.isfinite(float(value)) for value in values):
        raise ValueError(f"{source}: resolution and bounds must be finite")
    if resolution <= 0 or east <= west or north <= south:
        raise ValueError(f"{source}: invalid resolution or geographic extent")
    return MapGeometry(nx, ny, nlfp, *(float(value) for value in values))


def _validated_diminfo(nx, ny, nlfp, nxin, nyin, inpn, inpmat_file,
                       west, east, north, south, *, source):
    dimensions = (nx, ny, nlfp, nxin, nyin, inpn)
    if any(type(value) is not int for value in dimensions) or min(dimensions) < 1:
        raise ValueError(f"{source}: NX, NY, NLFP, NXIN, NYIN, and INPN must be positive integers")
    bounds = (west, east, north, south)
    if any(not math.isfinite(float(value)) for value in bounds):
        raise ValueError(f"{source}: model-grid bounds must be finite")
    if east <= west or north <= south:
        raise ValueError(f"{source}: invalid model-grid extent")
    if not isinstance(inpmat_file, str) or not inpmat_file.strip():
        raise ValueError(f"{source}: INPMAT_FILE must be a non-empty filename")
    return DimInfo(*dimensions, inpmat_file.strip(), *(float(value) for value in bounds))


def _real_token(value: float) -> str:
    """Keep enough digits to round-trip a Python float and retain real syntax."""
    token = repr(value)
    return token if any(character in token.lower() for character in (".", "e")) else token + ".0"

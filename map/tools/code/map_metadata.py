# SPDX-License-Identifier: Apache-2.0
"""Read and write the eight scalar fields that define a CaMa-Flood map grid."""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
import math
from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:  # Python 3.10 uses the small tomli compatibility package.
    try:
        import tomli as tomllib
    except ModuleNotFoundError:
        tomllib = None


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


def geometry_paths(path: str | Path) -> tuple[Path, Path]:
    """Return the TOML and legacy TXT candidates for a map directory or params path."""
    target = Path(path)
    if target.is_dir():
        directory = target
    elif target.name in {"params.txt", "params.toml"}:
        directory = target.parent
    else:
        directory = target
    return directory / "params.toml", directory / "params.txt"


def has_map_geometry(path: str | Path) -> bool:
    toml_path, txt_path = geometry_paths(path)
    return toml_path.is_file() or txt_path.is_file()


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


def read_toml_values(path: str | Path) -> MapGeometry:
    source = Path(path)
    if tomllib is None:
        raise RuntimeError("Reading params.toml with Python 3.10 requires tomli; install repository requirements.txt")
    try:
        with source.open("rb") as stream:
            data = tomllib.load(stream)
    except (OSError, ValueError) as exc:
        raise ValueError(f"Cannot read map geometry {source}: {exc}") from exc
    try:
        grid = data["grid"]
        domain = data["domain"]
        nx, ny, nlfp = grid["nx"], grid["ny"], grid["nlfp"]
        resolution = grid["resolution"]
        west, east, south, north = (domain[name] for name in ("west", "east", "south", "north"))
    except (KeyError, TypeError) as exc:
        raise ValueError(f"{source}: required [grid] and [domain] geometry keys are missing") from exc
    if any(type(value) is not int for value in (nx, ny, nlfp)):
        raise ValueError(f"{source}: grid nx, ny, and nlfp must be integers")
    numeric = (resolution, west, east, south, north)
    if any(type(value) is not float for value in numeric):
        raise ValueError(f"{source}: resolution and domain bounds must be TOML floating-point values")
    return _validated_geometry(nx, ny, nlfp, *numeric, source=source)


def read_map_geometry(path: str | Path) -> MapGeometry:
    """Read authoritative TOML, retaining TXT-only compatibility and rejecting conflicts."""
    toml_path, txt_path = geometry_paths(path)
    if toml_path.is_file():
        geometry = read_toml_values(toml_path)
        if txt_path.is_file():
            _, legacy_geometry = read_legacy_values(txt_path)
            if legacy_geometry.values() != geometry.values():
                raise ValueError(f"Conflicting map geometry in {toml_path} and {txt_path}")
        return geometry
    if txt_path.is_file():
        return read_legacy_values(txt_path)[1]
    raise FileNotFoundError(f"No params.toml or params.txt found for map geometry at {Path(path)}")


def render_toml(tokens: tuple[str, ...]) -> str:
    """Render the legacy decimal records in the approved small TOML schema."""
    if len(tokens) != 8:
        raise ValueError("exactly eight map-geometry values are required")
    floats = tuple(_float_token(token) for token in tokens[3:])
    return (
        "# CaMa-Flood map geometry\n\n"
        "[grid]\n"
        f"nx = {tokens[0]}  # Number of grid cells (east-west)\n"
        f"ny = {tokens[1]}  # Number of grid cells (north-south)\n"
        f"nlfp = {tokens[2]}  # Number of floodplain layers\n"
        f"resolution = {floats[0]}  # Grid resolution [degree]\n\n"
        "[domain]\n"
        f"west = {floats[1]}  # Western edge [degree]\n"
        f"east = {floats[2]}  # Eastern edge [degree]\n"
        f"south = {floats[3]}  # Southern edge [degree]\n"
        f"north = {floats[4]}  # Northern edge [degree]\n"
    )


def render_legacy(geometry: MapGeometry) -> str:
    """Render a readable, eight-record compatibility file from authoritative geometry."""
    labels = (
        "grid number (east-west)", "grid number (north-south)", "floodplain layers",
        "grid size [deg]", "west edge [deg]", "east edge [deg]",
        "south edge [deg]", "north edge [deg]",
    )
    return "".join(f"{value:>24}{label:>28}\n" for value, label in zip(geometry.values(), labels))


def write_toml(path: str | Path, geometry: MapGeometry) -> None:
    """Write geometry in the standard schema for newly generated regional maps."""
    tokens = (str(geometry.nx), str(geometry.ny), str(geometry.nlfp),
              *(_float_token(format(value, ".17g")) for value in geometry.values()[3:]))
    Path(path).write_text(render_toml(tokens), encoding="utf-8")


def _validated_geometry(nx, ny, nlfp, resolution, west, east, south, north, *, source):
    values = (resolution, west, east, south, north)
    if min(nx, ny, nlfp) < 1:
        raise ValueError(f"{source}: NX, NY, and NLFP must be positive")
    if any(not math.isfinite(float(value)) for value in values):
        raise ValueError(f"{source}: resolution and bounds must be finite")
    if resolution <= 0 or east <= west or north <= south:
        raise ValueError(f"{source}: invalid resolution or geographic extent")
    return MapGeometry(nx, ny, nlfp, *(float(value) for value in values))


def _float_token(value: str) -> str:
    """Keep an exact numeric token while ensuring TOML parses it as a float."""
    return value if any(character in value.lower() for character in (".", "e")) else value + ".0"

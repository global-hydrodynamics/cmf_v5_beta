#!/usr/bin/env python3
"""Read CaMa-Flood map geometry for GrADS CTL generation."""

from __future__ import annotations

import math
import re
from dataclasses import dataclass
from pathlib import Path


class MapMetadataError(ValueError):
    """Map metadata is missing, malformed, or inconsistent."""


@dataclass(frozen=True)
class MapGeometry:
    nx: int
    ny: int
    resolution: float
    west: float
    east: float
    south: float
    north: float


def _strip_comment(line: str) -> str:
    """Remove a Fortran comment without treating quoted exclamation marks as comments."""
    quote = None
    for index, char in enumerate(line):
        if quote:
            if char == quote:
                quote = None
        elif char in "'\"":
            quote = char
        elif char == "!":
            return line[:index]
    return line


def _read_groups(path: Path) -> dict[str, dict[str, str]]:
    """Read scalar assignments from Fortran namelist groups."""
    groups: dict[str, dict[str, str]] = {}
    active = None
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        raise MapMetadataError(f"Cannot read map metadata {path}: {exc}") from exc

    for raw_line in lines:
        line = _strip_comment(raw_line).strip()
        if not line:
            continue
        header = re.match(r"&([A-Za-z][A-Za-z0-9_]*)", line)
        if header:
            active = header.group(1).lower()
            groups[active] = {}
            line = line[header.end():]
        if active is None:
            continue
        for match in re.finditer(r"([A-Za-z][A-Za-z0-9_]*)\s*=\s*([^,\s/]+)", line):
            groups[active][match.group(1).lower()] = match.group(2).strip("'\"")
        if "/" in line:
            active = None
    return groups


def _integer(group: dict[str, str], key: str, path: Path) -> int:
    try:
        number = int(group[key])
    except (KeyError, ValueError) as exc:
        raise MapMetadataError(f"{path}: missing or invalid {key.upper()} value") from exc
    if number <= 0:
        raise MapMetadataError(f"{path}: {key.upper()} must be positive")
    return number


def _real(group: dict[str, str], key: str, path: Path) -> float:
    try:
        number = float(group[key].replace("D", "E").replace("d", "e"))
    except (KeyError, ValueError) as exc:
        raise MapMetadataError(f"{path}: missing or invalid {key.upper()} value") from exc
    if not math.isfinite(number):
        raise MapMetadataError(f"{path}: {key.upper()} must be finite")
    return number


def _close(left: float, right: float) -> bool:
    return math.isclose(left, right, rel_tol=1e-9, abs_tol=1e-7)


def _validate(geometry: MapGeometry, path: Path) -> MapGeometry:
    if geometry.east <= geometry.west or geometry.north <= geometry.south:
        raise MapMetadataError(f"{path}: map bounds must have positive width and height")
    if not math.isfinite(geometry.resolution) or geometry.resolution <= 0:
        raise MapMetadataError(f"{path}: resolution must be positive and finite")
    dx = (geometry.east - geometry.west) / geometry.nx
    dy = (geometry.north - geometry.south) / geometry.ny
    if not _close(dx, geometry.resolution) or not _close(dy, geometry.resolution):
        raise MapMetadataError(
            f"{path}: bounds, dimensions, and resolution do not describe a consistent square grid"
        )
    return geometry


def _read_params_nml(path: Path) -> MapGeometry:
    groups = _read_groups(path)
    try:
        grid, domain = groups["grid"], groups["domain"]
    except KeyError as exc:
        raise MapMetadataError(f"{path}: expected &GRID and &DOMAIN groups") from exc
    return _validate(MapGeometry(
        _integer(grid, "nx", path),
        _integer(grid, "ny", path),
        _real(grid, "resolution", path),
        _real(domain, "west", path),
        _real(domain, "east", path),
        _real(domain, "south", path),
        _real(domain, "north", path),
    ), path)


def _read_diminfo_nml(path: Path) -> MapGeometry:
    groups = _read_groups(path)
    try:
        model = groups["diminfo"]
        groups["inputdim"]
    except KeyError as exc:
        raise MapMetadataError(f"{path}: expected &DIMINFO and &INPUTDIM groups") from exc
    nx = _integer(model, "nx", path)
    ny = _integer(model, "ny", path)
    west = _real(model, "west", path)
    east = _real(model, "east", path)
    south = _real(model, "south", path)
    north = _real(model, "north", path)
    if east <= west or north <= south:
        raise MapMetadataError(f"{path}: DIMINFO bounds must have positive width and height")
    dx = (east - west) / nx
    dy = (north - south) / ny
    if not _close(dx, dy):
        raise MapMetadataError(f"{path}: DIMINFO longitude and latitude spacing differ ({dx} vs {dy})")
    return _validate(MapGeometry(nx, ny, dx, west, east, south, north), path)


def _read_legacy_params(path: Path) -> MapGeometry:
    try:
        tokens = [line.split()[0] for line in path.read_text(encoding="utf-8").splitlines() if line.split()]
        nx, ny = int(tokens[0]), int(tokens[1])
        resolution = float(tokens[3])
        west, east, south, north = map(float, tokens[4:8])
    except (OSError, IndexError, ValueError) as exc:
        raise MapMetadataError(f"Cannot read legacy map geometry from {path}: {exc}") from exc
    if nx <= 0 or ny <= 0:
        raise MapMetadataError(f"{path}: grid dimensions must be positive")
    return _validate(MapGeometry(nx, ny, resolution, west, east, south, north), path)


def _map_paths(run_dir: Path, values: dict[str, str]) -> tuple[list[Path], Path | None]:
    directories = []
    diminfo_path = None
    for key in ("CNEXTXY", "CGRAREA", "CDIMINFO"):
        raw = values.get(key)
        if not raw:
            continue
        path = Path(raw)
        if not path.is_absolute():
            path = run_dir / path
        path = path.resolve()
        if key == "CDIMINFO" and path.is_file():
            diminfo_path = path
        directory = path if path.is_dir() else path.parent
        for parent in (directory, *directory.parents):
            if parent not in directories:
                directories.append(parent)
    return directories, diminfo_path


def read_map_geometry(run_dir: Path, values: dict[str, str]) -> MapGeometry:
    """Read authoritative map geometry, validating any paired model-grid DIMINFO."""
    directories, diminfo_path = _map_paths(run_dir, values)
    params_nml = next((directory / "params.nml" for directory in directories
                       if (directory / "params.nml").is_file()), None)
    params_txt = next((directory / "params.txt" for directory in directories
                       if (directory / "params.txt").is_file()), None)

    if params_nml:
        geometry = _read_params_nml(params_nml)
        if diminfo_path and diminfo_path.suffix.lower() == ".nml":
            diminfo = _read_diminfo_nml(diminfo_path)
            if (geometry.nx != diminfo.nx or geometry.ny != diminfo.ny
                    or any(not _close(left, right) for left, right in (
                        (geometry.west, diminfo.west), (geometry.east, diminfo.east),
                        (geometry.south, diminfo.south), (geometry.north, diminfo.north),
                        (geometry.resolution, diminfo.resolution)))):
                raise MapMetadataError(
                    f"Map geometry conflicts between {params_nml} and {diminfo_path}"
                )
        return geometry

    if diminfo_path and diminfo_path.suffix.lower() == ".nml":
        return _read_diminfo_nml(diminfo_path)
    if params_txt:
        return _read_legacy_params(params_txt)

    raise MapMetadataError(
        "Could not locate map geometry using CNEXTXY, CGRAREA, or CDIMINFO. "
        "Expected params.nml and/or the configured diminfo_<ROFFTAG>.nml."
    )

#!/usr/bin/env python3
"""Safely copy legacy map products into the NetCDF-first directory layout.

The default is a dry run. Existing legacy products are never removed. A target
collision is accepted only when source and destination bytes are identical.
"""
from __future__ import annotations

import argparse
import hashlib
import shutil
from pathlib import Path

try:
    from .map_metadata import has_map_geometry
except ImportError:  # Direct execution from the map-local Shell workflows.
    from map_metadata import has_map_geometry


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            value.update(block)
    return value.hexdigest()


def plan(map_dir: Path) -> list[tuple[Path, Path]]:
    moves = []
    for source in sorted(map_dir.glob('*.bin')) + sorted(map_dir.glob('*.ctl')):
        moves.append((source, map_dir / 'binary' / source.name))
    for old in sorted(map_dir.glob('netcdf/*.nc')):
        moves.append((old, map_dir / old.name))
    for directory in sorted(map_dir.iterdir()):
        if not directory.is_dir() or directory.name in ('binary', 'COG', 'netcdf'):
            continue
        if directory.name.endswith('_nc'):
            resolution = directory.name[:-3]
            for source in sorted(directory.iterdir()):
                target_dir = map_dir / resolution
                if source.suffix == '.nc' or source.name in ('location.csv', 'location.txt'):
                    moves.append((source, target_dir / source.name))
        if not directory.name.endswith('_nc') and any((directory / name).is_file()
                                                       for name in ('location.csv', 'location.txt')):
            for source in sorted(directory.glob('*.bin')) + sorted(directory.glob('*.ctl')):
                moves.append((source, map_dir / 'binary' / directory.name / source.name))
            for name in ('location.csv', 'location.txt'):
                if (directory / name).is_file():
                    moves.append((directory / name, map_dir / 'binary' / directory.name / name))
    for source in (map_dir / 'params.nml', map_dir / 'params.txt', *sorted(map_dir.glob('diminfo_*.nml'))):
        if source.is_file():
            moves.append((source, map_dir / 'binary' / source.name))
    return moves


def execute(map_dir: Path, apply: bool) -> int:
    products = plan(map_dir)
    conflicts = []
    for source, target in products:
        if not source.is_file():
            continue
        if target.exists():
            if not target.is_file() or digest(source) != digest(target):
                print(f'CONFLICT  {source} -> {target}')
                conflicts.append((source, target))
            else:
                print(f'EXISTS    {target} (identical)')
    if conflicts:
        print(f'Aborted before copying: {len(conflicts)} conflicting target(s).')
        return 1
    errors = 0
    for source, target in products:
        if not source.is_file() or target.exists():
            continue
        print(f'{"COPY" if apply else "WOULD COPY"} {source} -> {target}')
        if apply:
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
            if digest(source) != digest(target):
                print(f'ERROR     copy verification failed: {target}')
                errors += 1
    print(f'Planned {len(products)} file(s); conflicts: {errors}; source files retained.')
    return 1 if errors else 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--map-dir', type=Path, required=True, help='map root containing params.nml or legacy params.txt')
    parser.add_argument('--apply', action='store_true', help='copy products after collision preflight; default only reports')
    args = parser.parse_args()
    map_dir = args.map_dir.expanduser().resolve()
    if not has_map_geometry(map_dir):
        parser.error(f'not a map root (params.nml/params.txt missing): {map_dir}')
    return execute(map_dir, args.apply)


if __name__ == '__main__':
    raise SystemExit(main())

#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Safely convert legacy params.txt geometry to authoritative params.toml."""
from __future__ import annotations

import argparse
import os
from pathlib import Path
import tempfile

try:
    from .map_metadata import (
        geometry_paths,
        read_legacy_values,
        read_map_geometry,
        read_toml_values,
        render_legacy,
        render_toml,
    )
except ImportError:  # Direct execution from repository and map-local workflows.
    from map_metadata import (
        geometry_paths,
        read_legacy_values,
        read_map_geometry,
        read_toml_values,
        render_legacy,
        render_toml,
    )


def convert_map(map_dir: Path) -> str:
    """Create params.toml when absent, or verify an existing pair without overwriting."""
    toml_path, txt_path = geometry_paths(map_dir)
    if not txt_path.is_file():
        raise FileNotFoundError(f"legacy params.txt is missing: {txt_path}")
    tokens, _ = read_legacy_values(txt_path)
    if toml_path.exists():
        read_map_geometry(map_dir)
        return "UNCHANGED"
    content = render_toml(tokens)
    descriptor, temporary = tempfile.mkstemp(prefix=".params.", suffix=".toml.tmp", dir=map_dir)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as stream:
            stream.write(content)
        # Verify the temporary TOML and the source have the same eight values
        # before publishing the new metadata file.
        temporary_path = Path(temporary)
        if temporary_path.read_text(encoding="utf-8") != content:
            raise OSError(f"temporary TOML verification failed: {temporary_path}")
        toml_geometry = read_toml_values(temporary_path)
        if toml_geometry.values() != read_legacy_values(txt_path)[1].values():
            raise ValueError(f"numeric geometry changed during conversion: {txt_path}")
        os.link(temporary_path, toml_path)
        return "CONVERTED"
    finally:
        Path(temporary).unlink(missing_ok=True)


def write_legacy_copy(map_dir: Path, output: Path) -> str:
    """Create a legacy compatibility copy without replacing conflicting metadata."""
    geometry = read_map_geometry(map_dir)
    output = output if output.is_absolute() else map_dir / output
    content = render_legacy(geometry)
    if output.exists():
        _, existing = read_legacy_values(output)
        if existing.values() != geometry.values():
            raise ValueError(f"refusing to overwrite conflicting legacy metadata: {output}")
        return "UNCHANGED"
    output.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix=f".{output.name}.", suffix=".tmp", dir=output.parent)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as stream:
            stream.write(content)
        os.link(temporary, output)
        return "WRITTEN"
    finally:
        Path(temporary).unlink(missing_ok=True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    targets = parser.add_mutually_exclusive_group(required=True)
    targets.add_argument("--map-dir", type=Path, help="one map directory")
    targets.add_argument("--map-root", type=Path, help="recursively scan map directories on disk, including ignored files")
    parser.add_argument("--write-legacy", type=Path, help="write a generated params.txt compatibility copy at this path")
    args = parser.parse_args()
    if args.write_legacy and args.map_root:
        parser.error("--write-legacy can be used only with --map-dir")
    if args.map_dir:
        map_dirs = [args.map_dir.expanduser().resolve()]
    else:
        root = args.map_root.expanduser().resolve()
        map_dirs = sorted(path.parent for path in root.rglob("params.txt") if path.is_file())
    if args.write_legacy:
        try:
            print(f"{write_legacy_copy(map_dirs[0], args.write_legacy)} {args.write_legacy}")
            return 0
        except (OSError, ValueError, RuntimeError) as exc:
            print(f"ERROR {map_dirs[0]}: {exc}")
            return 1

    converted = unchanged = failed = 0
    for map_dir in map_dirs:
        try:
            result = convert_map(map_dir)
            print(f"{result} {map_dir / 'params.toml'}")
            converted += result == "CONVERTED"
            unchanged += result == "UNCHANGED"
        except (OSError, ValueError, RuntimeError) as exc:
            print(f"ERROR {map_dir}: {exc}")
            failed += 1
    print(f"Discovered: {len(map_dirs)}; converted: {converted}; already matched: {unchanged}; failed/conflicting: {failed}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())

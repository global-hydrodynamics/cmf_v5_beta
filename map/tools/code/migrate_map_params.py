#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Write a legacy params.txt compatibility copy from map geometry metadata."""
from __future__ import annotations

import argparse
import os
from pathlib import Path
import tempfile

try:
    from .map_metadata import read_legacy_values, read_map_geometry, render_legacy
except ImportError:  # Direct execution from repository and map-local workflows.
    from map_metadata import read_legacy_values, read_map_geometry, render_legacy


def write_legacy_copy(map_dir: Path, output: Path) -> str:
    """Create a TXT compatibility copy without replacing conflicting metadata."""
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
    parser.add_argument("--map-dir", type=Path, required=True)
    parser.add_argument("--write-legacy", type=Path, required=True)
    args = parser.parse_args()
    try:
        print(f"{write_legacy_copy(args.map_dir.expanduser().resolve(), args.write_legacy)} {args.write_legacy}")
    except (OSError, ValueError, RuntimeError) as exc:
        print(f"ERROR {args.map_dir}: {exc}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Convert legacy positional diminfo text files to native Fortran Namelist."""
from __future__ import annotations

import argparse
from pathlib import Path

try:
    from .map_metadata import read_diminfo_nml, read_legacy_diminfo, write_diminfo_nml
except ImportError:  # Direct execution from map-local workflows.
    from map_metadata import read_diminfo_nml, read_legacy_diminfo, write_diminfo_nml


def convert(source: Path, remove_legacy: bool = False) -> Path:
    """Write or verify a sibling NML; remove TXT only after exact verification."""
    if source.suffix.lower() != ".txt" or not source.name.startswith("diminfo_"):
        raise ValueError(f"Expected a diminfo_*.txt file: {source}")
    target = source.with_suffix(".nml")
    legacy = read_legacy_diminfo(source)
    if target.exists():
        current = read_diminfo_nml(target)
        if current != legacy:
            raise ValueError(f"Conflicting metadata: {source} and {target}")
    else:
        write_diminfo_nml(target, legacy)
        if read_diminfo_nml(target) != legacy:
            target.unlink(missing_ok=True)
            raise ValueError(f"Namelist verification failed: {target}")
    if remove_legacy:
        source.unlink()
    return target


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="+", type=Path, help="legacy diminfo_*.txt paths")
    parser.add_argument(
        "--remove-legacy", action="store_true",
        help="remove each TXT only after its NML has been read back and verified",
    )
    args = parser.parse_args()
    for source in args.paths:
        print(f"{source} -> {convert(source, args.remove_legacy)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""List registered base map sources for the format-conversion Shell workflows."""
from __future__ import annotations

import argparse
from pathlib import Path

try:
    from . import convert_map_binary_to_netcdf as converter
except ImportError:
    import convert_map_binary_to_netcdf as converter


def list_sources(map_dir: Path, registry: Path, source_format: str, output: Path) -> int:
    rows = converter.registry_rows(registry)
    supported_rows: dict[str, list[tuple[int, dict[str, str]]]] = {}
    for index, row in enumerate(rows):
        dimensions = (row.get("dimensions") or "").replace(" ", "").upper()
        if dimensions not in {"NX,NY", "NX,NY,NLFP"}:
            continue
        for filename in converter.registered_base_filenames(row):
            supported_rows.setdefault(filename, []).append((index, row))

    directory = map_dir if source_format == "netcdf" else map_dir / "binary"
    extension = ".nc" if source_format == "netcdf" else ".bin"
    candidates: list[tuple[int, int, str, str]] = []
    for path in sorted(directory.glob(f"*{extension}")):
        binary_name = path.stem + ".bin"
        binary_name = converter.standard_binary_filename(binary_name)
        matches = supported_rows.get(binary_name, [])
        if not matches:
            continue
        supported, _ = converter.conversion_support([row for _, row in matches])
        if not supported:
            continue
        row_index, row = min(matches, key=lambda item: (int(item[1]["category_id"]), item[0]))
        candidates.append((int(row["category_id"]), row_index, path.name, (row.get("category") or "Registered map products").strip()))

    candidates.sort(key=lambda item: (item[0], item[1]))
    output.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        f"# {source_format.title()}-to-{('Binary' if source_format == 'netcdf' else 'NetCDF')} conversion list",
        "# Generated from map_variables.csv; comment out files to limit conversion.",
    ]
    previous_category = None
    for category_id, _, filename, category in candidates:
        if category_id != previous_category:
            lines.extend(("", f"# [{category_id}] {category}"))
            previous_category = category_id
        lines.append(filename)
    output.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Listed {len(candidates)} registered {source_format} source files: {output}")
    return len(candidates)


def main() -> int:
    root = Path(__file__).resolve().parents[3]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--map-dir", type=Path, required=True)
    parser.add_argument("--registry", type=Path, default=root / "variable_table/map_variables.csv")
    parser.add_argument("--format", choices=("netcdf", "binary"), required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        list_sources(args.map_dir.resolve(), args.registry.resolve(), args.format, args.output.resolve())
    except (OSError, ValueError) as exc:
        parser.exit(1, f"ERROR: {exc}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

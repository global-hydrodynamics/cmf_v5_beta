#!/usr/bin/env python3
"""Convert the dedicated three-variable INPMAT between NetCDF and Binary."""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np

from mod_map_io import read_inpmat, write_inpmat


def read_diminfo(path: Path) -> tuple[dict[str, float | int], str]:
    lines = path.read_text().splitlines()
    if len(lines) < 11:
        raise ValueError(f'{path}: expected the 11-line diminfo contract')
    values = [line.split()[0] for line in lines[:6]]
    names = ('nx', 'ny', 'nlfp', 'nxin', 'nyin', 'inpn')
    metadata = dict(zip(names, map(int, values)))
    metadata.update(zip(('west', 'east', 'north', 'south'), map(float, (lines[i].split()[0] for i in range(7, 11)))))
    return metadata, lines[6].strip()


def convert(source: Path, destination: Path, diminfo: Path, direction: str) -> None:
    metadata, _ = read_diminfo(diminfo)
    nx, ny, slots = (metadata[key] for key in ('nx', 'ny', 'inpn'))
    if direction == 'binary-to-netcdf':
        raw = np.memmap(source, dtype='<i4', mode='r', shape=(3, slots, ny, nx))
        write_inpmat(destination, raw[0], raw[1], raw[2].view('<f4'), metadata)
    else:
        x, y, area = read_inpmat(source, nx, ny, slots)
        destination.parent.mkdir(parents=True, exist_ok=True)
        temporary = destination.with_name(destination.name + '.tmp')
        try:
            with temporary.open('wb') as stream:
                for values in (x, y, area.astype('<f4', copy=False)):
                    values.tofile(stream)
            temporary.replace(destination)
        finally:
            temporary.unlink(missing_ok=True)
    print(f'Converted {direction}: {source} -> {destination}')


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('direction', choices=('binary-to-netcdf', 'netcdf-to-binary'))
    parser.add_argument('--input', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--diminfo', type=Path, required=True)
    args = parser.parse_args()
    convert(args.input, args.output, args.diminfo, args.direction)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

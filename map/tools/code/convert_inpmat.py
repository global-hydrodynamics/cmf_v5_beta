#!/usr/bin/env python3
"""Convert the dedicated three-variable INPMAT between NetCDF and Binary."""
from __future__ import annotations

import argparse
from dataclasses import replace
from pathlib import Path

import numpy as np

from mod_map_io import read_inpmat, write_inpmat
try:
    from .map_metadata import read_diminfo_nml, write_diminfo_nml
except ImportError:  # Direct execution from map-local wrappers.
    from map_metadata import read_diminfo_nml, write_diminfo_nml


def read_diminfo(path: Path) -> tuple[dict[str, float | int], str]:
    info = read_diminfo_nml(path)
    metadata = {
        'nx': info.nx, 'ny': info.ny, 'nlfp': info.nlfp,
        'nxin': info.nxin, 'nyin': info.nyin, 'inpn': info.inpn,
        'west': info.west, 'east': info.east, 'north': info.north, 'south': info.south,
    }
    return metadata, info.inpmat_file


def convert(source: Path, destination: Path, diminfo: Path, direction: str) -> None:
    info = read_diminfo_nml(diminfo)
    metadata, paired_name = read_diminfo(diminfo)
    if source.name != paired_name:
        raise ValueError(f'{diminfo} describes {paired_name}, not {source.name}')
    paired_info = replace(info, inpmat_file=destination.name)
    descriptor_output = destination.parent / diminfo.name
    if descriptor_output.exists() and read_diminfo_nml(descriptor_output) != paired_info:
        raise ValueError(f'Conflicting paired metadata already exists: {descriptor_output}')
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
    if not descriptor_output.exists():
        write_diminfo_nml(descriptor_output, paired_info)
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

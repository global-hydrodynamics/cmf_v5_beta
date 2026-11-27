#!/usr/bin/env python3
"""Convert the dedicated three-variable INPMAT between NetCDF and Binary."""
from __future__ import annotations

import argparse
from dataclasses import replace
import os
from pathlib import Path
import stat
import tempfile

import numpy as np

from mod_map_io import read_inpmat, write_inpmat
try:
    from .map_metadata import DimInfo, read_diminfo_nml, write_diminfo_nml
except ImportError:  # Direct execution from map-local wrappers.
    from map_metadata import DimInfo, read_diminfo_nml, write_diminfo_nml


def read_diminfo(path: Path) -> tuple[dict[str, float | int], str]:
    info = read_diminfo_nml(path)
    metadata = {
        'nx': info.nx, 'ny': info.ny, 'nlfp': info.nlfp,
        'nxin': info.nxin, 'nyin': info.nyin, 'inpn': info.inpn,
        'west': info.west, 'east': info.east, 'north': info.north, 'south': info.south,
    }
    return metadata, info.inpmat_file


def write_paired_diminfo(path: Path, info: DimInfo, source: Path) -> bool:
    """Atomically replace the regenerable paired descriptor; return whether it existed."""
    path.parent.mkdir(parents=True, exist_ok=True)
    overwritten = path.exists()
    mode_source = path if overwritten else source
    fd, temporary_name = tempfile.mkstemp(prefix=f'.{path.name}.', suffix='.tmp', dir=path.parent)
    os.close(fd)
    temporary = Path(temporary_name)
    try:
        write_diminfo_nml(temporary, info)
        os.chmod(temporary, stat.S_IMODE(mode_source.stat().st_mode))
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)
    return overwritten


def convert(source: Path, destination: Path, diminfo: Path, direction: str) -> None:
    if source.resolve() == destination.resolve():
        raise ValueError('Source and destination INPMAT paths must be different')
    info = read_diminfo_nml(diminfo)
    metadata, paired_name = read_diminfo(diminfo)
    if source.name != paired_name:
        raise ValueError(f'{diminfo} describes {paired_name}, not {source.name}')
    paired_info = replace(info, inpmat_file=destination.name)
    descriptor_output = destination.parent / diminfo.name
    if descriptor_output.resolve() == diminfo.resolve():
        raise ValueError('Destination DIMINFO path is the source DIMINFO; refusing to overwrite source metadata')
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
    overwritten = write_paired_diminfo(descriptor_output, paired_info, diminfo)
    action = 'Overwrote' if overwritten else 'Generated'
    print(f'{action} paired DIMINFO: {descriptor_output}')
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

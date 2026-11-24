# SPDX-License-Identifier: Apache-2.0
"""Binary map I/O for maintained Python map tools.

Arrays are (record, north-to-south row, west-to-east column), x fastest.
Direct-access records have no markers; map integers/reals are little-endian
int32/float32 unless the caller explicitly requests int16 high-resolution data.
Shell workflows invoke these Python tools directly; output products are replaced on rerun.
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path

import numpy as np


@dataclass(frozen=True)
class Grid:
    nx: int
    ny: int
    nlfp: int
    size: np.float32
    west: np.float32
    east: np.float32
    south: np.float32
    north: np.float32

    @classmethod
    def read(cls, path):
        """Read the eight leading scalar records of params.txt, without comments."""
        values = [line.split()[0] for line in Path(path).read_text().splitlines() if line.strip()][:8]
        return cls(*(int(x) for x in values[:3]), *(np.float32(x) for x in values[3:]))

    def raster(self, path, dtype='<f4', records=1):
        """Map complete records without loading another full-array copy."""
        shape = (records, self.ny, self.nx)
        if Path(path).stat().st_size < int(np.prod(shape)) * np.dtype(dtype).itemsize:
            raise ValueError(f'{path}: incomplete {shape} {dtype} map')
        result = np.memmap(path, dtype=dtype, mode='r', shape=shape)
        return result[0] if records == 1 else result


def write_raster(path, values, dtype):
    """Write a map product, replacing only this tool-owned output file."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('wb') as stream:
        np.asarray(values, dtype=dtype).tofile(stream)


def parser(description, map_default='..'):
    """Keep positional Fortran arguments, with explicit parallel-tool I/O roots."""
    result = argparse.ArgumentParser(description=description)
    result.add_argument('--map-dir', type=Path, default=Path(map_default), help='Read-only input map root; default follows Fortran CWD contract')
    result.add_argument('--output-dir', type=Path, help='Explicit output destination; default follows the Fortran CWD convention; existing outputs are replaced')
    return result


def output_root(args):
    """Return the selected output directory without modifying the source map."""
    return args.output_dir if args.output_dir is not None else args.map_dir

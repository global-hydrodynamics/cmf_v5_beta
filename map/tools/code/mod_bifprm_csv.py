# SPDX-License-Identifier: Apache-2.0
# Parallel port of mod_bifprm_csv.F90; original Fortran authors and license retained.
"""Read named bifprm.csv columns and reconstruct legacy deterministic sort keys.

Shared dependency of the experimental bifurcation/MPI ports. Values use float32
and one-based endpoints exactly as the Fortran reader; row IDs are consecutive.
"""
import csv
from pathlib import Path

import numpy as np


INTEGER_FIELDS = ('pth_id', 'ix', 'iy', 'jx', 'jy', 'ibsn', 'jbsn')
REAL_FIELDS = ('length', 'elevtn', 'depth', 'start_lat', 'start_lon', 'end_lat', 'end_lon')


def read_bifprm_csv(path):
    """Return numeric row dictionaries with widths and the reference whole-line key."""
    with Path(path).open(newline='') as stream:
        reader = csv.DictReader(stream)
        header = reader.fieldnames or []
        if len(header) != len(set(header)):
            raise ValueError('duplicate CSV columns')
        for field in INTEGER_FIELDS + REAL_FIELDS:
            if field not in header:
                raise ValueError(f'missing {field}')
        width_ids = sorted(int(h[6:]) for h in header if h.startswith('width_'))
        if not width_ids or width_ids != list(range(1, max(width_ids) + 1)) or width_ids[-1] > 100:
            raise ValueError('width columns must be consecutive width_1..width_N, N<=100')
        result = []
        for i, row in enumerate(reader, 1):
            values = {name: int(row[name]) for name in INTEGER_FIELDS}
            values.update({name: np.float32(row[name]) for name in REAL_FIELDS})
            if values['pth_id'] != i or None in row:
                raise ValueError('invalid row index/column count')
            widths = np.array([row[f'width_{k}'] for k in width_ids], dtype=np.float32)
            values['widths'] = widths
            integer_part = ''.join(f'{values[k]:8d}' for k in ('ix', 'iy', 'jx', 'jy'))
            real_part = ''.join(f'{x:12.2f}' for x in [values['length'], values['elevtn'], values['depth'], *widths])
            values['sort_line'] = integer_part + real_part + f"{values['start_lat']:10.3f}{values['start_lon']:10.3f}{values['ibsn']:8d}{values['jbsn']:8d}"
            result.append(values)
    return result

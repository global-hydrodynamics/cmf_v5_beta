# SPDX-License-Identifier: Apache-2.0
# Parallel port of mod_bifprm_csv.F90; original Fortran authors and license retained.
"""Read named bifprm.csv fields and reconstruct legacy deterministic sort keys.

The file stores river-channel width separately from overland layers. Values use
float32 and one-based endpoints exactly as the Fortran reader; row IDs are
consecutive.
"""
import csv
import re
from pathlib import Path

import numpy as np


INTEGER_FIELDS = ('pth_id', 'ix', 'iy', 'jx', 'jy', 'ibsn', 'jbsn')
REAL_FIELDS = ('length', 'elevtn', 'depth', 'riv_width', 'start_lat', 'start_lon', 'end_lat', 'end_lon')
OVERLAND_PATTERN = re.compile(r'^ovl_width_(\d+)$')
REQUIRED_FIELDS = INTEGER_FIELDS + REAL_FIELDS


def read_bifprm_csv(path):
    """Return numeric row dictionaries with widths and the reference whole-line key."""
    with Path(path).open(newline='') as stream:
        reader = csv.DictReader(stream)
        raw_header = reader.fieldnames or []
        header = [name.strip() for name in raw_header]
        reader.fieldnames = header
        if not header or len(header) != len(set(header)):
            raise ValueError('missing or duplicate CSV columns')
        missing = [field for field in REQUIRED_FIELDS if field not in header]
        if missing:
            raise ValueError(f'missing required columns: {", ".join(missing)}')

        layer_ids = []
        for name in header:
            match = OVERLAND_PATTERN.fullmatch(name)
            if match:
                if str(int(match.group(1))) != match.group(1):
                    raise ValueError(f'invalid overland width column: {name}')
                layer_ids.append(int(match.group(1)))
        layer_ids.sort()
        if layer_ids != list(range(1, len(layer_ids) + 1)) or len(layer_ids) > 100:
            raise ValueError('overland width columns must be consecutive ovl_width_1..N, N<=100')
        malformed = [name for name in header if name.startswith('ovl_width_') and not OVERLAND_PATTERN.fullmatch(name)]
        if malformed:
            raise ValueError(f'invalid overland width column: {malformed[0]}')

        result = []
        for i, raw_row in enumerate(reader, 1):
            row = {key.strip(): (value.strip() if value is not None else None)
                   for key, value in raw_row.items() if key is not None}
            if None in raw_row or any(row.get(name) in (None, '') for name in REQUIRED_FIELDS):
                raise ValueError(f'invalid row index/column count at row {i}')
            try:
                values = {name: int(row[name]) for name in INTEGER_FIELDS}
                values.update({name: np.float32(row[name]) for name in REAL_FIELDS})
                overland = np.asarray([row[f'ovl_width_{k}'] for k in layer_ids], dtype=np.float32)
            except (TypeError, ValueError) as exc:
                raise ValueError(f'invalid scientific value at row {i}') from exc
            if values['pth_id'] != i:
                raise ValueError('pth_id must match consecutive one-based row order')
            if any(row.get(f'ovl_width_{layer}', '').strip() == '' for layer in layer_ids):
                raise ValueError(f'missing overland width value at row {i}')
            if (not all(np.isfinite(value) for value in values.values() if isinstance(value, np.floating))
                    or not np.isfinite(overland).all()):
                raise ValueError(f'non-finite scientific value at row {i}')
            widths = np.concatenate((np.asarray([values['riv_width']], dtype=np.float32), overland))
            values['ovl_widths'] = overland
            values['widths'] = widths
            integer_part = ''.join(f'{values[k]:8d}' for k in ('ix', 'iy', 'jx', 'jy'))
            real_part = ''.join(f'{x:12.2f}' for x in [values['length'], values['elevtn'], values['depth'], *widths])
            values['sort_line'] = integer_part + real_part + f"{values['start_lat']:10.3f}{values['start_lon']:10.3f}{values['ibsn']:8d}{values['jbsn']:8d}"
            result.append(values)
    return result

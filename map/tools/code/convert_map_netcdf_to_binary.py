#!/usr/bin/env python3
"""Restore a registered individual map NetCDF raster to legacy Binary."""
from __future__ import annotations

import argparse
import os
from pathlib import Path
import tempfile

import numpy as np

try:
    from . import convert_map_binary_to_netcdf as forward
except ImportError:
    import convert_map_binary_to_netcdf as forward


def convert(map_dir: Path, source: Path, output: Path, registry: Path,
            variables: list[str] | None, no_overwrite: bool,
            source_variable: str | None = None,
            reference_binary: str | None = None) -> None:
    """Write registry records in x-fastest, little-endian Fortran order."""
    params = forward.read_params(map_dir)
    nx, ny, nlfp = params[:3]
    definition = forward.standard_binary_filename(output.name)
    registered_rows = forward.registry_rows(registry)
    rows = forward.select_variables(definition, registered_rows, variables, reference_binary)
    all_rows = forward.select_variables(definition, registered_rows, None, reference_binary)
    if len(rows) != len(all_rows):
        raise ValueError('restoring a multi-record Binary requires every registered record')
    if source_variable is not None and len(rows) != 1:
        raise ValueError('--source-variable requires a single-variable map product')
    rows.sort(key=lambda row: int(row.get('record_index') or '1'))
    expected_records = nlfp if rows[0]['dimensions'] == 'NX,NY,NLFP' else len(all_rows)
    expected_shape = (nlfp, ny, nx) if rows[0]['dimensions'] == 'NX,NY,NLFP' else (ny, nx)
    if source.resolve() == output.resolve():
        raise ValueError('input NetCDF and output Binary paths must differ')
    if output.exists() and no_overwrite:
        raise FileExistsError(f'{output} exists; rerun without --no-overwrite to replace it')
    output.parent.mkdir(parents=True, exist_ok=True)

    import netCDF4

    descriptor, name = tempfile.mkstemp(prefix=f'.{output.name}.', suffix='.tmp', dir=output.parent)
    temporary = Path(name)
    try:
        with os.fdopen(descriptor, 'wb') as stream, netCDF4.Dataset(source) as dataset:
            dtype = np.dtype(rows[0]['dtype']).newbyteorder('<')
            for row in rows:
                variable_name = source_variable or row['_individual_name']
                if variable_name not in dataset.variables:
                    raise ValueError(f'{source}: missing registered variable {variable_name}')
                variable = dataset.variables[variable_name]
                variable.set_auto_maskandscale(False)
                if variable.shape != expected_shape:
                    raise ValueError(f'{source}:{variable_name} has shape {variable.shape}; expected {expected_shape}')
                if np.dtype(variable.dtype) != np.dtype(row['dtype']):
                    raise ValueError(f'{source}:{variable_name} type {variable.dtype} differs from registry {row["dtype"]}')
                values = np.asarray(variable[:], dtype=dtype)
                values.tofile(stream)
            expected_bytes = nx * ny * expected_records * dtype.itemsize
            stream.flush()
            if os.fstat(stream.fileno()).st_size != expected_bytes:
                raise RuntimeError(f'{output}: wrote wrong Binary size')
        os.chmod(temporary, 0o644)
        if no_overwrite:
            os.link(temporary, output)
        else:
            os.replace(temporary, output)
    finally:
        temporary.unlink(missing_ok=True)
    print(f'Restored {source} -> {output} ({expected_bytes} bytes)')


def main() -> int:
    root = Path(__file__).resolve().parents[3]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--map-dir', type=Path, required=True, help='map root containing params.nml or legacy params.txt')
    parser.add_argument('--input', type=Path, required=True, help='registered individual NetCDF map')
    parser.add_argument('--output', type=Path, help='Binary destination; default is binary/<input-stem>.bin')
    parser.add_argument('--registry', type=Path, default=root / 'variable_table/map_variables.csv')
    parser.add_argument('--variables', help='optional comma-separated registered variable names')
    parser.add_argument('--source-variable', help='NetCDF variable name when it differs from the registered map variable')
    parser.add_argument('--reference-binary', help='exact registered Binary filename describing the input, independent of its custom name')
    parser.add_argument('--no-overwrite', action='store_true', help='keep an existing Binary file')
    args = parser.parse_args()
    map_dir, source = args.map_dir.resolve(), args.input.resolve()
    output = args.output or map_dir / 'binary' / f'{source.stem}.bin'
    output = output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    try:
        convert(map_dir, source, output, args.registry.resolve(),
                args.variables.split(',') if args.variables else None, args.no_overwrite,
                args.source_variable, args.reference_binary)
    except (OSError, ValueError, RuntimeError) as error:
        parser.exit(1, f'ERROR: {error}\n')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

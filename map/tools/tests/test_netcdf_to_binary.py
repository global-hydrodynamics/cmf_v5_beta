"""Check NetCDF-to-Binary record layouts against the maintained map registry."""
import hashlib
import tempfile
import unittest
from pathlib import Path

import netCDF4
import numpy as np

from map.tools.code import convert_map_netcdf_to_binary as converter

ROOT = Path(__file__).resolve().parents[3]
REGISTRY = ROOT / 'variable_table/map_variables.csv'


class NetCDFToBinaryTests(unittest.TestCase):
    def test_layered_fldhgt_restores_every_layer_as_binary_records(self):
        with tempfile.TemporaryDirectory() as tmp:
            nx, ny, nlfp = 4, 3, 5
            map_dir = Path(tmp) / 'map'
            map_dir.mkdir()
            (map_dir / 'params.txt').write_text(
                f'{nx}\n{ny}\n{nlfp}\n0.25\n90\n91\n5\n5.75\n', encoding='ascii'
            )
            source = map_dir / 'fldhgt.nc'
            values = np.arange(nlfp * ny * nx, dtype='<f4').reshape(nlfp, ny, nx)
            values[:, 0, 0] = -9999
            with netCDF4.Dataset(source, 'w') as dataset:
                dataset.createDimension('layer', nlfp)
                dataset.createDimension('lat', ny)
                dataset.createDimension('lon', nx)
                variable = dataset.createVariable(
                    'fldhgt', 'f4', ('layer', 'lat', 'lon'), fill_value=-9999
                )
                variable.set_auto_maskandscale(False)
                variable[:] = values

            source_digest = hashlib.sha256(source.read_bytes()).digest()
            output = map_dir / 'binary/fldhgt.bin'
            converter.convert(map_dir, source, output, REGISTRY, None, False)

            self.assertEqual(output.stat().st_size, nx * ny * nlfp * 4)
            self.assertEqual(output.read_bytes(), values.tobytes(order='C'))
            self.assertEqual(hashlib.sha256(source.read_bytes()).digest(), source_digest)

    def test_nextxy_noedge_uses_its_registered_variable_names(self):
        with tempfile.TemporaryDirectory() as tmp:
            nx, ny = 4, 3
            map_dir = Path(tmp) / 'map'
            map_dir.mkdir()
            (map_dir / 'params.txt').write_text(
                f'{nx}\n{ny}\n1\n0.25\n90\n91\n5\n5.75\n', encoding='ascii'
            )
            source = map_dir / 'nextxy_noedge.nc'
            x = np.arange(nx * ny, dtype='<i4').reshape(ny, nx)
            y = (x + 100).astype('<i4')
            with netCDF4.Dataset(source, 'w') as dataset:
                dataset.createDimension('lat', ny)
                dataset.createDimension('lon', nx)
                for name, values in (('nextx_noedge', x), ('nexty_noedge', y)):
                    variable = dataset.createVariable(name, 'i4', ('lat', 'lon'), fill_value=-9999)
                    variable.set_auto_maskandscale(False)
                    variable[:] = values

            output = map_dir / 'binary/nextxy_noedge.bin'
            converter.convert(map_dir, source, output, REGISTRY, None, False)

            self.assertEqual(output.read_bytes(), x.tobytes(order='C') + y.tobytes(order='C'))

"""Small synthetic map fixtures; no distributed data are copied into tests."""
import sys
from pathlib import Path

import numpy as np
import pytest
from netCDF4 import Dataset

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


@pytest.fixture
def map_dir(tmp_path):
    (tmp_path/'params.txt').write_text('4 NX\n3 NY\n2 NLFP\n1 spacing\n10 west\n14 east\n20 south\n23 north\n')
    values = np.array([[1e6, 2e6, -9999, 0], [4e6, 5e6, 6e6, 7e6], [8e6, 9e6, 10e6, 11e6]], dtype='<f4')
    values.tofile(tmp_path/'uparea.bin')
    return tmp_path


def write_nc(root, name, values, units='m2', reverse_lat=False, reverse_lon=False, transpose=False, shift=0):
    path = root/'netcdf'/f'{name}.nc'
    path.parent.mkdir(exist_ok=True)
    values = np.ma.asarray(values)
    with Dataset(path, 'w') as ds:
        ds.createDimension('lon', 4); ds.createDimension('lat', 3)
        lon = np.arange(4)+10.5+shift
        lat = 22.5-np.arange(3)
        ds.createVariable('lon', 'f8', ('lon',))[:] = lon[::-1] if reverse_lon else lon
        ds.createVariable('lat', 'f8', ('lat',))[:] = lat[::-1] if reverse_lat else lat
        data = values[::-1] if reverse_lat else values
        data = data[:, ::-1] if reverse_lon else data
        var = ds.createVariable(name, values.dtype, ('lon','lat') if transpose else ('lat','lon'), fill_value=-9999)
        var.units = units
        var[:] = data.T if transpose else data
    return path


def write_network(root):
    # row 0: local, flexible, terminal, out-of-map. row 1: crossing
    # flexible segment from col 0 to col 3; row 2: mixed and self link.
    x = np.full((3,4), -9999, dtype='<i4')
    y = x.copy()
    x[0], y[0] = [2,4,-9,8], [1,3,-9,1]
    x[1,0], y[1,0] = 4,2
    x[2,0], y[2,0] = 1,-10
    x[2,1], y[2,1] = 2,3
    np.stack([x,y]).tofile(root/'nextxy.bin')
    return x, y

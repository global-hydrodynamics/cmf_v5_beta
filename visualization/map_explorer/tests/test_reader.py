"""Prevent CaMa-Flood orientation, dtype, missing-value and grid-contract errors."""
import numpy as np
import pytest

from conftest import write_nc, write_network
from map_reader import Geometry, MapReader
from map_layers import make_layer
from netCDF4 import Dataset


def test_geometry_and_fortran_indices(map_dir):
    g = Geometry.read(map_dir/'params.txt')
    assert (g.nx,g.ny,g.layers) == (4,3,2)
    np.testing.assert_array_equal(g.lon, [10.5,11.5,12.5,13.5])
    np.testing.assert_array_equal(g.lat, [22.5,21.5,20.5])
    assert g.cell(10.5,22.5) == (0,0)
    assert g.cell(14,22) is None
    assert g.cell(10,20) is None


def test_inconsistent_params(map_dir):
    path = map_dir/'params.txt'
    path.write_text(path.read_text().replace('14 east','15 east'))
    with pytest.raises(ValueError, match='disagree'):
        MapReader(map_dir)


def test_binary_x_fastest_and_two_records(map_dir):
    x,y = write_network(map_dir)
    r = MapReader(map_dir)
    values = r.read('uparea')
    assert values[1,0] == 4e6
    assert values[0,3] == 0
    assert values.mask[0,2]
    nx,ny = r.read_network()
    np.testing.assert_array_equal(nx.filled(-9999),x)
    np.testing.assert_array_equal(ny.filled(-9999),y)


@pytest.mark.parametrize('reverse_lat,reverse_lon,transpose', [(False,False,False),(True,False,False),(False,True,True),(True,True,True)])
def test_netcdf_normalization(map_dir, reverse_lat, reverse_lon, transpose):
    expected = np.arange(12,dtype='f4').reshape(3,4)-4
    write_nc(map_dir,'elevtn',expected,units='m',reverse_lat=reverse_lat,reverse_lon=reverse_lon,transpose=transpose)
    r = MapReader(map_dir)
    np.testing.assert_array_equal(r.read('elevtn'),expected)
    assert r.read_cell('elevtn',0,1) == -3
    assert r.read_cell('elevtn',2,3) == 7
    assert not r.read('elevtn').mask.any()  # Negative/zero elevations are real.


def test_bad_netcdf_grid_falls_back_with_message(map_dir):
    write_nc(map_dir,'uparea',np.ones((3,4),dtype='f4'),shift=.25)
    r = MapReader(map_dir)
    assert not r.sources['uparea'].netcdf
    assert any('cell centers' in m for m in r.messages)


def test_invalid_binary_size_and_optional_variables(map_dir):
    (map_dir/'elevtn.bin').write_bytes(b'bad')
    (map_dir/'unknown.bin').write_bytes(bytes(48))
    r = MapReader(map_dir)
    assert list(r.sources) == ['uparea']
    assert not r.network_sources
    assert len(r.messages) == 2
    assert not r._cache


def test_prefer_netcdf_and_attribute_fill(map_dir):
    expected = np.arange(12,dtype='f4').reshape(3,4)
    expected[0,0] = -9999
    write_nc(map_dir,'uparea',expected)
    r = MapReader(map_dir)
    assert r.sources['uparea'].netcdf
    assert r.read('uparea').mask[0,0]
    assert r.read_cell('uparea',0,0) is np.ma.masked


def test_area_units_log_and_categories_preserve_values(map_dir):
    np.array([[0,1,20,100],[1,1,20,-9999],[100,20,1,0]],dtype='<i4').tofile(map_dir/'basin.bin')
    r = MapReader(map_dir)
    display = make_layer(r,'uparea')
    assert display.image[0,0] == 1
    assert np.isnan(display.image[0,3])
    assert r.read('uparea')[0,3] == 0
    categories = make_layer(r,'basin',scale='log')
    assert not categories.logarithmic
    np.testing.assert_array_equal(categories.categories,[0,1,20,100])
    assert r.read('basin')[0,3] == 100
    assert categories.image[0,3] == 3


def test_uncached_inspection_does_not_load_entire_variables(map_dir):
    np.ones((3,4),dtype='<f4').tofile(map_dir/'elevtn.bin')
    r = MapReader(map_dir)
    result = r.inspect(10.5,22.5)
    assert result['ix (1-based)'] == result['iy (1-based)'] == 1
    assert result['uparea [m2]'] == 1e6
    assert not r._cache


def test_wrong_dtype_units_and_noninteger_categories(map_dir):
    write_nc(map_dir,'elevtn',np.ones((3,4),dtype='i4'),units='m')
    write_nc(map_dir,'ctmare',np.ones((3,4),dtype='f4'),units='km2')
    r=MapReader(map_dir)
    assert 'elevtn' not in r.sources and 'ctmare' not in r.sources
    assert any('expected' in m for m in r.messages)


def test_attribute_fill_and_contract_sentinel_are_both_masked(map_dir):
    path=write_nc(map_dir,'elevtn',np.zeros((3,4),dtype='f4'),units='m')
    with Dataset(path,'a') as ds:
        var=ds.variables['elevtn']
        var.missing_value=np.float32(1e20)
        var[0,:]=[-9999,1e20,-2,0]
    r=MapReader(map_dir)
    np.testing.assert_array_equal(r.read('elevtn').mask[0],[True,True,False,False])
    assert r.read_cell('elevtn',0,2) == -2


def test_bad_variable_dimensions_and_coordinate_units(map_dir):
    path=write_nc(map_dir,'ctmare',np.ones((3,4),dtype='f4'))
    with Dataset(path,'a') as ds:
        ds.variables['lon'].units='radians'
    r=MapReader(map_dir)
    assert 'ctmare' not in r.sources
    assert any('geographic degrees' in message for message in r.messages)
    path=map_dir/'netcdf'/'elevtn.nc'
    with Dataset(path,'w') as ds:
        ds.createDimension('lon',4);ds.createDimension('lat',3);ds.createDimension('layer',1)
        ds.createVariable('lon','f8',('lon',))[:]=np.arange(4)+10.5
        ds.createVariable('lat','f8',('lat',))[:]=22.5-np.arange(3)
        var=ds.createVariable('elevtn','f4',('layer','lat','lon'))
        var.units='m'
    r=MapReader(map_dir)
    assert 'elevtn' not in r.sources
    assert any('exactly the lon' in message for message in r.messages)

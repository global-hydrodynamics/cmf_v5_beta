"""Small synthetic map fixtures; no distributed data are copied into tests."""
import sys
from pathlib import Path

import numpy as np
import pytest
from netCDF4 import Dataset

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "code"))


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


def native_assignments(tile):
    """Small-map test oracle only; large datasets require representative windows."""
    if "catmxy" in tile.cog:
        g = tile.geometry
        if g.nx*g.ny > 5_000_000:
            raise ValueError("Use native windows for large-map test oracles")
        return np.concatenate([tile.sample("catmxy",np.arange(r,min(g.ny,r+64)),np.arange(g.nx))
                               for r in range(0,g.ny,64)],axis=1)
    path = tile.files["catmxy"]
    if path.suffix != ".nc":
        return np.asarray(tile.mmap("catmxy"))
    with Dataset(path,"r") as ds:
        ds.set_auto_maskandscale(False)
        rows,cols = np.argsort(-ds["lat"][:]),np.argsort(ds["lon"][:])
        values=[]
        for key in ("catmxx","catmyy"):
            data=ds[key][:]
            if ds[key].dimensions == ("lon","lat"):data=data.T
            values.append(data[np.ix_(rows,cols)])
        return np.stack(values)


def install_test_cogs(root):
    """Promote tiny synthetic Binary fixtures to self-contained numeric COGs only.

    Never used with real datasets: both temporary-root and pixel-budget guards
    prevent an accidental scientific-map conversion during regression setup.
    """
    import tempfile
    import rasterio
    from rasterio.shutil import copy as raster_copy
    from rasterio.enums import Resampling
    from rasterio.transform import from_origin
    from hires import discover_tiles
    root=Path(root).resolve()
    assert Path(tempfile.gettempdir()).resolve() in root.parents
    for tile in discover_tiles(root,[]).values():
        g=tile.geometry
        assert g.nx*g.ny <= 50000
        for name in list(tile.files):
            source=tile.directory/f'{tile.prefix}.{name}.bin'
            if not source.is_file():continue
            dtype,records=('<i2',2) if name=='catmxy' else ('i1',1) if name in ('visual','catmz100') else ('<f4',1)
            values=np.fromfile(source,dtype=dtype).reshape(records,g.ny,g.nx)
            names=['catmxx','catmyy'] if name=='catmxy' else [name]
            units='km2' if name=='uparea' else 'code' if name=='visual' else '1' if values.dtype.kind=='i' else 'm'
            target=root/'COG'/Path(tile.key).parent/f'{tile.prefix}.{name}.tif'
            target.parent.mkdir(parents=True,exist_ok=True)
            stage=target.with_suffix('.stage.tif')
            with rasterio.open(stage,'w',driver='GTiff',width=g.nx,height=g.ny,count=records,dtype=values.dtype,
                               crs='EPSG:4326',transform=from_origin(g.west,g.north,g.resolution,g.resolution),
                               nodata=-9 if values.dtype==np.dtype('int8') else -9999,
                               tiled=True,blockxsize=128,blockysize=128) as ds:
                ds.write(values);ds.update_tags(source_file=source.with_suffix('.nc').name)
                for i,key in enumerate(names,1):ds.update_tags(i,source_variable=key,units=units)
                ds.build_overviews([2],Resampling.nearest if values.dtype.kind=='i' else Resampling.average)
            raster_copy(stage,target,driver='COG',BLOCKSIZE=128,COMPRESS='DEFLATE',OVERVIEWS='FORCE_USE_EXISTING')
            stage.unlink()

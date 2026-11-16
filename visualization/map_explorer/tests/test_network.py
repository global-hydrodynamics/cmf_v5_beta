"""Stored connectivity, endpoint codes, flexible links and viewport crossings."""
import numpy as np

from conftest import write_network
from map_reader import MapReader
from river_network import RiverNetwork, intersects


def test_stored_links_and_terminal_codes(map_dir):
    write_network(map_dir)
    n=RiverNetwork(MapReader(map_dir))
    assert len(n.rows) == 3
    np.testing.assert_array_equal(n.flexible,[False,True,True])
    assert n.inspect(0,0)['downstream longitude'] == 11.5
    assert n.inspect(0,1)['downstream status'] == 'flexible'
    assert 'terminal' in n.inspect(0,2)['downstream status']
    assert 'outside' in n.inspect(0,3)['downstream status']
    assert 'missing' in n.inspect(1,1)['downstream status']
    assert 'mixed' in n.inspect(2,0)['downstream status']
    assert 'self' in n.inspect(2,1)['downstream status']
    assert n.counts['out_of_map'] == n.counts['mixed_codes'] == n.counts['self_links'] == 1


def test_viewport_crossing_both_endpoints_outside(map_dir):
    write_network(map_dir)
    n=RiverNetwork(MapReader(map_dir))
    ids=n.visible((11.8,12.2,21.4,21.6))
    assert len(ids) == 1
    assert n.x0[ids[0]] == 10.5 and n.x1[ids[0]] == 13.5
    result=intersects(np.array([0.,0.]),np.array([0.,2.]),np.array([4.,4.]),np.array([0.,2.]),(1,3,-1,1))
    np.testing.assert_array_equal(result,[True,False])


def test_periodic_global_seam_does_not_span_globe(tmp_path):
    (tmp_path/'params.txt').write_text('360\n1\n1\n1\n-180\n180\n0\n1\n')
    np.ones((1,360),dtype='<f4').tofile(tmp_path/'uparea.bin')
    x=np.full((1,360),-9999,dtype='<i4');y=x.copy()
    x[0,0]=360;y[0,0]=1
    np.stack([x,y]).tofile(tmp_path/'nextxy.bin')
    n=RiverNetwork(MapReader(tmp_path))
    assert not n.flexible[0]
    assert len(n.x0) == 2
    assert np.all(np.abs(n.x1-n.x0) <= .5)
    assert not len(n.visible((-1,1,0,1)))
    assert len(n.visible((-180,-179,0,1))) == 1

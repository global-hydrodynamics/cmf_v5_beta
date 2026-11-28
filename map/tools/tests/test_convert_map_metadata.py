"""Focused checks for the explicit bidirectional map metadata converters."""
import csv
from pathlib import Path
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[3]
CODE = ROOT / 'map' / 'tools' / 'code'
sys.path.insert(0, str(CODE))

import convert_map_metadata as converter
from map_metadata import (DimInfo, MapGeometry, read_diminfo_nml, read_nml_values,
                          render_diminfo_nml, render_nml, write_diminfo_nml)


def test_geometry_and_diminfo_convert_both_directions_and_overwrite(tmp_path):
    (tmp_path / 'params.txt').write_text('80\n120\n10\n0.25\n90\n110\n5\n35\n')
    (tmp_path / 'diminfo_test.txt').write_text(
        '80\n120\n10\n360\n180\n4\ninpmat_test.nc\n90\n110\n35\n5\n')
    original_params = (tmp_path / 'params.txt').read_text()
    original_diminfo = (tmp_path / 'diminfo_test.txt').read_text()
    (tmp_path / 'params.nml').write_text('old destination')
    result = converter._convert_families(tmp_path, 'txt2meta')
    assert {item.destination.name for item in result} == {'params.nml'}
    assert read_nml_values(tmp_path / 'params.nml') == MapGeometry(80, 120, 10, .25, 90, 110, 5, 35)
    assert (tmp_path / 'params.txt').read_text() == original_params
    assert (tmp_path / 'diminfo_test.txt').read_text() == original_diminfo
    assert not (tmp_path / 'diminfo_test.nml').exists()

    write_diminfo_nml(tmp_path / 'diminfo_test.nml', DimInfo(
        80, 120, 10, 90, 110, 35, 5, 'inpmat_test.nc', 360, 180, 4,
        -180, 180, 90, -90, 'NtoS'))
    converter._convert_families(tmp_path, 'meta2txt')
    assert len((tmp_path / 'params.txt').read_text().splitlines()) == 8
    assert len((tmp_path / 'diminfo_test.txt').read_text().splitlines()) == 11
    legacy_values = [line.split()[0] for line in (tmp_path / 'diminfo_test.txt').read_text().splitlines()]
    assert legacy_values == ['80', '120', '10', '360', '180', '4', 'inpmat_test.nc',
                             '90.0', '110.0', '35.0', '5.0']


def test_diminfo_text_is_excluded_from_txt_to_meta_conversion(tmp_path):
    source = tmp_path / 'diminfo_test.txt'
    destination = tmp_path / 'diminfo_test.nml'
    source.write_text('80\n120\n10\n360\n180\n4\ninpmat_test.nc\n90\n110\n35\n5\n')
    destination.write_text('authoritative generated metadata')
    result = converter._convert_families(tmp_path, 'txt2meta')
    assert result == []
    assert source.is_file()
    assert destination.read_text() == 'authoritative generated metadata'


def test_location_inventory_is_converted_but_binary_tree_is_untouched(tmp_path):
    resolution = tmp_path / '1min'
    resolution.mkdir()
    resolution.joinpath('location.txt').write_text(
        '1 narea\niarea carea west east south north nx ny csize\n'
        '1 tile 0 1 0 1 60 60 0.016666666666666666\n')
    binary = tmp_path / 'binary' / '1min'
    binary.mkdir(parents=True)
    binary.joinpath('location.txt').write_text('must remain unchanged')
    converter._convert_families(tmp_path, 'txt2meta')
    assert (resolution / 'location.csv').is_file()
    assert binary.joinpath('location.txt').read_text() == 'must remain unchanged'


def test_bifori_round_trip_preserves_rows_and_source(tmp_path):
    (tmp_path / 'bifori.txt').write_text('2 2\n1 2 3 4 5.5 6.5 7.5 8.5 33.1 94.2\n'
                                         '3 4 5 6 9.5 10.5 11.5 12.5 30.1 95.2\n')
    source = (tmp_path / 'bifori.txt').read_text()
    converter._convert_families(tmp_path, 'txt2meta')
    with (tmp_path / 'bifori.csv').open(newline='') as stream:
        rows = list(csv.DictReader(stream))
    assert rows[1]['path_id'] == '2'
    assert rows[1]['ovl_width_1'] == '12.5'
    converter._convert_families(tmp_path, 'meta2txt')
    assert (tmp_path / 'bifori.txt').read_text().splitlines()[0] == '     2    2'
    assert (tmp_path / 'bifori.txt').read_text() != source  # output uses canonical spacing


def test_bifprm_reverse_omits_v5_outlet_coordinates_and_preserves_v4_layers(
        tmp_path, monkeypatch, capsys):
    path = tmp_path / 'bifprm.csv'
    path.write_text(
        'pth_id,ix, iy,jx, jy, length, elevtn, depth, riv_width, ovl_width_1, ovl_width_2,'
        ' start_lat, start_lon, end_lat, end_lon, ibsn, jbsn\n'
        '1,1,2,3,4,5,6,0.5,7,8,9,10,11,12,13,14,15\n')
    original = path.read_bytes()
    monkeypatch.setattr(sys, 'argv', ['convert_map_metadata.py', 'meta2txt', str(tmp_path)])

    assert converter.main() == 0

    output = capsys.readouterr().out
    lines = (tmp_path / 'bifprm.txt').read_text().splitlines()
    assert 'omitted v5-only columns: end_lat, end_lon' in output
    assert path.read_bytes() == original
    assert lines[0].split() == ['1', '3']
    values = lines[1].split()
    assert len(values) == 14
    assert values == ['1', '2', '3', '4', '5', '6', '0.5', '7', '8', '9',
                      '10', '11', '14', '15']
    # The v4 reader consumes indices, length/elevation/depth, then width layers;
    # channel is first, overland layers follow in their numbered order.
    v4_reader_fields = values[:4 + 3 + 3]
    assert v4_reader_fields[-3:] == ['7', '8', '9']


@pytest.mark.parametrize('kind', tuple(converter.ALLOCATION_SCHEMAS))
def test_allocation_fixed_width_round_trip(kind, tmp_path):
    fields = converter.ALLOCATION_SCHEMAS[kind]
    layout = converter.ALLOCATION_LAYOUTS[kind]
    integer_fields = {'ID', 'Type', 'ix', 'iy', 'ix1', 'iy1', 'ix2', 'iy2', 'year'}
    values = {name: ('Dam name' if name == 'damname' else 'River name' if name == 'rivname'
                     else '1' if name in integer_fields else '1.25') for name in fields}
    line = []
    iterator = iter(fields)
    for descriptor in layout:
        if descriptor[0] == 'x':
            line.append(' ' * descriptor[1])
        else:
            line.append(converter._fmt_allocation(values[next(iterator)], descriptor, tmp_path / 'x'))
    (tmp_path / f'{kind}.txt').write_text('legacy heading\n' + ''.join(line) + '\n')
    converter._convert_families(tmp_path, 'txt2meta')
    assert (tmp_path / f'{kind}.csv').is_file()
    output, count = converter._allocation_csv_to_txt(tmp_path / f'{kind}.csv', kind)
    assert count == 1
    (tmp_path / f'{kind}.txt').write_text(output)
    assert converter._parse_allocation_txt(tmp_path / f'{kind}.txt', kind)[0]['ID'] == '1'


def test_failure_does_not_replace_destination_or_delete_source(tmp_path):
    source = tmp_path / 'params.txt'
    source.write_text('bad\n')
    destination = tmp_path / 'params.nml'
    destination.write_text('keep me')
    with pytest.raises(RuntimeError):
        converter._convert_families(tmp_path, 'txt2meta')
    assert source.exists()
    assert destination.read_text() == 'keep me'


def test_missing_sources_are_skipped(tmp_path):
    assert converter._convert_families(tmp_path, 'txt2meta') == []


@pytest.mark.parametrize('script', ('s31-txt2meta.sh', 's32-meta2txt.sh'))
def test_shell_entry_points_do_not_accept_options(script):
    path = ROOT / 'map' / 'tools' / 'script_format_conv' / script
    result = subprocess.run(['sh', str(path), '--help'], capture_output=True, text=True, check=False)
    assert result.returncode == 2
    assert result.stderr.startswith('Usage:')

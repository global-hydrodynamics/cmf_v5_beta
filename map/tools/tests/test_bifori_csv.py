"""Checks for the FLOW bifurcation-source CSV contract and Mekong migration."""
import csv
from pathlib import Path
import subprocess
import sys

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[3]
CODE = ROOT / 'map' / 'tools' / 'code'
sys.path.insert(0, str(CODE))

from mod_bifori_csv import crop_bifori_records, read_bifori_csv, write_bifori_csv


SAMPLE = ROOT / 'map' / 'mekong_15min'


def test_mekong_source_csv_preserves_all_legacy_rows_and_values():
    table = read_bifori_csv(SAMPLE / 'bifori.csv')
    legacy_rows = (SAMPLE / 'bifori.txt').read_text(encoding='utf-8').splitlines()
    npath, nwidth = map(int, legacy_rows[0].split()[:2])

    assert npath == len(table.rows) == 687
    assert nwidth == table.width_count == 21
    assert table.overland_fields == tuple(f'ovl_width_{i}' for i in range(1, 21))

    for path_id, (legacy, row) in enumerate(zip(legacy_rows[1:], table.rows), 1):
        values = legacy.split()
        assert int(row['path_id']) == path_id
        assert [row[name] for name in ('ix', 'iy', 'jx', 'jy')] == values[:4]
        assert row['length'] == values[4]
        assert row['elevtn'] == values[5]
        assert row['riv_width'] == values[6]
        assert [row[name] for name in table.overland_fields] == values[7:27]
        assert row['start_lat'] == values[-2]
        assert row['start_lon'] == values[-1]


def test_csv_reader_uses_names_and_preserves_extra_columns(tmp_path):
    path = tmp_path / 'bifori.csv'
    path.write_text(
        'ovl_width_1, start_lon, path_id, jx, iy, length, diagnostic, ix, jy, elevtn, '
        'riv_width, start_lat\n'
        ' 2.5, 94.625, 41, 18, 6, 36131.08, retained, 19, 6, 4574.60, 0.00, 33.625\n',
        encoding='utf-8',
    )
    table = read_bifori_csv(path)
    assert table.rows[0]['path_id'] == '41'
    assert table.rows[0]['diagnostic'] == 'retained'
    assert table.rows[0]['riv_width'] == '0.00'
    assert table.rows[0]['ovl_width_1'] == '2.5'


def test_csv_reader_accepts_channel_only_and_aligned_roundtrip(tmp_path):
    source = tmp_path / 'source.csv'
    source.write_text(
        'path_id,ix,iy,jx,jy,length,elevtn,riv_width,start_lat,start_lon\n'
        '7,1,2,3,4,5.00,6.00,0.0,10.000,20.000\n', encoding='utf-8')
    table = read_bifori_csv(source)
    assert table.width_count == 1
    target = tmp_path / 'regional' / 'bifori.csv'
    write_bifori_csv(target, table.fields, list(table.rows))
    reread = read_bifori_csv(target)
    assert reread.fields == table.fields
    assert reread.rows == table.rows


def test_regional_crop_shifts_endpoints_and_preserves_ids_and_extra_fields(tmp_path):
    rows = [
        {'path_id': '41', 'ix': '3', 'iy': '3', 'jx': '4', 'jy': '4',
         'length': '5.00', 'elevtn': '6.00', 'riv_width': '7.0',
         'start_lat': '10.0', 'start_lon': '20.0', 'source_tag': 'keep, with comma'},
        {'path_id': '42', 'ix': '2', 'iy': '2', 'jx': '3', 'jy': '3',
         'length': '5.00', 'elevtn': '6.00', 'riv_width': '7.0',
         'start_lat': '10.0', 'start_lon': '20.0', 'source_tag': 'edge'},
        {'path_id': '43', 'ix': '7', 'iy': '3', 'jx': '8', 'jy': '4',
         'length': '5.00', 'elevtn': '6.00', 'riv_width': '7.0',
         'start_lat': '10.0', 'start_lon': '20.0', 'source_tag': 'outside'},
    ]
    nextx = np.ones((5, 5), dtype=np.int32)
    nextx[0, 0] = -9999
    cropped = crop_bifori_records(rows, nextx, nx=6, ny=6, dx=1, dy=1)
    assert len(cropped) == 1
    assert cropped[0]['path_id'] == '41'
    assert (cropped[0]['ix'], cropped[0]['iy'], cropped[0]['jx'], cropped[0]['jy']) == (
        '2', '2', '3', '3')
    assert cropped[0]['source_tag'] == 'keep, with comma'
    target = tmp_path / 'bifori.csv'
    write_bifori_csv(target, tuple(cropped[0]), cropped)
    assert read_bifori_csv(target).rows[0]['source_tag'] == 'keep, with comma'


@pytest.mark.parametrize(
    'header,row,match',
    [
        ('path_id,ix,iy,jx,jy,length,elevtn,riv_width,start_lat',
         '1,1,2,3,4,5,6,0,10', 'missing required columns'),
        ('path_id,ix,iy,jx,jy,length,elevtn,riv_width,ovl_width_2,start_lat,start_lon',
         '1,1,2,3,4,5,6,0,1,10,20', 'consecutive'),
        ('path_id,ix,iy,jx,jy,length,elevtn,riv_width,ovl_width_1,ovl_width_1,start_lat,start_lon',
         '1,1,2,3,4,5,6,0,1,2,10,20', 'duplicate'),
        ('path_id,ix,iy,jx,jy,length,elevtn,riv_width,start_lat,start_lon',
     '1,1,2,3,4,5,not-a-width,not-a-width,10,20', 'invalid scientific value'),
    ],
)
def test_csv_reader_rejects_invalid_contract(tmp_path, header, row, match):
    path = tmp_path / 'invalid.csv'
    path.write_text(header + '\n' + row + '\n', encoding='utf-8')
    with pytest.raises(ValueError, match=match):
        read_bifori_csv(path)


def test_mekong_generator_reproduces_existing_bifprm_for_biflayer_five(tmp_path):
    pytest.importorskip('netCDF4')
    pytest.importorskip('f90nml')
    output = tmp_path / 'bifprm.csv'
    command = [
        sys.executable, str(CODE / 'param_bif_set_params.py'),
        str(SAMPLE / 'rivhgt.nc'), str(output), '5',
        str(SAMPLE / 'diminfo_test-1deg.nml'), '--map-dir', str(SAMPLE),
    ]
    result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, check=False)
    assert result.returncode == 0, result.stdout + result.stderr

    with output.open(newline='', encoding='utf-8') as stream:
        generated = list(csv.DictReader(stream, skipinitialspace=True))
    with (SAMPLE / 'bifprm.csv').open(newline='', encoding='utf-8') as stream:
        expected = list(csv.DictReader(stream, skipinitialspace=True))
    assert len(generated) == len(expected) == 382
    assert generated[0]['riv_width'].strip() == expected[0]['riv_width'].strip()
    assert [name for name in generated[0] if name.startswith('ovl_width_')] == [
        f'ovl_width_{i}' for i in range(1, 5)
    ]
    for actual, reference in zip(generated, expected):
        assert {key: value.strip() for key, value in actual.items()} == {
            key: value.strip() for key, value in reference.items()
        }

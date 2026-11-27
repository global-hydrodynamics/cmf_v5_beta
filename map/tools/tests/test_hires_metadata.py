"""Contract tests for standard and temporary legacy high-resolution metadata."""
from pathlib import Path

import pytest

from map.tools.code.hires_metadata import (
    LocationArea,
    read_location_csv,
    read_location_txt,
    write_location_csv,
    write_location_txt,
)


AREAS = [
    LocationArea(1, 'n00w180', -180, -150, 0, 30, 7200, 7200, 1 / 240),
    LocationArea(25, 'n00w120', -120, -90, 0, 30, 7200, 7200, 1 / 240),
]


def test_aligned_csv_roundtrip_strips_fields_and_keeps_sparse_tile_ids(tmp_path):
    path = tmp_path / 'location.csv'
    write_location_csv(path, AREAS)

    lines = path.read_text().splitlines()
    assert len(lines) == 3
    comma_positions = [[index for index, char in enumerate(line) if char == ','] for line in lines]
    assert all(positions == comma_positions[0] for positions in comma_positions[1:])
    assert 'narea' not in lines[0].lower()
    assert read_location_csv(path) == AREAS


def test_csv_with_padded_header_and_values_is_standard_csv(tmp_path):
    path = tmp_path / 'location.csv'
    path.write_text(
        'iarea,carea  , west, east, south, north, nx, ny, csize\n'
        '    1,n00w180  , -180, -150, 0, 30, 7200, 7200,0.004166666666666667\n',
    )

    area, = read_location_csv(path)
    assert area.iarea == 1
    assert area.carea == 'n00w180'
    assert area.west == -180


def test_csv_rejects_invalid_header_duplicate_ids_and_inconsistent_geometry(tmp_path):
    path = tmp_path / 'location.csv'
    path.write_text('narea\n1\n')
    with pytest.raises(ValueError, match='header'):
        read_location_csv(path)

    path.write_text(
        'iarea,carea,west,east,south,north,nx,ny,csize\n'
        '1,n00w180,-180,-150,0,30,7200,7200,0.004166666666666667\n'
        '1,n00w120,-120,-90,0,30,7200,7200,0.004166666666666667\n'
    )
    with pytest.raises(ValueError, match='duplicate iarea'):
        read_location_csv(path)

    with pytest.raises(ValueError, match='extent and csize'):
        write_location_csv(path, [LocationArea(1, 'bad', 0, 2, 0, 1, 2, 1, .25)])


def test_explicit_legacy_text_reader_and_writer_preserve_geometry(tmp_path):
    path = tmp_path / 'location.txt'
    write_location_txt(path, AREAS)

    assert read_location_txt(path) == AREAS


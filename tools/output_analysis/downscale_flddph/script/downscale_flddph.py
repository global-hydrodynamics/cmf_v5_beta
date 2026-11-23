#!/usr/bin/env python3
"""Port the tributary-aware CaMa-Flood flood-depth downscaler to Python."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from netCDF4 import Dataset
import numpy as np

FILL_VALUE = np.float32(-9999.0)
PERMANENT_WATER_DEPTH = np.float32(0.1)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True, help="2D flddph NetCDF, or a one-record time series")
    parser.add_argument("--map-dir", type=Path, required=True, help="CaMa-Flood coarse river map directory")
    parser.add_argument("--resolution", required=True, help="High-resolution map directory/tag, for example 1min")
    parser.add_argument("--west", type=float, required=True)
    parser.add_argument("--east", type=float, required=True)
    parser.add_argument("--south", type=float, required=True)
    parser.add_argument("--north", type=float, required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def read_map_geometry(path: Path) -> tuple[int, int, float, float, float, float, float]:
    if not path.is_file():
        raise FileNotFoundError(path)
    values = path.read_text().splitlines()
    if len(values) < 8:
        raise ValueError(f"{path}: expected at least eight parameter lines")
    try:
        nx, ny = int(values[0].split()[0]), int(values[1].split()[0])
        resolution = float(values[3].split()[0])
        west, east, south, north = (float(values[i].split()[0]) for i in range(4, 8))
    except (ValueError, IndexError) as exc:
        raise ValueError(f"{path}: could not parse CaMa-Flood map geometry") from exc
    if nx <= 0 or ny <= 0 or resolution <= 0 or west >= east or south >= north:
        raise ValueError(f"{path}: invalid map dimensions or extent")
    return nx, ny, resolution, west, east, south, north


def read_records(path: Path, dtype: str, count: int, shape: tuple[int, int], records: int = 1) -> np.ndarray:
    if not path.is_file():
        raise FileNotFoundError(path)
    data = np.fromfile(path, dtype=np.dtype(dtype))
    expected = count * records
    if data.size != expected:
        raise ValueError(f"{path}: expected {expected} {dtype} values, found {data.size}")
    return data.reshape((records, *shape))


def read_snapshot(path: Path, nx: int, ny: int, west: float, resolution: float, south: float, north: float):
    with Dataset(path) as source:
        if "flddph" not in source.variables or "lat" not in source.variables or "lon" not in source.variables:
            raise ValueError(f"{path}: expected flddph, lat and lon variables")
        variable = source.variables["flddph"]
        if variable.dimensions == ("lat", "lon"):
            values = np.ma.asarray(variable[:], dtype=np.float32)
        elif variable.dimensions == ("time", "lat", "lon") and variable.shape[0] == 1:
            values = np.ma.asarray(variable[0], dtype=np.float32)
        else:
            raise ValueError(f"{path}: flddph must be (lat,lon) or one-record (time,lat,lon); aggregate first")
        if getattr(variable, "units", "") != "m":
            raise ValueError(f"{path}: flddph units must be 'm'")
        lon = np.asarray(source.variables["lon"][:], dtype=np.float64)
        lat = np.asarray(source.variables["lat"][:], dtype=np.float64)
        attrs = {name: source.getncattr(name) for name in source.ncattrs()}
        fill = getattr(variable, "_FillValue", np.float32(1.0e20))
    if values.shape != (ny, nx) or lon.size != nx or lat.size != ny:
        raise ValueError(f"{path}: flddph grid {values.shape} does not match map {(ny, nx)}")
    expected_lon = west + (np.arange(nx, dtype=np.float64) + 0.5) * resolution
    expected_lat = north - (np.arange(ny, dtype=np.float64) + 0.5) * resolution
    if not np.allclose(lon, expected_lon, rtol=0, atol=1.0e-5) or not np.allclose(lat, expected_lat, rtol=0, atol=1.0e-5):
        raise ValueError(f"{path}: coordinates do not match params.txt cell centers and north-first row order")
    raw = np.asarray(np.ma.filled(values, np.float32(fill)), dtype=np.float32)
    raw[(~np.isfinite(raw)) | (raw == np.float32(fill)) | (raw == np.float32(1.0e20))] = FILL_VALUE
    return raw, attrs


def read_locations(path: Path) -> list[dict[str, object]]:
    if not path.is_file():
        raise FileNotFoundError(path)
    lines = path.read_text().splitlines()
    if len(lines) < 2:
        raise ValueError(f"{path}: incomplete location file")
    try:
        declared = int(lines[0].split()[0])
    except ValueError as exc:
        raise ValueError(f"{path}: first line must give tile count") from exc
    tiles = []
    for line_number, line in enumerate(lines[2:], start=3):
        fields = line.split()
        if not fields:
            continue
        if len(fields) < 9:
            raise ValueError(f"{path}:{line_number}: expected tile id, area, bounds, dimensions and resolution")
        tiles.append({
            "id": fields[0], "area": fields[1], "west": float(fields[2]),
            "east": float(fields[3]), "south": float(fields[4]), "north": float(fields[5]),
            "nx": int(fields[6]), "ny": int(fields[7]), "resolution": float(fields[8]),
        })
    if len(tiles) != declared:
        raise ValueError(f"{path}: declares {declared} tiles but contains {len(tiles)} rows")
    return tiles


def merge_high_resolution(map_dir: Path, resolution_tag: str, bounds: tuple[float, float, float, float],
                          pixel_size: float, shape: tuple[int, int]):
    west, east, south, north = bounds
    height, width = shape
    high_dir = map_dir / resolution_tag
    tiles = read_locations(high_dir / "location.txt")
    down_x = np.full(shape, -9999, dtype=np.int16)
    down_y = np.full(shape, -9999, dtype=np.int16)
    catch_x = np.full(shape, -9999, dtype=np.int16)
    catch_y = np.full(shape, -9999, dtype=np.int16)
    flddif = np.full(shape, FILL_VALUE, dtype=np.float32)
    rivwth = np.full(shape, FILL_VALUE, dtype=np.float32)
    copied = 0

    for tile in tiles:
        tw, te = float(tile["west"]), float(tile["east"])
        ts, tn = float(tile["south"]), float(tile["north"])
        nx, ny = int(tile["nx"]), int(tile["ny"])
        tile_size = float(tile["resolution"])
        if te < west or tw > east or tn < south or ts > north:
            continue
        if not np.isclose(tile_size, pixel_size, rtol=0, atol=1.0e-9):
            raise ValueError(f"{high_dir}/location.txt: mixed high-resolution grid sizes")
        name = str(tile["area"])
        cells = nx * ny
        cx = read_records(high_dir / f"{name}.catmxy.bin", "<i2", cells, (ny, nx), records=2)
        dx_path = high_dir / f"{name}.downxy.bin"
        if dx_path.is_file():
            downstream = read_records(dx_path, "<i2", cells, (ny, nx), records=2)
            tx, ty = downstream[0], downstream[1]
        else:
            flow_path = high_dir / f"{name}.flwdir.bin"
            flow = read_records(flow_path, "i1", cells, (ny, nx))[0]
            tx = np.full((ny, nx), -9999, dtype=np.int16)
            ty = np.full((ny, nx), -9999, dtype=np.int16)
            directions = {
                1: (0, -1), 2: (1, -1), 3: (1, 0), 4: (1, 1),
                5: (0, 1), 6: (-1, 1), 7: (-1, 0), 8: (-1, -1),
                0: (-999, -999), -1: (-1000, -1000),
            }
            for code, (offset_x, offset_y) in directions.items():
                selected = flow == code
                tx[selected], ty[selected] = offset_x, offset_y
            tx[~np.isin(flow, list(directions))] = -9999
            ty[~np.isin(flow, list(directions))] = -9999
        relative_height = read_records(high_dir / f"{name}.flddif.bin", "<f4", cells, (ny, nx))[0]
        river_width = read_records(high_dir / f"{name}.rivwth.bin", "<f4", cells, (ny, nx))[0]

        longitudes = tw + (np.arange(nx, dtype=np.float64) + 0.5) * tile_size
        longitudes = np.where(longitudes >= 180.0, longitudes - 360.0, longitudes)
        longitudes = np.where(longitudes < -180.0, longitudes + 360.0, longitudes)
        latitudes = tn - (np.arange(ny, dtype=np.float64) + 0.5) * tile_size
        columns = np.floor((longitudes - west) / pixel_size + 0.001).astype(np.int64)
        rows = np.floor((north - latitudes) / pixel_size + 0.001).astype(np.int64)
        good_x = (longitudes > west) & (longitudes < east) & (columns >= 0) & (columns < width)
        good_y = (latitudes > south) & (latitudes < north) & (rows >= 0) & (rows < height)
        if np.any(good_x) and np.any(good_y):
            source_cols, target_cols = np.flatnonzero(good_x), columns[good_x]
            source_rows, target_rows = np.flatnonzero(good_y), rows[good_y]
            target_index = np.ix_(target_rows, target_cols)
            source_index = np.ix_(source_rows, source_cols)
            down_x[target_index] = tx[source_index]
            down_y[target_index] = ty[source_index]
            catch_x[target_index] = cx[0][source_index]
            catch_y[target_index] = cx[1][source_index]
            flddif[target_index] = relative_height[source_index]
            rivwth[target_index] = river_width[source_index]
            copied += int(good_x.sum() * good_y.sum())
    if copied == 0:
        raise ValueError(f"No high-resolution tiles cover requested buffered bounds {bounds}")
    return down_x, down_y, catch_x, catch_y, flddif, rivwth, copied


def convert_flwdir(flow: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Translate the legacy signed byte direction codes to downstream increments."""
    dx = np.full(flow.shape, -9999, dtype=np.int16)
    dy = np.full(flow.shape, -9999, dtype=np.int16)
    values = {
        1: (0, -1), 2: (1, -1), 3: (1, 0), 4: (1, 1), 5: (0, 1),
        6: (-1, 1), 7: (-1, 0), 8: (-1, -1), 0: (-999, -999),
        -1: (-1000, -1000),
    }
    for code, (x, y) in values.items():
        match = flow == code
        dx[match], dy[match] = x, y
    return dx, dy


def inside(x: int, y: int, nx: int, ny: int) -> bool:
    return 0 <= x < nx and 0 <= y < ny


def calculate_depth(depth: np.ndarray, next_x: np.ndarray, next_y: np.ndarray, upstream_area: np.ndarray,
                    down_x: np.ndarray, down_y: np.ndarray, catch_x: np.ndarray,
                    catch_y: np.ndarray, flddif: np.ndarray, rivwth: np.ndarray) -> tuple[np.ndarray, dict[str, int]]:
    ny, nx = catch_x.shape
    map_ny, map_nx = next_x.shape
    uparea = np.asarray(upstream_area, dtype=np.float32).copy()
    valid_map = next_x != -9999
    uparea[valid_map] = uparea[valid_map] * np.float32(1.0e-6)
    max_uparea = np.zeros((map_ny, map_nx), dtype=np.float32)

    # The first Fortran pass records the largest upstream area entering each downstream cell.
    for iy in range(map_ny):
        for ix in range(map_nx):
            jx, jy = int(next_x[iy, ix]) - 1, int(next_y[iy, ix]) - 1
            if jx >= 0 and jy >= 0:
                max_uparea[jy, jx] = max(max_uparea[jy, jx], uparea[iy, ix])

    assigned = catch_x > 0
    flood = np.full((ny, nx), FILL_VALUE, dtype=np.float32)
    flood[assigned] = np.float32(0.0)
    if np.any(assigned):
        iy_map = catch_y[assigned].astype(np.int64) - 1
        ix_map = catch_x[assigned].astype(np.int64) - 1
        if (np.any(iy_map < 0) or np.any(iy_map >= map_ny) or
                np.any(ix_map < 0) or np.any(ix_map >= map_nx)):
            raise ValueError("High-resolution catmxy contains an index outside the coarse map")
        coarse_depth = depth[iy_map, ix_map]
        relative = flddif[assigned]
        wet = coarse_depth > relative
        values = np.zeros(coarse_depth.shape, dtype=np.float32)
        values[wet] = coarse_depth[wet] - relative[wet]
        flood[assigned] = values

    check = np.zeros((ny, nx), dtype=np.float32)
    outlet_count = mainstem_count = tributary_count = 0
    # Mark outlet paths and distinguish a mainstem reach from a tributary by the
    # exact single-precision comparison used by the Fortran reference.
    for iy in range(ny):
        for ix in range(nx):
            if catch_x[iy, ix] <= 0:
                continue
            ixx, iyy = int(catch_x[iy, ix]) - 1, int(catch_y[iy, ix]) - 1
            jxx, jyy = int(next_x[iyy, ixx]), int(next_y[iyy, ixx])
            if jxx <= 0 or down_x[iy, ix] < -900:
                continue
            jx, jy = ix + int(down_x[iy, ix]), iy + int(down_y[iy, ix])
            if not inside(jx, jy, nx, ny):
                continue
            if catch_x[jy, jx] == jxx and catch_y[jy, jx] == jyy:
                check[iy, ix] = np.float32(6.0)
                value = np.float32(1.0)
                if uparea[iyy, ixx] == max_uparea[jyy - 1, jxx - 1]:
                    value = np.float32(3.0)
                outlet_count += 1
                if value == 3.0:
                    mainstem_count += 1
                else:
                    tributary_count += 1
                steps = 0
                while catch_x[jy, jx] == jxx and catch_y[jy, jx] == jyy:
                    check[jy, jx] = max(check[jy, jx], value)
                    if down_x[jy, jx] < -900:
                        break
                    kx, ky = jx + int(down_x[jy, jx]), jy + int(down_y[jy, jx])
                    if not inside(kx, ky, nx, ny):
                        check[jy, jx] = np.float32(-1.0)
                        break
                    jx, jy = kx, ky
                    steps += 1
                    if steps > nx * ny:
                        raise ValueError("Cycle detected while following high-resolution catchment flow")

    modify = np.zeros((map_ny, map_nx), dtype=np.float32)
    tributary_updates = 0
    # Increase downstream tributary depths using the outlet depth gradient to the mainstem.
    for iy in range(ny):
        for ix in range(nx):
            if catch_x[iy, ix] <= 0:
                continue
            ixx, iyy = int(catch_x[iy, ix]) - 1, int(catch_y[iy, ix]) - 1
            jxx, jyy = int(next_x[iyy, ixx]), int(next_y[iyy, ixx])
            if jxx <= 0 or down_x[iy, ix] < -900:
                continue
            outlet_x, outlet_y = ix + int(down_x[iy, ix]), iy + int(down_y[iy, ix])
            if not inside(outlet_x, outlet_y, nx, ny):
                continue
            if catch_x[outlet_y, outlet_x] != jxx or catch_y[outlet_y, outlet_x] != jyy:
                continue
            if check[outlet_y, outlet_x] > 1.0:
                continue
            dph1 = np.float32(flood[iy, ix])
            length = np.float32(1.0)
            jx, jy = outlet_x, outlet_y
            steps = 0
            while check[jy, jx] == 1.0:
                if down_x[jy, jx] < -900:
                    break
                kx, ky = jx + int(down_x[jy, jx]), jy + int(down_y[jy, jx])
                jx, jy = kx, ky
                length = np.float32(length + np.float32(1.0))
                steps += 1
                if not inside(jx, jy, nx, ny):
                    raise ValueError("Tributary reaches the edge before its termination marker")
                if steps > nx * ny:
                    raise ValueError("Cycle detected in tributary adjustment path")
            if check[jy, jx] == -1.0:
                continue
            dph2 = np.float32(flood[jy, jx])
            ddph = np.float32(np.float32(dph1 - dph2) / length)
            if ddph < 0.0:
                ddph = np.float32(0.0)
            jx, jy = outlet_x, outlet_y
            length = np.float32(1.0)
            steps = 0
            while check[jy, jx] == 1.0:
                adjusted = np.float32(dph1 - np.float32(ddph * length))
                if adjusted > flood[jy, jx]:
                    modify[jyy - 1, jxx - 1] = np.float32(1.0)
                    flood[jy, jx] = max(flood[jy, jx], adjusted)
                    tributary_updates += 1
                if down_x[jy, jx] < -900:
                    break
                kx, ky = jx + int(down_x[jy, jx]), jy + int(down_y[jy, jx])
                jx, jy = kx, ky
                length = np.float32(length + np.float32(1.0))
                steps += 1
                if not inside(jx, jy, nx, ny):
                    raise ValueError("Tributary modification path leaves the buffered grid")
                if steps > nx * ny:
                    raise ValueError("Cycle detected in tributary modification path")

    # Backwater raises local water surfaces in modified catchments, in map-flow order.
    backwater_updates = 0
    for iy in range(ny):
        for ix in range(nx):
            if catch_x[iy, ix] <= 0:
                continue
            ixx, iyy = int(catch_x[iy, ix]) - 1, int(catch_y[iy, ix]) - 1
            if modify[iyy, ixx] == 0.0 or check[iy, ix] != 0.0 or down_x[iy, ix] < -900:
                continue
            jx, jy = ix + int(down_x[iy, ix]), iy + int(down_y[iy, ix])
            if not inside(jx, jy, nx, ny):
                continue
            steps = 0
            while check[jy, jx] == 0.0:
                if down_x[jy, jx] < -900:
                    break
                kx, ky = jx + int(down_x[jy, jx]), jy + int(down_y[jy, jx])
                if not inside(kx, ky, nx, ny):
                    check[jy, jx] = np.float32(-1.0)
                    break
                jx, jy = kx, ky
                steps += 1
                if steps > nx * ny:
                    raise ValueError("Cycle detected while searching downstream water level")
            if check[jy, jx] == -1.0:
                # The Fortran EXIT leaves the current east-west scan at this row.
                break
            dph1 = np.float32(flddif[jy, jx] + flood[jy, jx])
            jx, jy = ix, iy
            steps = 0
            while check[jy, jx] == 0.0:
                local_surface = np.float32(flddif[jy, jx] + flood[jy, jx])
                if local_surface < dph1:
                    flood[jy, jx] = np.float32(dph1 - flddif[jy, jx])
                    backwater_updates += 1
                check[jy, jx] = np.float32(10.0)
                if down_x[jy, jx] < -900:
                    break
                kx, ky = jx + int(down_x[jy, jx]), jy + int(down_y[jy, jx])
                if not inside(kx, ky, nx, ny):
                    check[jy, jx] = np.float32(-1.0)
                    break
                jx, jy = kx, ky
                steps += 1
                if steps > nx * ny:
                    raise ValueError("Cycle detected while applying backwater adjustment")

    permanent = assigned & (rivwth != FILL_VALUE) & (rivwth != 0.0)
    flood[permanent] = np.maximum(PERMANENT_WATER_DEPTH, flood[permanent])
    summary = {
        "assigned_pixels_in_buffer": int(np.count_nonzero(assigned)),
        "outlet_pixels": outlet_count,
        "mainstem_outlet_paths": mainstem_count,
        "tributary_outlet_paths": tributary_count,
        "tributary_depth_updates": tributary_updates,
        "backwater_depth_updates": backwater_updates,
        "permanent_water_pixels_in_buffer": int(np.count_nonzero(permanent)),
    }
    return flood, summary


def write_output(path: Path, values: np.ndarray, extent: tuple[float, float, float, float],
                 pixel_size: float, source: Path, map_dir: Path, resolution: str, input_attrs: dict[str, object]) -> None:
    west, east, south, north = extent
    ny, nx = values.shape
    longitude = west + (np.arange(nx, dtype=np.float64) + 0.5) * pixel_size
    latitude = north - (np.arange(ny, dtype=np.float64) + 0.5) * pixel_size
    path.parent.mkdir(parents=True, exist_ok=True)
    with Dataset(path, "w", format="NETCDF4") as output:
        output.createDimension("lat", ny)
        output.createDimension("lon", nx)
        lat = output.createVariable("lat", "f8", ("lat",))
        lat.standard_name, lat.long_name, lat.units = "latitude", "latitude", "degrees_north"
        lat[:] = latitude
        lon = output.createVariable("lon", "f8", ("lon",))
        lon.standard_name, lon.long_name, lon.units = "longitude", "longitude", "degrees_east"
        lon[:] = longitude
        flddph = output.createVariable("flddph", "f4", ("lat", "lon"), fill_value=FILL_VALUE, zlib=True, complevel=4)
        flddph.long_name = "downscaled floodplain water depth"
        flddph.units = "m"
        flddph.coordinates = "lat lon"
        flddph[:, :] = np.ma.masked_where((values == FILL_VALUE) | ~np.isfinite(values), values)
        output.title = "CaMa-Flood tributary-aware downscaled flood depth"
        output.source = str(source)
        output.map_directory = str(map_dir)
        output.high_resolution_map = resolution
        output.downscaling_method = "downscale_flddph_trib.F90 Python port"
        output.downscaling_description = "Catchment flddph minus flddif; mainstem/tributary classification; tributary inundation adjustment; backwater adjustment; permanent-water minimum 0.1 m."
        output.domain_west_east_south_north_degrees = json.dumps([west, east, south, north])
        output.pixel_size_degrees = pixel_size
        if "selected_cf_time" in input_attrs:
            output.selected_cf_time = str(input_attrs["selected_cf_time"])
        if "temporal_selection" in input_attrs:
            output.temporal_selection = str(input_attrs["temporal_selection"])
        if "aggregation_sample_count" in input_attrs:
            output.aggregation_sample_count = int(input_attrs["aggregation_sample_count"])
        output.history = "Generated by the standalone downscale_flddph.py package script."


def main() -> None:
    args = parse_args()
    if not args.input.is_file():
        raise FileNotFoundError(args.input)
    if args.west >= args.east or args.south >= args.north:
        raise ValueError("Require WEST < EAST and SOUTH < NORTH")
    map_dir = args.map_dir.resolve()
    nx_map, ny_map, grid_size, west_map, east_map, south_map, north_map = read_map_geometry(map_dir / "params.txt")
    if args.west < west_map or args.east > east_map or args.south < south_map or args.north > north_map:
        raise ValueError("Requested domain must be contained by the coarse river map")

    highres_dir = map_dir / args.resolution
    location_tiles = read_locations(highres_dir / "location.txt")
    sizes = {float(tile["resolution"]) for tile in location_tiles}
    if len(sizes) != 1:
        raise ValueError(f"{highres_dir}/location.txt: all tiles must use one resolution")
    pixel_size = sizes.pop()
    width_float = (args.east - args.west) / pixel_size
    height_float = (args.north - args.south) / pixel_size
    if not np.isclose(width_float, round(width_float), rtol=0, atol=1.0e-6) or not np.isclose(height_float, round(height_float), rtol=0, atol=1.0e-6):
        raise ValueError("Requested domain bounds must align to an integer number of high-resolution cells")
    out_nx, out_ny = int(round(width_float)), int(round(height_float))
    buffer = grid_size * 5.0
    west_buf, east_buf = args.west - buffer, args.east + buffer
    south_buf, north_buf = args.south - buffer, args.north + buffer
    buf_w_float = (east_buf - west_buf) / pixel_size
    buf_h_float = (north_buf - south_buf) / pixel_size
    if not np.isclose(buf_w_float, round(buf_w_float), rtol=0, atol=1.0e-6) or not np.isclose(buf_h_float, round(buf_h_float), rtol=0, atol=1.0e-6):
        raise ValueError("Five-cell coarse-map buffer does not align to the high-resolution grid")
    buf_nx, buf_ny = int(round(buf_w_float)), int(round(buf_h_float))
    shift_x = int(grid_size * 5.0 / pixel_size + 0.01)
    shift_y = int(grid_size * 5.0 / pixel_size + 0.01)

    depth, input_attrs = read_snapshot(args.input, nx_map, ny_map, west_map, grid_size, south_map, north_map)
    next_records = read_records(map_dir / "nextxy.bin", "<i4", nx_map * ny_map, (ny_map, nx_map), records=2)
    upstream = read_records(map_dir / "uparea.bin", "<f4", nx_map * ny_map, (ny_map, nx_map))[0]
    down_x, down_y, catch_x, catch_y, flddif, rivwth, copied = merge_high_resolution(
        map_dir, args.resolution, (west_buf, east_buf, south_buf, north_buf), pixel_size, (buf_ny, buf_nx),
    )
    flood, diagnostics = calculate_depth(
        depth, next_records[0], next_records[1], upstream,
        down_x, down_y, catch_x, catch_y, flddif, rivwth,
    )
    output_values = flood[shift_y:shift_y + out_ny, shift_x:shift_x + out_nx]
    if output_values.shape != (out_ny, out_nx):
        raise ValueError(f"Output crop shape mismatch: {output_values.shape} vs {(out_ny, out_nx)}")
    extent = (args.west, args.east, args.south, args.north)
    write_output(args.output, output_values, extent, pixel_size, args.input.resolve(), map_dir, args.resolution, input_attrs)
    valid = output_values[(output_values != FILL_VALUE) & np.isfinite(output_values)]
    print(json.dumps({
        "output": str(args.output), "shape_yx": list(output_values.shape), "dtype": "float32",
        "units": "m", "resolution_degrees": pixel_size,
        "domain_west_east_south_north": list(extent),
        "buffer_shape_yx": [buf_ny, buf_nx], "high_resolution_pixels_merged": copied,
        "valid_output_pixels": int(valid.size),
        "minimum_depth_m": float(valid.min()) if valid.size else None,
        "maximum_depth_m": float(valid.max()) if valid.size else None,
        "processing_diagnostics": diagnostics,
    }, indent=2))


if __name__ == "__main__":
    main()

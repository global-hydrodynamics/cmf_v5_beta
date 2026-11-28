#!/usr/bin/env python3
"""Port the tributary-aware CaMa-Flood flood-depth downscaler to Python."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from netCDF4 import Dataset
import numpy as np

FILL_VALUE = np.float32(-9999.0)
PERMANENT_WATER_DEPTH = np.float32(0.1)

REPOSITORY = Path(__file__).resolve().parents[4]
MAP_TOOLS_CODE = REPOSITORY / "map" / "tools" / "code"
if str(MAP_TOOLS_CODE) not in sys.path:
    sys.path.insert(0, str(MAP_TOOLS_CODE))
from hires_metadata import read_location_csv, read_location_txt  # noqa: E402
from map_metadata import read_map_geometry as read_standard_map_geometry  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True, help="2D flddph NetCDF or one-record Float32 Binary")
    parser.add_argument("--input-format", choices=("auto", "netcdf", "binary"), default="auto")
    parser.add_argument("--map-dir", type=Path, required=True, help="CaMa-Flood coarse river map directory")
    parser.add_argument("--map-format", choices=("auto", "netcdf", "binary"), default="auto")
    parser.add_argument("--resolution", required=True, help="High-resolution map directory/tag, for example 1min")
    parser.add_argument("--west", type=float, required=True)
    parser.add_argument("--east", type=float, required=True)
    parser.add_argument("--south", type=float, required=True)
    parser.add_argument("--north", type=float, required=True)
    parser.add_argument("--tributary-fill", type=int, choices=(0, 1), default=1)
    parser.add_argument("--permanent-water", type=int, choices=(0, 1), default=1)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def read_map_geometry(path: Path) -> tuple[int, int, float, float, float, float, float]:
    geometry = read_standard_map_geometry(path)
    return (geometry.nx, geometry.ny, geometry.resolution, geometry.west,
            geometry.east, geometry.south, geometry.north)


def read_records(path: Path, dtype: str, count: int, shape: tuple[int, int], records: int = 1) -> np.ndarray:
    if not path.is_file():
        raise FileNotFoundError(path)
    data = np.fromfile(path, dtype=np.dtype(dtype))
    expected = count * records
    if data.size != expected:
        raise ValueError(f"{path}: expected {expected} {dtype} values, found {data.size}")
    return data.reshape((records, *shape))


def read_base_map(map_dir: Path, map_format: str, nx: int, ny: int, west: float,
                  north: float, resolution: float):
    """Read nextxy and uparea into the common (lat,lon), north-first arrays."""
    formats = {}
    sources = {}
    layers = {}
    expected_lon = west + (np.arange(nx, dtype=np.float64) + 0.5) * resolution
    expected_lat = north - (np.arange(ny, dtype=np.float64) + 0.5) * resolution
    for layer in ("nextxy", "uparea"):
        netcdf_path = map_dir / f"{layer}.nc"
        if not netcdf_path.is_file():
            netcdf_path = map_dir / "netcdf" / f"{layer}.nc"
        binary_path = map_dir / "binary" / f"{layer}.bin"
        if not binary_path.is_file():
            binary_path = map_dir / f"{layer}.bin"
        selected = resolve_format(map_format, netcdf_path, binary_path, layer)
        formats[layer] = selected
        sources[layer] = str(netcdf_path if selected == "netcdf" else binary_path)
        if selected == "binary":
            if layer == "nextxy":
                values = read_records(binary_path, "<i4", nx * ny, (ny, nx), records=2)
                layers["nextx"], layers["nexty"] = values[0], values[1]
            else:
                layers["uparea"] = read_records(binary_path, "<f4", nx * ny, (ny, nx))[0]
                layers["uparea"][(~np.isfinite(layers["uparea"])) | (layers["uparea"] == FILL_VALUE)] = FILL_VALUE
            continue

        with Dataset(netcdf_path) as source:
            for coord, expected in (("lon", expected_lon), ("lat", expected_lat)):
                if coord not in source.variables:
                    raise ValueError(f"{netcdf_path}: missing {coord} coordinate")
                actual = np.asarray(source.variables[coord][:], dtype=np.float64)
                if not np.allclose(actual, expected, rtol=0, atol=1e-5):
                    raise ValueError(f"{netcdf_path}: {coord} does not match params.nml cell centers")
            names = ("nextx", "nexty") if layer == "nextxy" else ("uparea",)
            for name in names:
                if name not in source.variables:
                    raise ValueError(f"{netcdf_path}: missing {name!r}")
                variable = source.variables[name]
                if variable.dimensions != ("lat", "lon") or variable.shape != (ny, nx):
                    raise ValueError(f"{netcdf_path}: {name} must have dimensions (lat,lon) and shape {(ny, nx)}")
                fill = getattr(variable, "_FillValue", -9999)
                data = np.ma.asarray(variable[:])
                if name.startswith("next"):
                    layers[name] = np.asarray(np.ma.filled(data, fill), dtype=np.int32)
                else:
                    data = np.asarray(np.ma.filled(data, fill), dtype=np.float32)
                    data[(~np.isfinite(data)) | (data == np.float32(fill))] = FILL_VALUE
                    layers[name] = data
    return layers["nextx"], layers["nexty"], layers["uparea"], formats, sources


def resolve_format(requested: str, netcdf_path: Path, binary_path: Path, label: str) -> str:
    """Prefer NetCDF in auto mode; only missing files allow fallback."""
    if requested == "netcdf":
        if not netcdf_path.is_file():
            raise FileNotFoundError(f"{label}: required NetCDF map/input is missing: {netcdf_path}")
        return "netcdf"
    if requested == "binary":
        if not binary_path.is_file():
            raise FileNotFoundError(f"{label}: required Binary map/input is missing: {binary_path}")
        return "binary"
    if netcdf_path.is_file():
        return "netcdf"
    if binary_path.is_file():
        return "binary"
    raise FileNotFoundError(f"{label}: neither NetCDF nor Binary input exists ({netcdf_path}, {binary_path})")


def read_snapshot(path: Path, nx: int, ny: int, west: float, resolution: float,
                  north: float, input_format: str):
    selected_format = input_format
    if selected_format == "auto":
        suffix = path.suffix.lower()
        if suffix in (".nc", ".nc4", ".cdf"):
            selected_format = "netcdf"
        elif suffix in (".bin", ".dat", ".raw"):
            selected_format = "binary"
        else:
            raise ValueError(f"Cannot infer flddph format from suffix {path.suffix!r}; set --input-format")
    if selected_format == "binary":
        data = np.fromfile(path, dtype="<f4")
        expected = nx * ny
        if data.size != expected:
            raise ValueError(f"{path}: expected one {expected}-cell Float32 Binary record, found {data.size} values")
        values = data.reshape((ny, nx))
        attrs = {"input_format": "binary"}
        raw = np.asarray(values, dtype=np.float32)
        raw[(~np.isfinite(raw)) | (raw == FILL_VALUE) | (raw == np.float32(1.0e20))] = FILL_VALUE
        return raw, attrs, selected_format

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
        raise ValueError(f"{path}: coordinates do not match params.nml cell centers and north-first row order")
    raw = np.asarray(np.ma.filled(values, np.float32(fill)), dtype=np.float32)
    raw[(~np.isfinite(raw)) | (raw == np.float32(fill)) | (raw == np.float32(1.0e20))] = FILL_VALUE
    return raw, attrs, selected_format


def read_netcdf_tile(path: Path, tile: dict[str, object], layer: str) -> dict[str, np.ndarray]:
    """Read and validate only one intersecting high-resolution NetCDF tile."""
    nx, ny = int(tile["nx"]), int(tile["ny"])
    west, north, pixel = float(tile["west"]), float(tile["north"]), float(tile["resolution"])
    expected_lon = west + (np.arange(nx, dtype=np.float64) + 0.5) * pixel
    expected_lon = np.where(expected_lon >= 180.0, expected_lon - 360.0, expected_lon)
    expected_lon = np.where(expected_lon < -180.0, expected_lon + 360.0, expected_lon)
    expected_lat = north - (np.arange(ny, dtype=np.float64) + 0.5) * pixel
    names = {
        "catmxy": ("catmxx", "catmyy"),
        "downxy": ("downx", "downy"),
        "elevtn": ("elevtn",),
        "flwdir": ("flwdir",),
        "flddif": ("flddif",),
        "rivwth": ("rivwth",),
    }[layer]
    with Dataset(path) as source:
        if "lon" not in source.variables or "lat" not in source.variables:
            raise ValueError(f"{path}: missing lon/lat coordinates")
        lon = np.asarray(source.variables["lon"][:], dtype=np.float64)
        lat = np.asarray(source.variables["lat"][:], dtype=np.float64)
        if not np.allclose(lon, expected_lon, rtol=0, atol=1e-5) or not np.allclose(lat, expected_lat, rtol=0, atol=1e-5):
            raise ValueError(f"{path}: NetCDF coordinates do not match the high-resolution inventory cell centers")
        result = {}
        for name in names:
            if name not in source.variables:
                raise ValueError(f"{path}: missing {name!r} for {layer}")
            variable = source.variables[name]
            if variable.dimensions != ("lat", "lon") or variable.shape != (ny, nx):
                raise ValueError(f"{path}: {name} must have dimensions (lat,lon) and shape {(ny, nx)}")
            fill = getattr(variable, "_FillValue", -9999)
            data = np.ma.asarray(variable[:])
            if np.issubdtype(data.dtype, np.integer):
                data = np.asarray(np.ma.filled(data, fill), dtype=np.int16 if data.dtype.itemsize <= 2 else np.int32)
            else:
                data = np.asarray(np.ma.filled(data, fill), dtype=np.float32)
                data[(~np.isfinite(data)) | (data == np.float32(fill))] = FILL_VALUE
            result[name] = data
    return result


def read_locations(path: Path) -> list[dict[str, object]]:
    areas = read_location_csv(path) if path.name == "location.csv" else read_location_txt(path)
    return [{
        "id": str(area.iarea), "area": area.carea, "west": area.west,
        "east": area.east, "south": area.south, "north": area.north,
        "nx": area.nx, "ny": area.ny, "resolution": area.csize,
    } for area in areas]


def resolve_hires_layer(high_dir: Path, area: str, layer: str, requested: str) -> tuple[str, Path, str]:
    """Resolve one high-resolution layer, preferring NetCDF in auto mode."""
    layers = ("downxy", "flwdir") if layer == "flow" else (layer,)
    candidates = []
    for layer_name in layers:
        candidates.append(("netcdf", high_dir / f"{area}.{layer_name}.nc", layer_name))
    legacy_nc_dir = high_dir.parent / f"{high_dir.name}_nc"
    for layer_name in layers:
        candidates.append(("netcdf", legacy_nc_dir / f"{area}.{layer_name}.nc", layer_name))
    for layer_name in layers:
        candidates.append(("binary", high_dir / f"{area}.{layer_name}.bin", layer_name))
    if requested == "netcdf":
        candidates = [item for item in candidates if item[0] == "netcdf"]
    elif requested == "binary":
        candidates = [item for item in candidates if item[0] == "binary"]
    for file_format, path, layer_name in candidates:
        if path.is_file():
            return file_format, path, layer_name
    expected = ", ".join(str(path) for _, path, _ in candidates)
    raise FileNotFoundError(f"Missing required {layer} map layer; checked {expected}")


def read_binary_hires_tile(path: Path, tile: dict[str, object], layer: str) -> dict[str, np.ndarray]:
    nx, ny = int(tile["nx"]), int(tile["ny"])
    cells = nx * ny
    if layer == "catmxy":
        values = read_records(path, "<i2", cells, (ny, nx), records=2)
        return {"catmxx": values[0], "catmyy": values[1]}
    if layer == "downxy":
        values = read_records(path, "<i2", cells, (ny, nx), records=2)
        return {"downx": values[0], "downy": values[1]}
    if layer == "flwdir":
        values = read_records(path, "i1", cells, (ny, nx))[0]
        return {"flwdir": values}
    values = read_records(path, "<f4", cells, (ny, nx))[0]
    values[(~np.isfinite(values)) | (values == FILL_VALUE) | (values == np.float32(-9999.0))] = FILL_VALUE
    return {layer: values}


def merge_high_resolution(map_dir: Path, resolution_tag: str, bounds: tuple[float, float, float, float],
                          pixel_size: float, shape: tuple[int, int], map_format: str):
    west, east, south, north = bounds
    height, width = shape
    high_dir = map_dir / resolution_tag
    location_csv = high_dir / "location.csv"
    location_file = location_csv if location_csv.is_file() else high_dir / "location.txt"
    tiles = read_locations(location_file)
    down_x = np.full(shape, -9999, dtype=np.int16)
    down_y = np.full(shape, -9999, dtype=np.int16)
    catch_x = np.full(shape, -9999, dtype=np.int16)
    catch_y = np.full(shape, -9999, dtype=np.int16)
    flddif = np.full(shape, FILL_VALUE, dtype=np.float32)
    rivwth = np.full(shape, FILL_VALUE, dtype=np.float32)
    copied = 0
    used_formats: dict[str, str] = {}
    used_sources: dict[str, str] = {}

    for tile in tiles:
        tw, te = float(tile["west"]), float(tile["east"])
        ts, tn = float(tile["south"]), float(tile["north"])
        nx, ny = int(tile["nx"]), int(tile["ny"])
        tile_size = float(tile["resolution"])
        if te < west or tw > east or tn < south or ts > north:
            continue
        if not np.isclose(tile_size, pixel_size, rtol=0, atol=1.0e-9):
            raise ValueError(f"{location_file}: mixed high-resolution grid sizes")
        name = str(tile["area"])
        tile_data: dict[str, dict[str, np.ndarray]] = {}
        for layer in ("catmxy", "flow", "flddif", "rivwth"):
            file_format, source_path, source_layer = resolve_hires_layer(high_dir, name, layer, map_format)
            if file_format == "netcdf":
                tile_data[layer] = read_netcdf_tile(source_path, tile, source_layer)
            else:
                tile_data[layer] = read_binary_hires_tile(source_path, tile, source_layer)
            used_formats[f"{name}.{source_layer}"] = file_format
            used_sources[f"{name}.{source_layer}"] = str(source_path)
        cx = np.stack((tile_data["catmxy"]["catmxx"], tile_data["catmxy"]["catmyy"]))
        if "downx" in tile_data["flow"]:
            tx, ty = tile_data["flow"]["downx"], tile_data["flow"]["downy"]
        else:
            flow = tile_data["flow"]["flwdir"]
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
        relative_height = tile_data["flddif"]["flddif"]
        river_width = tile_data["rivwth"]["rivwth"]

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
    return down_x, down_y, catch_x, catch_y, flddif, rivwth, copied, used_formats, used_sources


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
                    catch_y: np.ndarray, flddif: np.ndarray, rivwth: np.ndarray,
                    tributary_fill: bool = True, permanent_water: bool = True) -> tuple[np.ndarray, dict[str, int]]:
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

    if not tributary_fill:
        permanent = assigned & (rivwth != FILL_VALUE) & (rivwth != 0.0)
        if permanent_water:
            flood[permanent] = np.maximum(PERMANENT_WATER_DEPTH, flood[permanent])
        return flood, {
            "assigned_pixels_in_buffer": int(np.count_nonzero(assigned)),
            "outlet_pixels": 0,
            "mainstem_outlet_paths": 0,
            "tributary_outlet_paths": 0,
            "tributary_depth_updates": 0,
            "backwater_depth_updates": 0,
            "permanent_water_pixels_in_buffer": int(np.count_nonzero(permanent)) if permanent_water else 0,
        }

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
    if permanent_water:
        flood[permanent] = np.maximum(PERMANENT_WATER_DEPTH, flood[permanent])
    summary = {
        "assigned_pixels_in_buffer": int(np.count_nonzero(assigned)),
        "outlet_pixels": outlet_count,
        "mainstem_outlet_paths": mainstem_count,
        "tributary_outlet_paths": tributary_count,
        "tributary_depth_updates": tributary_updates,
        "backwater_depth_updates": backwater_updates,
        "permanent_water_pixels_in_buffer": int(np.count_nonzero(permanent)) if permanent_water else 0,
    }
    return flood, summary


def write_output(path: Path, values: np.ndarray, extent: tuple[float, float, float, float],
                 pixel_size: float, source: Path, map_dir: Path, resolution: str,
                 input_attrs: dict[str, object], input_format: str,
                 map_formats: dict[str, str], map_sources: dict[str, str], tributary_fill: bool,
                 permanent_water: bool) -> None:
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
        output.title = ("CaMa-Flood tributary-aware downscaled flood depth" if tributary_fill
                        else "CaMa-Flood basic downscaled flood depth")
        output.source = str(source)
        output.input_file = source.name
        output.input_format = input_format
        output.map_directory = str(map_dir)
        unique_formats = set(map_formats.values())
        output.map_format = next(iter(unique_formats)) if len(unique_formats) == 1 else "mixed"
        output.map_format_details = json.dumps(map_formats, sort_keys=True)
        output.map_source_files = json.dumps(map_sources, sort_keys=True)
        output.high_resolution_map = resolution
        output.tributary_fill = int(tributary_fill)
        output.permanent_water = int(permanent_water)
        if tributary_fill:
            output.downscaling_method = "downscale_flddph_trib.F90 Python port"
            description = ["Catchment flddph minus flddif", "mainstem/tributary classification",
                           "tributary inundation adjustment", "backwater adjustment"]
        else:
            output.downscaling_method = "basic catchment-based flood-depth downscaling"
            description = ["Catchment flddph minus flddif"]
        if permanent_water:
            description.append("permanent-water minimum 0.1 m")
        output.downscaling_description = "; ".join(description) + "."
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
    nx_map, ny_map, grid_size, west_map, east_map, south_map, north_map = read_map_geometry(map_dir)
    if args.west < west_map or args.east > east_map or args.south < south_map or args.north > north_map:
        raise ValueError("Requested domain must be contained by the coarse river map")

    highres_dir = map_dir / args.resolution
    location_file = highres_dir / "location.csv"
    if not location_file.is_file():
        location_file = highres_dir / "location.txt"
    location_tiles = read_locations(location_file)
    sizes = {float(tile["resolution"]) for tile in location_tiles}
    if len(sizes) != 1:
        raise ValueError(f"{location_file}: all tiles must use one resolution")
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

    depth, input_attrs, actual_input_format = read_snapshot(
        args.input, nx_map, ny_map, west_map, grid_size, north_map, args.input_format,
    )
    next_x, next_y, upstream, base_formats, base_sources = read_base_map(
        map_dir, args.map_format, nx_map, ny_map, west_map, north_map, grid_size,
    )
    down_x, down_y, catch_x, catch_y, flddif, rivwth, copied, high_formats, high_sources = merge_high_resolution(
        map_dir, args.resolution, (west_buf, east_buf, south_buf, north_buf), pixel_size,
        (buf_ny, buf_nx), args.map_format,
    )
    actual_map_formats = {**base_formats, **high_formats}
    actual_map_sources = {
        key: str(Path(source_path).relative_to(map_dir))
        for key, source_path in {**base_sources, **high_sources}.items()
    }
    flood, diagnostics = calculate_depth(
        depth, next_x, next_y, upstream, down_x, down_y, catch_x, catch_y, flddif, rivwth,
        tributary_fill=bool(args.tributary_fill), permanent_water=bool(args.permanent_water),
    )
    output_values = flood[shift_y:shift_y + out_ny, shift_x:shift_x + out_nx]
    if output_values.shape != (out_ny, out_nx):
        raise ValueError(f"Output crop shape mismatch: {output_values.shape} vs {(out_ny, out_nx)}")
    extent = (args.west, args.east, args.south, args.north)
    write_output(
        args.output, output_values, extent, pixel_size, args.input.resolve(), map_dir,
        args.resolution, input_attrs, actual_input_format, actual_map_formats, actual_map_sources,
        bool(args.tributary_fill), bool(args.permanent_water),
    )
    valid = output_values[(output_values != FILL_VALUE) & np.isfinite(output_values)]
    print(json.dumps({
        "output": str(args.output), "shape_yx": list(output_values.shape), "dtype": "float32",
        "units": "m", "resolution_degrees": pixel_size,
        "input_format": actual_input_format,
        "map_format_details": actual_map_formats,
        "map_source_files": actual_map_sources,
        "tributary_fill": bool(args.tributary_fill),
        "permanent_water": bool(args.permanent_water),
        "domain_west_east_south_north": list(extent),
        "buffer_shape_yx": [buf_ny, buf_nx], "high_resolution_pixels_merged": copied,
        "valid_output_pixels": int(valid.size),
        "minimum_depth_m": float(valid.min()) if valid.size else None,
        "maximum_depth_m": float(valid.max()) if valid.size else None,
        "processing_diagnostics": diagnostics,
    }, indent=2))


if __name__ == "__main__":
    main()

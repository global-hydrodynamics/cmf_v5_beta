#!/usr/bin/env python3
"""Validate the three Tutorial 11 gauge allocations against the Rhine map."""

from __future__ import annotations

import argparse
import csv
import math
from pathlib import Path

from netCDF4 import Dataset
import numpy as np


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as stream:
        return list(csv.DictReader(stream))


def load_map(map_dir: Path):
    netcdf = map_dir / "netcdf"
    with Dataset(netcdf / "lonlat.nc") as data:
        lon = np.asarray(data.variables["lon"][:], dtype=np.float64)
        lat = np.asarray(data.variables["lat"][:], dtype=np.float64)
        outlon_var = data.variables["outlon"]
        outlat_var = data.variables["outlat"]
        if (outlon_var.dimensions != ("lat", "lon") or
                outlat_var.dimensions != ("lat", "lon") or
                getattr(outlon_var, "units", "") != "degrees_east" or
                getattr(outlat_var, "units", "") != "degrees_north"):
            raise ValueError("lonlat.nc outlet coordinate metadata is not as expected")
        outlon = np.ma.asarray(outlon_var[:], dtype=np.float64).filled(np.nan)
        outlat = np.ma.asarray(outlat_var[:], dtype=np.float64).filled(np.nan)
    with Dataset(netcdf / "uparea.nc") as data:
        variable = data.variables["uparea"]
        if variable.dimensions != ("lat", "lon") or getattr(variable, "units", "") != "m2":
            raise ValueError("uparea.nc must be a lat/lon grid with units m2")
        uparea = np.ma.asarray(variable[:], dtype=np.float64).filled(np.nan)
    with Dataset(netcdf / "nextxy.nc") as data:
        nextx = np.ma.asarray(data.variables["nextx"][:]).filled(-9999).astype(np.int32)
        nexty = np.ma.asarray(data.variables["nexty"][:]).filled(-9999).astype(np.int32)
        grid_lon = np.asarray(data.variables["lon"][:], dtype=np.float64)
        grid_lat = np.asarray(data.variables["lat"][:], dtype=np.float64)
    shape = (lat.size, lon.size)
    if any(a.shape != shape for a in (outlon, outlat, uparea, nextx, nexty)):
        raise ValueError("Rhine map variables do not match the map coordinate dimensions")
    if not (np.allclose(grid_lon, lon) and np.allclose(grid_lat, lat)):
        raise ValueError("nextxy grid coordinates do not match lonlat.nc")
    if not (np.all(np.diff(lon) > 0) and np.all(np.diff(lat) < 0)):
        raise ValueError("Expected eastward longitude and north-first latitude axes")
    return lon, lat, outlon, outlat, uparea, nextx, nexty


def great_circle_km(lon1: float, lat1: float, lon2: float, lat2: float) -> float:
    """Return spherical great-circle distance using the mean Earth radius."""
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = phi2 - phi1
    dlambda = math.radians(lon2 - lon1)
    hav = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return 2 * 6371.0088 * math.asin(math.sqrt(hav))


def parse_grdc_outputs(data_path: Path, output_path: Path) -> dict[str, dict[str, str]]:
    source_by_name = {row["Station Name"].strip().casefold(): row
                      for row in read_csv(data_path)}
    output_by_id: dict[str, dict[str, str]] = {}
    with output_path.open(encoding="utf-8") as stream:
        for line in stream:
            fields = line.split()
            if len(fields) >= 10 and fields[0].isdigit():
                output_by_id[fields[0]] = {
                    "ix1": fields[8], "iy1": fields[9], "area_CaMa_km2": fields[4],
                }
    result = {}
    for name, source in source_by_name.items():
        if source["ID"] in output_by_id:
            result[name] = {**source, **output_by_id[source["ID"]]}
    return result


def trace_downstream(start: tuple[int, int], targets: dict[str, tuple[int, int]],
                     nextx: np.ndarray, nexty: np.ndarray) -> list[str]:
    rows, cols = nextx.shape
    current = start
    seen: set[tuple[int, int]] = set()
    visited: list[str] = []
    for _ in range(rows * cols):
        if current in seen:
            break
        seen.add(current)
        for name, cell in targets.items():
            if current == cell and name not in visited:
                visited.append(name)
        x = int(nextx[current])
        y = int(nexty[current])
        if x < 1 or y < 1 or x > cols or y > rows:
            break
        current = (y - 1, x - 1)
    return visited


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tutorial-dir", type=Path, required=True)
    parser.add_argument("--map-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    tutorial = args.tutorial_dir.resolve()
    map_dir = args.map_dir.resolve()
    stations_path = tutorial / "observation/stations_data/allstations.csv"
    gauge_path = tutorial / "metadata/02_gauges.csv"
    if not stations_path.is_file() or not gauge_path.is_file():
        raise FileNotFoundError("Required station metadata or selected gauge inventory is missing")
    stations = {row["Id"]: row for row in read_csv(stations_path)}
    selected = [row for row in read_csv(gauge_path)
                if row.get("plot_group") == "existing_gauges"]
    if len(selected) != 3:
        raise ValueError(f"Expected the three selected existing gauges; found {len(selected)}")

    lon, lat, outlon, outlat, uparea, nextx, nexty = load_map(map_dir)
    map_resolution = float(np.median(np.diff(lon)))
    if not np.allclose(np.diff(lon), map_resolution) or not np.allclose(-np.diff(lat), map_resolution):
        raise ValueError("Map grid is not a regular square degree grid")
    grdc = parse_grdc_outputs(map_dir.parent / "data/GRDC_allocated.csv",
                              map_dir / "GRDC_alloc.txt")

    prepared = []
    for gauge in selected:
        station_id = str(gauge["location_id"])
        if station_id not in stations:
            raise ValueError(f"Station {station_id} from 02_gauges.csv is missing in allstations.csv")
        source = stations[station_id]
        source_row, source_col = int(source["Cama15row"]), int(source["Cama15col"])
        source_lon = -180.0 + (source_col + 0.5) * map_resolution
        source_lat = 90.0 - (source_row + 0.5) * map_resolution
        if (not math.isclose(source_lon, float(source["Cama15lon"]), abs_tol=1e-5) or
                not math.isclose(source_lat, float(source["Cama15lat"]), abs_tol=1e-5)):
            raise ValueError(f"{source['Name']}: Cama15 row/col does not match global grid-center convention")
        col = int(np.argmin(np.abs(lon - source_lon)))
        row = int(np.argmin(np.abs(lat - source_lat)))
        if (abs(float(lon[col]) - source_lon) > 1e-5 or
                abs(float(lat[row]) - source_lat) > 1e-5):
            raise ValueError(f"{source['Name']}: supplied Cama15 cell is outside current Rhine map")

        model_out_lon, model_out_lat = float(outlon[row, col]), float(outlat[row, col])
        model_uparea_m2 = float(uparea[row, col])
        if not (math.isfinite(model_out_lon) and math.isfinite(model_out_lat) and
                model_out_lon != -9999 and model_out_lat != -9999 and
                math.isfinite(model_uparea_m2) and model_uparea_m2 > 0):
            raise ValueError(f"{source['Name']}: selected map cell lacks a valid outlet/uparea")
        model_uparea_km2 = model_uparea_m2 / 1_000_000.0
        if not math.isclose(model_uparea_km2, float(source["Cama15area"]), abs_tol=0.05):
            raise ValueError(f"{source['Name']}: current map uparea disagrees with ECMWF Cama15area")

        grdc_match = grdc.get(source["Name"].strip().casefold())
        grdc_match_cell = "not_found"
        grdc_id = ""
        if grdc_match:
            grdc_id = grdc_match["ID"]
            grdc_row, grdc_col = int(grdc_match["iy1"]) - 1, int(grdc_match["ix1"]) - 1
            grdc_match_cell = "match" if (grdc_row, grdc_col) == (row, col) else "mismatch"

        observed_lon, observed_lat = float(source["StatLon"]), float(source["StatLat"])
        reported_area = float(source["ProvArea"])
        prepared.append({
            "source": source, "gauge": gauge, "row": row, "col": col,
            "model_out_lon": model_out_lon, "model_out_lat": model_out_lat,
            "model_uparea_m2": model_uparea_m2, "model_uparea_km2": model_uparea_km2,
            "distance_km": great_circle_km(observed_lon, observed_lat,
                                            model_out_lon, model_out_lat),
            "reported_area": reported_area,
            "conditional_area_ratio": model_uparea_km2 / reported_area,
            "conditional_area_error_pct": 100 * (model_uparea_km2 - reported_area) / reported_area,
            "grdc_id": grdc_id, "grdc_match": grdc_match,
            "grdc_match_cell": grdc_match_cell,
        })

    cells = {item["source"]["Name"]: (item["row"], item["col"]) for item in prepared}
    chain = trace_downstream(cells["Maxau"], cells, nextx, nexty)
    if chain[:3] != ["Maxau", "Speyer", "Lobith"]:
        raise ValueError(f"Expected downstream chain Maxau -> Speyer -> Lobith; visited {chain}")
    if any(item["grdc_match_cell"] == "mismatch" for item in prepared):
        raise ValueError("A selected cell disagrees with the current map's GRDC allocation output")

    fields = [
        "station_id", "station_name", "river", "country",
        "observed_lon_deg", "observed_lat_deg", "reported_area_source_value",
        "reported_area_unit_status", "ecmwf_cama15_lon_deg", "ecmwf_cama15_lat_deg",
        "ecmwf_cama15_area_source_value", "ecmwf_cama15_area_unit_status",
        "ecmwf_cama15_global_row_0based", "ecmwf_cama15_global_col_0based",
        "source_global_index_basis", "model_row_0based", "model_col_0based",
        "map_cell_center_lon_deg", "map_cell_center_lat_deg",
        "model_outlet_lon_deg", "model_outlet_lat_deg", "model_uparea_m2",
        "model_uparea_km2", "observed_to_outlet_great_circle_km",
        "area_ratio_conditional_on_km2", "area_error_pct_conditional_on_km2",
        "area_comparison_unit_note", "grdc_station_id", "grdc_model_row_0based",
        "grdc_model_col_0based", "grdc_allocation_matches_selected_cell",
        "ecmwf_allocation_matches_selected_cell", "network_order_from_maxau",
        "allocation_status", "allocation_reason",
    ]
    chain_order = {name: i + 1 for i, name in enumerate(chain)}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for item in prepared:
            source = item["source"]
            grdc_match = item["grdc_match"]
            writer.writerow({
                "station_id": source["Id"], "station_name": source["Name"],
                "river": source["River"], "country": source["Country"],
                "observed_lon_deg": source["StatLon"], "observed_lat_deg": source["StatLat"],
                "reported_area_source_value": source["ProvArea"],
                "reported_area_unit_status": "not_declared_in_source; km2_basis_is_conditional",
                "ecmwf_cama15_lon_deg": source["Cama15lon"],
                "ecmwf_cama15_lat_deg": source["Cama15lat"],
                "ecmwf_cama15_area_source_value": source["Cama15area"],
                "ecmwf_cama15_area_unit_status": "not_declared; value_matches_current_uparea_m2_divided_by_1e6",
                "ecmwf_cama15_global_row_0based": source["Cama15row"],
                "ecmwf_cama15_global_col_0based": source["Cama15col"],
                "source_global_index_basis": "zero_based_glb_15min; row_north_first; col_west_first",
                "model_row_0based": item["row"], "model_col_0based": item["col"],
                "map_cell_center_lon_deg": f"{lon[item['col']]:.6f}",
                "map_cell_center_lat_deg": f"{lat[item['row']]:.6f}",
                "model_outlet_lon_deg": f"{item['model_out_lon']:.8f}",
                "model_outlet_lat_deg": f"{item['model_out_lat']:.8f}",
                "model_uparea_m2": f"{item['model_uparea_m2']:.3f}",
                "model_uparea_km2": f"{item['model_uparea_km2']:.3f}",
                "observed_to_outlet_great_circle_km": f"{item['distance_km']:.3f}",
                "area_ratio_conditional_on_km2": f"{item['conditional_area_ratio']:.6f}",
                "area_error_pct_conditional_on_km2": f"{item['conditional_area_error_pct']:.3f}",
                "area_comparison_unit_note": "Conditional: treat ProvArea as km2; source has no unit declaration. GRDC source fields and the current map comparison support, but do not formally declare, this interpretation.",
                "grdc_station_id": item["grdc_id"],
                "grdc_model_row_0based": int(grdc_match["iy1"]) - 1 if grdc_match else "",
                "grdc_model_col_0based": int(grdc_match["ix1"]) - 1 if grdc_match else "",
                "grdc_allocation_matches_selected_cell": item["grdc_match_cell"],
                "ecmwf_allocation_matches_selected_cell": "match_after_global_to_regional_crosswalk",
                "network_order_from_maxau": chain_order[source["Name"]],
                "allocation_status": "checked_existing_allocation",
                "allocation_reason": "ECMWF cell center and raw row/col resolve to this current map cell; its outlet and uparea are valid, the current GRDC allocation agrees, and nextxy traces Maxau to Speyer to Lobith.",
            })
    print(f"Wrote {args.output} ({len(prepared)} stations); downstream order: {' -> '.join(chain)}")
    for item in prepared:
        print(f"{item['source']['Name']}: row={item['row']} col={item['col']} "
              f"outlet=({item['model_out_lon']:.5f}, {item['model_out_lat']:.5f}) "
              f"distance={item['distance_km']:.2f} km "
              f"conditional area error={item['conditional_area_error_pct']:.2f}%")


if __name__ == "__main__":
    main()

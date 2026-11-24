#!/usr/bin/env python3
"""Allocate Tutorial 11 gauges and reported impact locations to the Rhine map."""

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


# Step 21 scientific review: candidate channel cells are selected from the
# local 1-minute catmxy assignments, current-map topology, outlet positions,
# and external gauge catchment areas where available. These are not geographic
# cell assignments and must remain separately labeled.
RIVER_ASSESSMENTS = {
    "impact-ahr-schuld": (10, 15, "plausible", "The Ahr candidate cell is the local small-channel outlet (6.9804, 50.4996), about 9 km from the approximate Schuld town point, and its nextxy link enters the Sinzig confluence cell. Its 680 km2 uparea is larger than the 353 km2 Müsch gauge catchment; treat it as a coarse downstream Ahr-path candidate, not a point match at Schuld."),
    "peak-ahr-muesch": (10, 15, "plausible", "The local Ahr-path candidate outlet is about 16.5 km downstream of the Müsch gauge coordinate and has 680 km2 uparea versus the reported 353 km2 gauge basin. It may support a broad Ahr timing context but is not a gauge-cell match."),
    "impact-ahr-altenahr": (10, 15, "plausible", "The candidate outlet is about 2.3 km from the town point, and the detailed Altenahr gauge coordinate is about 2 km away. Model uparea 680 km2 is reasonably close to the official 747 km2 gauge basin; nextxy connects to the Sinzig confluence cell. Keep the 0.25-degree support limitation."),
    "peak-ahr-altenahr": (10, 15, "plausible", "The candidate outlet is about 2 km from the detailed gauge coordinate and its 680 km2 uparea is close to the official 747 km2 gauge basin; nextxy connects to the Sinzig confluence cell. This is the strongest Ahr-cell candidate, though still a coarse-grid match."),
    "impact-ahr-bad-neuenahr": (None, None, "not_represented", "The 1-minute catmxy lookup assigns this location to the Sinzig/Rhine mainstem cell (row 9, col 17; about 140,561 km2), not to an Ahr-only cell. The mapped Ahr path jumps from the Altenahr-area candidate to the confluence, so no direct Bad Neuenahr Ahr cell is identified."),
    "impact-ahr-sinzig": (None, None, "unresolved", "The 1-minute catmxy lookup maps this location to the confluence/mainstem cell (row 9, col 17; about 140,561 km2). This may be useful for downstream mixed Rhine-plus-Ahr context, but it cannot isolate Ahr discharge at Sinzig."),
    "peak-ahr-bad-bodendorf": (None, None, "not_represented", "The 1-minute catmxy lookup maps this Ahr gauge location to the confluence/mainstem cell (row 9, col 17; about 140,561 km2), far larger than the official 861 km2 gauge catchment. No direct Bad Bodendorf Ahr channel cell is represented separately."),
    "impact-erft-bad-muenstereifel": (9, 15, "plausible", "The 1-minute catmxy assignment identifies this Erft catchment cell (630 km2); its outlet is downstream near the Erft corridor and nextxy leads northwest. This is a basin-scale candidate, not an exact locality cell."),
    "impact-erft-euskirchen": (9, 15, "plausible", "The 1-minute catmxy assignment identifies this Erft catchment cell (630 km2), with downstream routing northwest along the Erft corridor. The coarse outlet is not an exact point match."),
    "impact-erft-blessem": (8, 14, "plausible", "The 1-minute catmxy assignment selects row 8, col 14 rather than the containing cell's Rhine mainstem channel. It is downstream of the row 9, col 15 Erft candidate and routes northwest; use as a coarse downstream Erft candidate, not a precise Blessem reach."),
    "peak-erft-bliesheim": (9, 15, "plausible", "The candidate cell uparea is 630 km2, close to the Erftverband Bliesheim gauge catchment of 604.17 km2. Its outlet is about 5 km from the detailed gauge coordinate and nextxy links downstream to the Blessem-area candidate."),
    "impact-kyll-kordel": (11, 14, "confirmed", "The high-resolution catmxy assignment selects this cell; its outlet is about 1.5 km from Kordel and model uparea 819.9 km2 matches the official 819 km2 gauge catchment. nextxy then reaches the larger downstream Moselle routing cell."),
    "peak-kyll-kordel": (11, 14, "confirmed", "The high-resolution catmxy assignment selects this cell; its outlet is about 1.5 km from the detailed Kordel gauge coordinate and model uparea 819.9 km2 matches the official 819 km2 catchment. The nextxy link proceeds downstream to a much larger routing cell."),
    "impact-pruem-pruemzurlay": (None, None, "not_represented", "The mapped outlet associated with the location has about 4,222 km2 uparea, compared with the official 574 km2 Prümzurlay gauge catchment; the cell is near the Prüm–Sauer confluence and likely represents combined downstream routing. No separate Prüm evaluation cell is identified."),
    "peak-pruem-pruemzurlay": (None, None, "not_represented", "The mapped outlet associated with the location has about 4,222 km2 uparea, compared with the official 574 km2 Prümzurlay gauge catchment; the cell is near the Prüm–Sauer confluence and likely represents combined downstream routing. No separate Prüm evaluation cell is identified."),
    "impact-vesdre-verviers": (9, 12, "plausible", "The local 1-minute catmxy lookup assigns the location to this 351 km2 upstream Vesdre candidate; its outlet is about 3.5 km away and nextxy links west/downstream to the Pepinster-area cell."),
    "impact-vesdre-pepinster": (9, 11, "plausible", "The 1-minute catmxy lookup assigns the location to this 698 km2 Vesdre candidate; the mapped outlet is downstream toward the Meuse. The 0.25-degree grid does not establish the exact impact reach."),
    "impact-meuse-valkenburg": (8, 11, "plausible", "The 1-minute catmxy lookup assigns the Geul/Valkenburg location to this 340 km2 candidate, with a mapped outlet near the Geul–Meuse lowland and a valid downstream link. The exact river reach remains coarse-grid."),
    "peak-geul-valkenburg": (8, 11, "plausible", "The 1-minute catmxy lookup assigns the detailed Geul site to this 340 km2 candidate. Treat it as a coarse Geul basin/outlet match, not an exact site-level cell."),
    "impact-gete-halen": (8, 8, "plausible", "The 1-minute catmxy assignment agrees with this containing cell; the mapped outlet is about 9 km from Halen and the downstream link continues toward the Demer/Meuse routing system. The named local reach is not independently verified."),
    "impact-dyle-wavre": (9, 6, "plausible", "The 1-minute catmxy assignment agrees with this containing cell; the outlet is about 8 km from Wavre and the network links northward. This supports a coarse Dyle-basin candidate, not an exact reach match."),
}


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


def allocate_impact_locations(tutorial: Path, map_data, output_path: Path) -> None:
    """Assign each Step 1 report to its containing regional map cell."""
    impact_path = tutorial / "metadata/01_impact_locations.csv"
    timing_path = tutorial / "metadata/01_reported_flood_timing.csv"
    if not impact_path.is_file() or not timing_path.is_file():
        raise FileNotFoundError("Step 1 impact inventory or report/timing file is missing")
    impact_by_id = {row["location_id"]: row for row in read_csv(impact_path)}
    reports = read_csv(timing_path)
    (lon, lat, outlon, outlat, uparea, nextx, nexty, river_width, basin) = map_data
    resolution = float(np.median(np.diff(lon)))
    west, east = float(lon[0] - resolution / 2), float(lon[-1] + resolution / 2)
    north, south = float(lat[0] + resolution / 2), float(lat[-1] - resolution / 2)
    if not (np.allclose(np.diff(lon), resolution) and
            np.allclose(np.diff(lat), -resolution)):
        raise ValueError("Expected regular eastward longitude and north-first latitude axes")

    fields = [
        "report_id", "location_id", "location_name", "river_group",
        "observed_lon", "observed_lat", "coordinate_type", "coordinate_confidence",
        "model_row_0based", "model_col_0based", "model_cell_lon", "model_cell_lat",
        "model_outlet_lon", "model_outlet_lat", "model_uparea_km2",
        "distance_to_outlet_km", "model_basin_id", "model_cell_rivwth_m",
        "river_match_status", "allocation_status", "allocation_note",
        "river_model_row_0based", "river_model_col_0based",
        "river_model_cell_lon", "river_model_cell_lat",
        "river_model_outlet_lon", "river_model_outlet_lat",
        "river_model_uparea_km2", "river_model_rivwth_m",
        "river_allocation_status", "river_allocation_reason", "ai_notes",
    ]
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for report in reports:
            location_id = report["location_id"]
            base = impact_by_id.get(location_id, {})
            # The 14 impact rows retain the Step 1 locality inventory; extra
            # report rows retain their own detailed coordinate/name record.
            is_impact = report["timing_type"] == "impact_report"
            name = base.get("place", report["location_name"]) if is_impact else report["location_name"]
            river_group = report["river_group"] or base.get("river_group", "")
            coordinate_type = report["coordinate_type"]
            confidence = report["coordinate_confidence"] or report["confidence"]
            lon_text, lat_text = report["longitude"], report["latitude"]
            row = {key: "" for key in fields}
            row.update({
                "report_id": report["report_id"],
                "location_id": location_id,
                "location_name": name,
                "river_group": river_group,
                "observed_lon": lon_text,
                "observed_lat": lat_text,
                "coordinate_type": coordinate_type,
                "coordinate_confidence": confidence,
            })
            river_assignment = RIVER_ASSESSMENTS.get(report["report_id"])
            if river_assignment:
                river_row, river_col, river_status, river_reason = river_assignment
                row["river_allocation_status"] = river_status
                row["river_allocation_reason"] = river_reason
                if river_row is not None and river_col is not None:
                    if not (0 <= river_row < len(lat) and 0 <= river_col < len(lon)):
                        raise ValueError(
                            f"{report['report_id']}: reviewed river cell {(river_row, river_col)} "
                            "is outside the current map"
                        )
                    river_outlet_lon = float(outlon[river_row, river_col])
                    river_outlet_lat = float(outlat[river_row, river_col])
                    river_uparea = float(uparea[river_row, river_col])
                    river_width_value = float(river_width[river_row, river_col])
                    if not (math.isfinite(river_outlet_lon) and math.isfinite(river_outlet_lat)
                            and river_outlet_lon != -9999 and river_outlet_lat != -9999
                            and math.isfinite(river_uparea) and river_uparea > 0
                            and river_width_value > 0):
                        raise ValueError(
                            f"{report['report_id']}: reviewed river cell {(river_row, river_col)} "
                            "does not contain a valid river outlet"
                        )
                    row.update({
                        "river_model_row_0based": river_row,
                        "river_model_col_0based": river_col,
                        "river_model_cell_lon": f"{lon[river_col]:.6f}",
                        "river_model_cell_lat": f"{lat[river_row]:.6f}",
                        "river_model_outlet_lon": f"{river_outlet_lon:.8f}",
                        "river_model_outlet_lat": f"{river_outlet_lat:.8f}",
                        "river_model_uparea_km2": f"{river_uparea / 1_000_000.0:.3f}",
                        "river_model_rivwth_m": f"{river_width_value:.3f}",
                    })
            elif report["longitude"] and report["latitude"]:
                row["river_allocation_status"] = "unresolved"
                row["river_allocation_reason"] = "No river-cell assessment was recorded for this report; use only the geographic containing-cell allocation until reviewed."
            if not lon_text or not lat_text:
                row.update({
                    "river_match_status": "not_assessed_missing_coordinates",
                    "allocation_status": "missing_coordinates",
                    "allocation_note": "Step 1 record has no verified longitude/latitude; no location was inferred.",
                    "ai_notes": "Detailed report is retained by report_id, but its source has no coordinates. The base locality is a separate record and was not substituted for this detailed site.",
                })
                if not row["river_allocation_status"]:
                    row["river_allocation_status"] = "not_assessed_missing_coordinates"
                    row["river_allocation_reason"] = "No source coordinate is available; no river cell was inferred."
                writer.writerow(row)
                continue

            observed_lon, observed_lat = float(lon_text), float(lat_text)
            if not (west <= observed_lon < east and south <= observed_lat < north):
                row.update({
                    "river_match_status": "outside_model_map",
                    "allocation_status": "outside_map",
                    "allocation_note": f"Coordinate ({observed_lon:g}, {observed_lat:g}) is outside map edges {west:g}–{east:g} E, {south:g}–{north:g} N.",
                    "ai_notes": "No nearest-cell reassignment was attempted because the observation lies outside the current model map.",
                })
                writer.writerow(row)
                continue

            col = int(math.floor((observed_lon - west) / resolution))
            map_row = int(math.floor((north - observed_lat) / resolution))
            cell_lon, cell_lat = float(lon[col]), float(lat[map_row])
            outlet_lon, outlet_lat = float(outlon[map_row, col]), float(outlat[map_row, col])
            uparea_m2 = float(uparea[map_row, col])
            width_m = float(river_width[map_row, col])
            basin_id = int(basin[map_row, col])
            valid_outlet = (
                math.isfinite(outlet_lon) and math.isfinite(outlet_lat) and
                outlet_lon != -9999 and outlet_lat != -9999 and
                math.isfinite(uparea_m2) and uparea_m2 > 0 and width_m > 0
            )
            row.update({
                "model_row_0based": map_row,
                "model_col_0based": col,
                "model_cell_lon": f"{cell_lon:.6f}",
                "model_cell_lat": f"{cell_lat:.6f}",
                "model_basin_id": basin_id,
                "model_cell_rivwth_m": f"{width_m:.3f}" if math.isfinite(width_m) else "",
                "allocation_status": "assigned_to_containing_grid_cell",
            })
            if not valid_outlet:
                row.update({
                    "river_match_status": "no_valid_channel_outlet_in_cell",
                    "allocation_note": "Geographic grid cell is assigned; map cell has no valid river outlet/upstream area.",
                    "ai_notes": f"The point was assigned by containment to cell center ({cell_lon:.3f}, {cell_lat:.3f}); no alternative nearest-channel search was made. Model basin value {basin_id} is not treated as a natural basin name.",
                })
                writer.writerow(row)
                continue

            uparea_km2 = uparea_m2 / 1_000_000.0
            distance_km = great_circle_km(observed_lon, observed_lat, outlet_lon, outlet_lat)
            downx, downy = int(nextx[map_row, col]), int(nexty[map_row, col])
            downstream_note = ""
            if 1 <= downx <= len(lon) and 1 <= downy <= len(lat):
                downstream_note = f"Nextxy destination cell center=({lon[downx - 1]:.3f}, {lat[downy - 1]:.3f})."
            if river_group in {"Ahr", "Erft/Swist"} and uparea_km2 >= 100_000:
                river_status = "possible_major_channel_not_local_tributary"
                status_note = "Large mapped upstream area at a reported tributary locality suggests this coarse cell may correspond to a major routing channel rather than the named local tributary."
            elif distance_km <= 10:
                river_status = "plausible_local_network_not_verified"
                status_note = "The assigned cell has a valid river outlet within 10 km, but the named river connection is not proven by the coarse map cell alone."
            else:
                river_status = "coarse_grid_river_match_uncertain"
                status_note = "A valid channel exists in the containing cell, but outlet separation and 0.25-degree resolution do not establish correspondence to the named river reach."
            row.update({
                "model_outlet_lon": f"{outlet_lon:.8f}",
                "model_outlet_lat": f"{outlet_lat:.8f}",
                "model_uparea_km2": f"{uparea_km2:.3f}",
                "distance_to_outlet_km": f"{distance_km:.3f}",
                "river_match_status": river_status,
                "allocation_note": status_note,
                "ai_notes": (
                    f"Cell assigned by 0.25-degree outer-edge containment, not nearest Outlet. "
                    f"Outlet distance={distance_km:.1f} km; map uparea={uparea_km2:.1f} km2; "
                    f"model basin ID={basin_id} is a routing label, not a guaranteed natural-basin identity. "
                    f"{downstream_note} Geographic containing-cell allocation is separate from the river-assessment cell fields."
                ),
            })
            writer.writerow(row)
    print(f"Wrote {output_path} ({len(reports)} reports; {sum(bool(r['longitude'] and r['latitude']) for r in reports)} with coordinates)")


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
    parser.add_argument("--impact-output", type=Path, required=True)
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
    with Dataset(map_dir / "netcdf/rivwth_merit.nc") as data:
        river_width = np.ma.asarray(data.variables["rivwth"][:], dtype=np.float64).filled(0)
    with Dataset(map_dir / "netcdf/basin.nc") as data:
        basin = np.ma.asarray(data.variables["basin"][:]).filled(0).astype(np.int32)
    if river_width.shape != uparea.shape or basin.shape != uparea.shape:
        raise ValueError("basin/rivwth map arrays do not match the current map grid")
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
    allocate_impact_locations(
        tutorial,
        (lon, lat, outlon, outlat, uparea, nextx, nexty, river_width, basin),
        args.impact_output.resolve(),
    )


if __name__ == "__main__":
    main()

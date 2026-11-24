#!/usr/bin/env python3
"""Select the one Tutorial11 S1A acquisition and run the maintained depth downscaler.

Inputs: the scoped S1A pass handoff, model flddph, regional map and downscaler.
Outputs: one 1-minute depth NetCDF and verification/provenance JSON.
Workflow:
    1. Determine the exact source-scene acquisition-envelope midpoint in UTC.
    2. Select the nearest model output time without temporal interpolation.
    3. Run the maintained tributary/permanent-water-enabled downscaler.
    4. Record geometry/value checks, time offsets, provenance and limitations.
Depth is simulated metres, not a satellite classification or skill score.
Permanent-water minimum and the inherited forcing-attribution caveat remain.
"""
import argparse
import csv
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile

import numpy as np
from netCDF4 import Dataset, num2date


def utc(value):
    """Parse a source timestamp and normalize its explicit timezone to UTC."""
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)


def stamp(value):
    """Format the existing UTC datetime with a Z suffix."""
    return value.isoformat().replace("+00:00", "Z")


def main():
    """Select the one acquisition/model time, run the existing downscaler and record checks."""

    #*** 1. Read the scoped source/acquisition and output settings
    # Preserve the established CLI description while expanding source documentation.
    parser = argparse.ArgumentParser(description='Select the one Tutorial11 S1A acquisition and run the maintained depth downscaler.')
    parser.add_argument("--tutorial-dir", type=Path, required=True)
    parser.add_argument("--map-dir", type=Path, required=True)
    parser.add_argument("--downscaler", type=Path, required=True)
    parser.add_argument("--model-netcdf", type=Path)
    parser.add_argument("--domain-config", type=Path)
    parser.add_argument("--selection-json", type=Path)
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--metadata-output", type=Path)
    args = parser.parse_args()
    t = args.tutorial_dir.resolve()
    pass_id = "S1A_o038784_dt049389"
    selected = json.loads((args.selection_json or t / "metadata/03a_selected_passes.json").read_text())
    matches = [p for p in selected["passes"] if p["pass_id"] == pass_id]
    if len(matches) != 1 or matches[0]["satellite"] != "S1A" or matches[0]["absolute_orbit"] != 38784:
        raise ValueError("The requested single S1A acquisition is missing or ambiguous")
    footprints = json.loads((t / "metadata/03a_sentinel1_acquisition_footprints.geojson").read_text())
    # Group the five exact source scenes by the one Step03 acquisition ID.
    with (t / "metadata/03a_satellite_pass_inventory.csv").open() as stream:
        inventory = next(p for p in csv.DictReader(stream) if p["pass_id"] == pass_id)
    ids = inventory["source_product_ids"].split(";")
    scenes = [f["properties"] for f in footprints["features"] if f["properties"]["source_product_id"] in ids]
    if {p["source_product_id"] for p in scenes} != set(ids):
        raise ValueError("Incomplete source-product acquisition timestamps")
    if len(scenes) != matches[0]["source_product_count"]:
        raise ValueError("Unexpected number of scenes within the single acquisition")

    #*** 2. Select the acquisition midpoint and nearest model time
    start = min(utc(p["acquisition_start_utc"]) for p in scenes)
    end = max(utc(p["acquisition_end_utc"]) for p in scenes)
    representative = start + (end - start) / 2
    source = (args.model_netcdf or t / "experiment/Rhine2021/o_flddphRhine2021Jul.nc").resolve()
    domain = json.loads((args.domain_config or t / "metadata/02_domain_selection.json").read_text())
    west, south, east, north = domain["satellite_analysis"]["domain"]["bbox_west_south_east_north"]

    #*** 3. Extract one model snapshot and run the maintained downscaler
    with Dataset(source) as ds:
        vtime = ds["time"]
        if vtime.units != "seconds since 2021-07-01 00:00":
            raise ValueError("Recheck the model time convention for this changed output")
        times = num2date(
            vtime[:], vtime.units, calendar=getattr(vtime, "calendar", "standard"),
            only_use_cftime_datetimes=False, only_use_python_datetimes=True,
        )
        times = [v.replace(tzinfo=timezone.utc) for v in times]
        if not all(b > a for a, b in zip(times, times[1:])):
            raise ValueError("Model time axis is not strictly increasing")
        index = min(range(len(times)), key=lambda i: abs((times[i] - representative).total_seconds()))
        model_time = times[index]
        output = (args.output_dir or t/"out")/f"24_flddph_1min_{pass_id}_{model_time:%Y%m%dT%H%M%SZ}.nc"
        output.parent.mkdir(parents=True, exist_ok=True)
        field = ds["flddph"][index]
        if ds["flddph"].units != "m" or ds["flddph"].dimensions != ("time", "lat", "lon"):
            raise ValueError("Expected floodplain-depth snapshot in metres")
        # CF omits a time-zone offset here: the default reference offset is zero.
        # Step14 runs the ERA5-Land UTC forcing without a local-time shift; output
        # labels are endpoint point samples, not an average or acquisition interval.
        with tempfile.TemporaryDirectory(prefix="cama-step24-") as temp:
            snapshot = Path(temp) / "snapshot.nc"
            with Dataset(snapshot, "w") as d:
                for coord in ("lat", "lon"):
                    d.createDimension(coord, len(ds[coord]))
                    c = d.createVariable(coord, "f8", (coord,))
                    c[:] = ds[coord][:]
                    c.units = ds[coord].units
                v = d.createVariable("flddph", "f4", ("lat", "lon"), fill_value=ds["flddph"]._FillValue)
                v.units = "m"
                v[:] = field
                d.selected_cf_time = stamp(model_time)
            subprocess.run(
                [sys.executable, str(args.downscaler), "--input", str(snapshot),
                 "--map-dir", str(args.map_dir), "--map-format", "auto", "--resolution", "1min",
                 "--west", str(west), "--east", str(east), "--south", str(south), "--north", str(north),
                 "--tributary-fill", "1", "--permanent-water", "1", "--output", str(output)],
                check=True,
            )

    #*** 4. Record time offsets, depth/grid checks and provenance
    delta = (model_time - representative).total_seconds()
    time_basis = "CF default zero time-zone offset; Step14 ERA5-Land UTC forcing and no local-time shift; time: point at model output endpoints"
    with Dataset(output, "a") as d:
        d.source_input = str(source.relative_to(t) if source.is_relative_to(t) else source)
        d.source = str(source.relative_to(t) if source.is_relative_to(t) else source)
        d.satellite = "Sentinel-1A"
        d.absolute_orbit = 38784
        d.acquisition_id = pass_id
        d.observation_start_utc = stamp(start)
        d.observation_end_utc = stamp(end)
        d.observation_representative_time_utc = stamp(representative)
        d.representative_time_method = "Midpoint of full five-scene acquisition start/end envelope"
        d.model_time_utc = stamp(model_time)
        d.model_minus_observation_seconds = delta
        d.absolute_time_difference_seconds = abs(delta)
        d.model_time_index = index
        d.model_time_convention = time_basis
        d.model_experiment = "Rhine2021"
        d.product_status = "preliminary L0-L1; simulated depth, not satellite observation or skill validation"
        d.source_flddph_meaning = "Floodplain water depth at the output time (metres); no temporal interpolation"
        d.domain_source = "metadata/02_domain_selection.json: satellite_analysis.domain"
        d.permanent_water_caveat = "Existing rivwth-based permanent-water minimum of 0.1 m is enabled; positive depth is not a satellite flood classification"
        d.history = "Step24 one S1A acquisition; maintained tools/downscale_flddph tributary-aware Python port; no interpolation of coarse depth"
        # The extraction snapshot is temporary; preserve its actual origin above.
        d.input_file = str(source.relative_to(t) if source.is_relative_to(t) else source)
        values = np.ma.asarray(d["flddph"][:])
        valid = values.compressed()
        lon = np.asarray(d["lon"][:])
        lat = np.asarray(d["lat"][:])
        assert values.shape == (round((north - south)*60), round((east - west)*60))
        assert d["flddph"].units == "m" and valid.size and np.isfinite(valid).all() and (valid >= 0).all()
        assert np.allclose(np.diff(lon), 1 / 60, atol=1e-7, rtol=0)
        assert np.allclose(np.diff(lat), -1 / 60, atol=1e-7, rtol=0)
        assert np.allclose([lon[0] - 1 / 120, lat[-1] - 1 / 120, lon[-1] + 1 / 120, lat[0] + 1 / 120], [west, south, east, north], atol=1e-6)
        method = d.downscaling_method
        map_sources = json.loads(d.map_source_files) if "map_source_files" in d.ncattrs() else {k: str(d.getncattr(k)) for k in d.ncattrs() if "map" in k}
    inputs = [
        args.map_dir / "params.txt",
        args.map_dir / "1min/location.txt",
        *[args.map_dir / p for p in map_sources.values()],
        source,
        args.selection_json or t / "metadata/03a_selected_passes.json",
        t / "metadata/03a_sentinel1_acquisition_footprints.geojson",
        t / "metadata/03a_satellite_pass_inventory.csv",
        args.domain_config or t / "metadata/02_domain_selection.json",
        args.downscaler,
    ]
    report = {
        "status": "preliminary_executed",
        "acquisition_count": 1,
        "satellite": "Sentinel-1A",
        "absolute_orbit": 38784,
        "acquisition_id": pass_id,
        "scene_count": len(scenes),
        "scenes": scenes,
        "observation_start_utc": stamp(start),
        "observation_end_utc": stamp(end),
        "representative_time_utc": stamp(representative),
        "representative_time_method": "Midpoint of five-scene acquisition envelope; one pass, not five targets",
        "model_time_utc": stamp(model_time),
        "model_time_index": index,
        "model_minus_observation_seconds": delta,
        "absolute_time_difference_seconds": abs(delta),
        "model_time_convention": time_basis,
        "input_sha256": {str(p.relative_to(t) if p.is_relative_to(t) else p): hashlib.sha256(p.read_bytes()).hexdigest() for p in inputs},
        "output": str(output.relative_to(t) if output.is_relative_to(t) else output),
        "output_sha256": hashlib.sha256(output.read_bytes()).hexdigest(),
        "method": method,
        "map_sources": map_sources,
        "extent_west_south_east_north": [west, south, east, north],
        "resolution_degrees": 1 / 60,
        "shape_lat_lon": list(values.shape),
        "units": "m",
        "valid_pixels": int(valid.size),
        "missing_pixels": int(values.size - valid.size),
        "dry_pixels": int((valid == 0).sum()),
        "positive_pixels": int((valid > 0).sum()),
        "minimum_m": float(valid.min()),
        "maximum_m": float(valid.max()),
        "tributary_fill": True,
        "permanent_water": True,
        "limitations": [
            "Preliminary feasibility check, not independent scientific validation",
            "Permanent-water pixels may have an imposed 0.1 m minimum",
            "Five-coarse-cell buffer may be clipped by regional map coverage",
            "No GFM comparison, metrics, other acquisition, or finer-resolution downscaling",
            "Inherited Step14 KG-0019 forcing accumulation attribution remains unresolved",
        ],
    }
    (args.metadata_output or t / "metadata/24_downscaling_verification.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({k: report[k] for k in ["representative_time_utc", "model_time_utc", "absolute_time_difference_seconds", "shape_lat_lon", "valid_pixels", "missing_pixels", "minimum_m", "maximum_m"]}, indent=2))


if __name__ == "__main__":
    main()

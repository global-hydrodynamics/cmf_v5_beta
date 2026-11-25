#!/usr/bin/env python3
"""Compute and plot signed local peak discharge for Tutorial 11 Step 15.

Inputs: Step14 hourly outflw/pthflw, regional map and domain metadata.
Outputs: signed peak/time NetCDF fields, regional/AOI PNGs and printed diagnostics.
Workflow:
    1. Resolve and check the saved model/map/time contracts.
    2. Select signed local absolute maxima; sum active bifurcation layers first.
    3. Save analysis fields, render the two views, and report diagnostics.
Flows are in m3/s. Cell/path maxima may occur at different hours; this map is
not a simultaneous flow snapshot or a model-skill evaluation.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
import sys

import matplotlib

# Select the noninteractive backend before importing pyplot.
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.cm import ScalarMappable
from matplotlib.lines import Line2D
from netCDF4 import Dataset, num2date
import numpy as np

SCRIPT_DIR = Path(__file__).resolve().parent
TUTORIAL_DIR = SCRIPT_DIR.parent
ROOT = SCRIPT_DIR.parents[2]
sys.path.insert(0, str(ROOT / "visualization" / "river_map" / "script"))
sys.path.insert(0, str(ROOT / "visualization" / "cmf_colormap"))


def load_module(path: Path, name: str):
    """Load the existing visualization implementation from its repository path."""
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load visualization helper: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


VECTOR = load_module(
    ROOT / "visualization/output_analysis/script/f02-discharge_vector.py",
    "tutorial11_reused_discharge_vector",
)
from river_map_common import add_aligned_colorbar, draw_raster, read_geometry  # noqa: E402

EXPECTED_UNITS = "m3/s"


def parse_args() -> argparse.Namespace:
    """Read analysis/figure paths and the Shell-owned display settings."""
    # Preserve the established CLI description while expanding source documentation.
    parser = argparse.ArgumentParser(description='Compute and plot signed local peak discharge for Tutorial 11 Step 15.')
    parser.add_argument("--step14-metadata", type=Path, required=True)
    parser.add_argument("--domain-metadata", type=Path, required=True)
    parser.add_argument("--map-dir", type=Path, required=True)
    parser.add_argument("--tutorial-dir", type=Path, required=True)
    parser.add_argument("--analysis-file", type=Path, required=True)
    parser.add_argument("--regional-figure", type=Path, required=True)
    parser.add_argument("--aoi-figure", type=Path, required=True)
    parser.add_argument("--color-levels", required=True)
    parser.add_argument("--linthresh", type=float, required=True)
    parser.add_argument("--linear-frac", type=float, required=True)
    parser.add_argument("--dpi", type=int, default=200)
    parser.add_argument("--regional-height", type=float, default=10.0)
    parser.add_argument("--aoi-height", type=float, default=9.0)
    return parser.parse_args()


def read_metadata(path: Path) -> dict:
    """Read an existing JSON Step handoff without altering its contents."""
    with path.open(encoding="utf-8") as stream:
        return json.load(stream)


def resolve_step14_inputs(step14: dict, tutorial_dir: Path, root: Path):
    """Resolve required model outputs and the map path from the Step14 handoff."""
    output_rows = step14["outputs"]["hourly_files"]
    output_paths = {row["variable"]: tutorial_dir / row["path"] for row in output_rows}
    required = {"outflw", "pthflw"}
    if required - set(output_paths):
        raise ValueError(f"Step 14 metadata lacks output rows: {sorted(required - set(output_paths))}")
    for path in (output_paths["outflw"], output_paths["pthflw"]):
        if not path.is_file():
            raise FileNotFoundError(f"Step 14 output does not exist: {path}")
    map_dir = root / step14["map"]["path"].rstrip("/")
    return output_paths["outflw"], output_paths["pthflw"], map_dir


def read_map_data(map_dir: Path):
    """Read north-first map arrays, stored outlets/connectivity and bifurcation fields."""
    netcdf_dir = map_dir / "netcdf"
    with Dataset(netcdf_dir / "uparea.nc") as data:
        lon = np.asarray(data.variables["lon"][:], dtype=np.float64)
        lat = np.asarray(data.variables["lat"][:], dtype=np.float64)
        uparea = np.asarray(np.ma.filled(data.variables["uparea"][:], np.nan), dtype=np.float64)
    with Dataset(netcdf_dir / "nextxy.nc") as data:
        nextx = np.asarray(np.ma.filled(data.variables["nextx"][:], -9999), dtype=np.int32)
        nexty = np.asarray(np.ma.filled(data.variables["nexty"][:], -9999), dtype=np.int32)
    with Dataset(netcdf_dir / "lonlat.nc") as data:
        outlon = np.asarray(np.ma.filled(data.variables["outlon"][:], -9999), dtype=np.float64)
        outlat = np.asarray(np.ma.filled(data.variables["outlat"][:], -9999), dtype=np.float64)
    with Dataset(netcdf_dir / "bifprm.nc") as data:
        bif = {name: np.asarray(data.variables[name][:]) for name in (
            "pth_id", "ix", "iy", "jx", "jy", "width",
        )}
    shape = (lat.size, lon.size)
    if any(array.shape != shape for array in (uparea, nextx, nexty, outlon, outlat)):
        raise ValueError("Rhine map fields do not match the lon/lat grid")
    if not (np.all(np.diff(lon) > 0) and np.all(np.diff(lat) < 0)):
        raise ValueError("Expected map longitude eastward and latitude north-first")
    return lon, lat, uparea, nextx, nexty, outlon, outlat, bif


def parse_time_axis(variable, path: Path, expected_count: int):
    """Decode an expected-length finite hourly CF time axis; return numeric/date values."""
    if variable.ndim != 1 or len(variable) != expected_count:
        raise ValueError(f"{path}: expected {expected_count} time records, found {len(variable)}")
    numeric = np.asarray(variable[:], dtype=np.float64)
    if not np.all(np.isfinite(numeric)) or np.any(np.diff(numeric) != 3600):
        raise ValueError(f"{path}: time coordinate is not a finite hourly sequence")
    dates = num2date(
        numeric, variable.units, calendar=getattr(variable, "calendar", "standard"),
        only_use_cftime_datetimes=False,
    )
    return numeric, dates


def maximum_absolute_signed(values: np.ma.MaskedArray, time_values: np.ndarray):
    """Return signed local absolute maxima and their source-record times/indices.

    Time is axis 0. Invalid values are masked; entirely missing cells/paths
    return NaN values/times and index -1. Argmax retains the first tied peak.
    Retaining the sign distinguishes reverse flow from positive routing."""
    masked = np.ma.masked_invalid(np.ma.asarray(values, dtype=np.float64))
    all_missing = np.all(np.ma.getmaskarray(masked), axis=0)
    indices = np.asarray(np.ma.argmax(np.ma.abs(masked), axis=0), dtype=np.int32)
    selected = np.take_along_axis(masked.data, indices[np.newaxis, ...], axis=0)[0]
    selected = np.asarray(selected, dtype=np.float64)
    peak_times = np.asarray(time_values[indices], dtype=np.float64)
    selected[all_missing] = np.nan
    peak_times[all_missing] = np.nan
    indices[all_missing] = -1
    return selected, indices, peak_times, all_missing


def read_outflow(path: Path, geometry, expected_records: int):
    """Read hourly outflw [m3/s] on (time, north-first lat, lon) and select signed peaks."""
    nx, ny, resolution, west, east, south, north = geometry
    with Dataset(path) as data:
        variable = data.variables["outflw"]
        if variable.dimensions != ("time", "lat", "lon"):
            raise ValueError(f"{path}: unexpected outflw dimensions {variable.dimensions}")
        if getattr(variable, "units", "") != EXPECTED_UNITS:
            raise ValueError(f"{path}: outflw units must be {EXPECTED_UNITS}")
        if getattr(variable, "cell_methods", "") != "time: mean":
            raise ValueError(f"{path}: outflw must be labeled as a time mean")
        time_numeric, dates = parse_time_axis(data.variables["time"], path, expected_records)
        lon = np.asarray(data.variables["lon"][:], dtype=np.float64)
        lat = np.asarray(data.variables["lat"][:], dtype=np.float64)
        values = np.ma.masked_invalid(np.ma.asarray(variable[:], dtype=np.float64))
        fill = getattr(variable, "_FillValue", None)
        if fill is not None:
            values = np.ma.masked_where(values == float(fill), values)
    expected_lon = west + (np.arange(nx) + 0.5) * resolution
    expected_lat = north - (np.arange(ny) + 0.5) * resolution
    if values.shape != (expected_records, ny, nx):
        raise ValueError(f"{path}: output grid shape does not match {nx}x{ny}")
    if not (np.allclose(lon, expected_lon, rtol=0, atol=1e-5) and
            np.allclose(lat, expected_lat, rtol=0, atol=1e-5)):
        raise ValueError(f"{path}: output coordinates do not match Rhine map cell centers")
    peak, indices, peak_times, all_missing = maximum_absolute_signed(values, time_numeric)
    return peak, indices, peak_times, values, time_numeric, dates, int(np.ma.count(values)), int(np.count_nonzero(all_missing))


def read_bifurcation_peak(path: Path, bif: dict, expected_time: np.ndarray,
                          expected_records: int):
    """Match pth_id/endpoints, sum active signed layers, then select absolute maxima.

    Input pthflw is (time, NPTHLEV, NPTHOUT) [m3/s]; positive map widths
    select active layers. Hours without a valid active layer remain masked.
    The returned path order follows output IDs, not an assumed map row order."""

    #*** 1. Read the hourly layer/path contract and match endpoint IDs
    with Dataset(path) as data:
        variable = data.variables["pthflw"]
        if variable.dimensions != ("time", "NPTHLEV", "NPTHOUT"):
            raise ValueError(f"{path}: unexpected pthflw dimensions {variable.dimensions}")
        if getattr(variable, "units", "") != EXPECTED_UNITS:
            raise ValueError(f"{path}: pthflw units must be {EXPECTED_UNITS}")
        if getattr(variable, "cell_methods", "") != "time: mean":
            raise ValueError(f"{path}: pthflw must be labeled as a time mean")
        time_numeric, _ = parse_time_axis(data.variables["time"], path, expected_records)
        if not np.array_equal(time_numeric, expected_time):
            raise ValueError(f"{path}: pthflw time coordinate differs from outflw")
        path_ids = np.asarray(data.variables["pth_id"][:], dtype=np.int32)
        if len(np.unique(path_ids)) != len(path_ids):
            raise ValueError(f"{path}: pth_id values are not unique")
        output_endpoints = {
            name: np.asarray(data.variables[name][:], dtype=np.int32)
            for name in ("ix", "iy", "jx", "jy")
        }
        q = np.ma.masked_invalid(np.ma.asarray(variable[:], dtype=np.float64))
        for name, output_values in output_endpoints.items():
            map_by_id = {int(pid): int(value) for pid, value in zip(bif["pth_id"], bif[name])}
            if any(map_by_id.get(int(pid)) != int(value)
                   for pid, value in zip(path_ids, output_values)):
                raise ValueError(f"{path}: {name} endpoints do not match Rhine bifprm by pth_id")

    #*** 2. Sum signed flow over positive-width active layers
    map_ids = np.asarray(bif["pth_id"], dtype=np.int32)
    map_index = {int(pid): i for i, pid in enumerate(map_ids)}
    if set(path_ids.tolist()) != set(map_ids.tolist()):
        raise ValueError(f"{path}: output pth_id values do not match Rhine bifprm.nc")
    widths = np.asarray(bif["width"], dtype=np.float64)
    widths = widths[:, [map_index[int(pid)] for pid in path_ids]]
    active_layers = widths > 0
    valid_layer_values = ~np.ma.getmaskarray(q) & np.broadcast_to(active_layers[None, :, :], q.shape)
    summed = np.ma.sum(np.ma.array(q.data, mask=~valid_layer_values), axis=1)
    no_valid_layer = ~np.any(valid_layer_values, axis=1)
    summed = np.ma.array(summed.data, mask=np.ma.getmaskarray(summed) | no_valid_layer)

    #*** 3. Select signed local absolute maxima and retain path order
    peak, indices, peak_times, all_missing = maximum_absolute_signed(summed, time_numeric)

    map_bif = {name: np.asarray(bif[name], dtype=np.int32) for name in ("ix", "iy", "jx", "jy")}
    reorder = [map_index[int(pid)] for pid in path_ids]
    endpoints = {name: values[reorder] for name, values in map_bif.items()}
    channel = widths[0, :] > 0
    eligible = np.any(active_layers, axis=0)
    return {
        "path_ids": path_ids,
        "peak": peak,
        "peak_time_index": indices,
        "peak_time": peak_times,
        "endpoints": endpoints,
        "channel": channel,
        "eligible": eligible & ~all_missing,
        "active_layer_count": np.count_nonzero(active_layers, axis=0),
        "valid_layer_record_count": int(np.count_nonzero(valid_layer_values)),
    }


def write_analysis(path: Path, lon: np.ndarray, lat: np.ndarray, time_numeric: np.ndarray,
                   time_units: str, out_peak, out_index, out_time, path_result,
                   source_paths: list[str], time_start: str, time_end: str):
    """Save signed peak/time/index fields and their existing source/time metadata."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path_ids = path_result["path_ids"]
    with Dataset(path, "w", format="NETCDF4") as data:
        data.createDimension("lon", lon.size)
        data.createDimension("lat", lat.size)
        data.createDimension("bifurcation_path", path_ids.size)
        data.createVariable("lon", "f8", ("lon",))[:] = lon
        data.createVariable("lat", "f8", ("lat",))[:] = lat
        data.createVariable("pth_id", "i4", ("bifurcation_path",))[:] = path_ids
        out_var = data.createVariable("outflw_peak_signed", "f4", ("lat", "lon"),
                                      fill_value=-9999.0, zlib=True, complevel=4)
        out_var[:] = np.where(np.isfinite(out_peak), out_peak, -9999.0).astype(np.float32)
        out_var.units = EXPECTED_UNITS
        out_var.long_name = "signed outflw value at local maximum absolute hourly mean"
        out_var.cell_methods = "time: maximum (abs(outflw)); outflw: mean"
        out_time_var = data.createVariable("outflw_peak_time", "f8", ("lat", "lon"),
                                           fill_value=-9999.0, zlib=True, complevel=4)
        out_time_var[:] = np.where(np.isfinite(out_time), out_time, -9999.0)
        out_time_var.units = time_units
        out_time_var.long_name = "time coordinate of local maximum absolute outflw"
        out_index_var = data.createVariable("outflw_peak_time_index", "i2", ("lat", "lon"),
                                            fill_value=-1, zlib=True, complevel=4)
        out_index_var[:] = out_index
        out_index_var.long_name = "zero-based source-record index of local maximum absolute outflw"

        pth_var = data.createVariable("pthflw_peak_signed_sum", "f4", ("bifurcation_path",),
                                      fill_value=-9999.0, zlib=True, complevel=4)
        pth_var[:] = np.where(np.isfinite(path_result["peak"]), path_result["peak"], -9999.0)
        pth_var.units = EXPECTED_UNITS
        pth_var.long_name = "signed layer-summed pathway flow at local maximum absolute hourly mean"
        pth_var.cell_methods = "time: maximum (abs(sum(active-layer pthflw))); pthflw: mean"
        pth_time_var = data.createVariable("pthflw_peak_time", "f8", ("bifurcation_path",),
                                           fill_value=-9999.0)
        pth_time_var[:] = np.where(np.isfinite(path_result["peak_time"]), path_result["peak_time"], -9999.0)
        pth_time_var.units = time_units
        pth_index_var = data.createVariable("pthflw_peak_time_index", "i2", ("bifurcation_path",),
                                            fill_value=-1)
        pth_index_var[:] = path_result["peak_time_index"]
        data.createVariable("pthflw_active_layer_count", "i1", ("bifurcation_path",))[:] = path_result["active_layer_count"]
        data.createVariable("is_channel_bifurcation", "i1", ("bifurcation_path",))[:] = path_result["channel"].astype(np.int8)
        for name in ("ix", "iy", "jx", "jy"):
            key = f"endpoint_{name}"
            data.createVariable(key, "i4", ("bifurcation_path",))[:] = path_result["endpoints"][name]
        data.title = "Tutorial 11 Step 15 local signed peak discharge analysis"
        data.source_files = "; ".join(source_paths)
        data.source_time_coverage = f"{time_start} through {time_end} (inclusive record labels)"
        data.source_time_records = len(time_numeric)
        data.processing = (
            "For each grid cell, select signed outflw at argmax(abs(outflw)) over hourly time means. "
            "For each bifurcation path and hour, sum signed pthflw over layers with positive map width, "
            "then select the signed sum at argmax(abs(layer sum)). Missing values are masked."
        )
        data.interpretation = (
            "Cell/path peaks can occur at different times; the map is not a simultaneous flow snapshot."
        )


def draw_regional(map_dir: Path, peak: np.ndarray, geometry, map_data, path_result,
                  output: Path, color_levels: np.ndarray, linthresh: float,
                  linear_frac: float, dpi: int, figure_height=10.0):
    """Draw signed cell peaks and stored bifurcation pathways over the regional map."""
    nx, ny, _, west, east, south, north = geometry
    lon, lat, uparea, nextx, nexty, outlon, outlat, _ = map_data
    norm = VECTOR.RASTER.AsymmetricSignedLogNorm(
        float(color_levels[0]), float(color_levels[-1]), linthresh, linear_frac,
    )
    cmap = VECTOR.recenter_diverging_cmap(
        VECTOR.get_cmap("diverge_asymmetry"), norm.zero_position,
    )

    links = VECTOR.NETWORK.downstream_links(lon, lat, uparea, nextx, nexty)
    _, _, sr, sc, dr, dc, _, _, invalid = links
    if invalid:
        raise ValueError(f"Rhine nextxy has {invalid} out-of-map river links")
    outlet_valid = (
        np.isfinite(outlon) & np.isfinite(outlat) & (outlon != -9999) & (outlat != -9999)
        & (outlon >= -180) & (outlon <= 360) & (outlat >= -90) & (outlat <= 90)
    )
    valid_link = outlet_valid[sr, sc] & outlet_valid[dr, dc]
    sr, sc, dr, dc = sr[valid_link], sc[valid_link], dr[valid_link], dc[valid_link]
    main_segments = np.stack((
        np.column_stack((outlon[sr, sc], outlat[sr, sc])),
        np.column_stack((outlon[dr, dc], outlat[dr, dc])),
    ), axis=1)
    main_values = peak[sr, sc]
    areas = uparea[sr, sc]
    finite = np.isfinite(main_values) & np.isfinite(areas) & (areas > 0)
    main_segments, main_values, areas = main_segments[finite], main_values[finite], areas[finite]
    thresholds = np.quantile(np.log10(areas), [0.25, 0.5, 0.75])
    area_class = np.digitize(np.log10(areas), thresholds)
    order = np.argsort(areas, kind="stable")
    main_segments = main_segments[order]
    main_values = main_values[order]
    area_class = area_class[order]
    # Keep the full 40x32 network legible at the regional scale.
    main_widths = np.asarray([0.45, 0.62, 0.82, 1.05])[area_class] * 1.60

    endpoints = path_result["endpoints"]
    pth_values = path_result["peak"]
    pth_eligible = path_result["eligible"] & np.isfinite(pth_values)
    ix, iy, jx, jy = (endpoints[name].astype(int) - 1 for name in ("ix", "iy", "jx", "jy"))
    if np.any((ix < 0) | (ix >= len(lon)) | (jx < 0) | (jx >= len(lon)) |
              (iy < 0) | (iy >= len(lat)) | (jy < 0) | (jy >= len(lat))):
        raise ValueError("A Rhine bifurcation path endpoint lies outside the map")
    bif_segments = np.stack((
        np.column_stack((outlon[iy, ix], outlat[iy, ix])),
        np.column_stack((outlon[jy, jx], outlat[jy, jx])),
    ), axis=1)
    valid_bif = np.all(np.isfinite(bif_segments), axis=(1, 2)) & np.all(bif_segments != -9999, axis=(1, 2))
    pth_eligible &= valid_bif
    channel_paths = path_result["channel"]
    bif_width = 1.50

    extent = (west, east, south, north)
    background, bg_extent, bg_min, bg_max, _, _ = VECTOR.BACKGROUND.read_elevation_background(
        map_dir / "1min" / "1min.elevtn.nc", extent,
    )
    fig, ax = plt.subplots(figsize=(9.0 * figure_height / 10.0, figure_height))
    fig.subplots_adjust(left=0.12, right=0.82, top=0.89, bottom=0.14)
    ax.set_facecolor("#FAFAFA")
    ax.imshow(background, extent=bg_extent, origin="upper", cmap="Greys",
              vmin=bg_min, vmax=bg_max, interpolation="nearest", alpha=0.40, zorder=0)
    for index in range(4):
        selected = area_class == index
        VECTOR.add_colored_links(
            ax, main_segments[selected], main_values[selected], cmap, norm,
            main_widths[selected], zorder=3,
        )
        reverse = selected & (main_values < 0)
        for segment, value, width in zip(main_segments[reverse], main_values[reverse], main_widths[reverse]):
            VECTOR.NETWORK.add_directional_arrow(
                ax, segment[::-1], cmap(norm(value)), linewidth=width,
                start_fraction=0.42, end_fraction=0.60, size=6.5, zorder=5,
            )

    for path_mask, path_style in (
        (channel_paths & pth_eligible, (0, (2.4, 1.6))),
        (~channel_paths & pth_eligible, (0, (0.7, 1.5))),
    ):
        VECTOR.add_colored_links(
            ax, bif_segments[path_mask], np.abs(pth_values[path_mask]), cmap, norm,
            np.full(np.count_nonzero(path_mask), bif_width), linestyle=path_style, zorder=4,
        )
    for segment, value in zip(bif_segments[pth_eligible], pth_values[pth_eligible]):
        flow_segment = segment if value >= 0 else segment[::-1]
        VECTOR.NETWORK.add_directional_arrow(
            ax, flow_segment, cmap(norm(abs(value))), linewidth=bif_width,
            start_fraction=0.42, end_fraction=0.60, size=6.5, zorder=6,
        )

    ax.set_xlim(west, east)
    ax.set_ylim(south, north)
    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")
    ax.set_title(
        "Tutorial 11 Fig. 15a — Maximum River Discharge: Regional Network\n"
        "Local signed peaks; links may peak at different hours", fontsize=13,
    )
    ax.tick_params(labelsize=9)
    ax.set_aspect(1.0 / np.cos(np.deg2rad((south + north) / 2)))
    ax._river_map_extent = extent
    legend_handles = [
        Line2D([0, 0.5, 1], [0, 0, 0], color="#333333", linewidth=1.0,
               marker=">", markevery=[1], markersize=5,
               label="Main channel (arrow shows reverse flow)"),
        Line2D([0, 0.5, 1], [0, 0, 0], color="#333333", linewidth=1.0,
               linestyle=(0, (2.4, 1.6)), marker=">", markevery=[1], markersize=5,
               label="Channel bifurcation (dashed)"),
        Line2D([0, 0.5, 1], [0, 0, 0], color="#333333", linewidth=1.0,
               linestyle=(0, (0.7, 1.5)), marker=">", markevery=[1], markersize=5,
               label="Overland-only pathway (dotted)"),
    ]
    fig.legend(handles=legend_handles, loc="lower center", ncols=1,
               bbox_to_anchor=(0.46, 0.005), frameon=False, fontsize=8)
    colorbar = add_aligned_colorbar(
        fig, ax, ScalarMappable(norm=norm, cmap=cmap),
        "Signed peak discharge scale (m³/s)\nBifurcation color uses |peak|; arrow shows sign",
        extend="both",
    )
    colorbar.set_ticks(color_levels)
    colorbar.ax.set_yticklabels([VECTOR.RASTER.format_color_level(x) for x in color_levels])
    colorbar.ax.tick_params(labelsize=8)
    output.parent.mkdir(parents=True, exist_ok=True)
    VECTOR.save_panel(fig, output, dpi, figure_height=figure_height)
    plt.close(fig)
    return {
        "main_network_links_displayed": int(len(main_segments)),
        "bifurcation_paths_displayed": int(np.count_nonzero(pth_eligible)),
        "channel_bifurcation_paths": int(np.count_nonzero(pth_eligible & channel_paths)),
        "overland_only_paths": int(np.count_nonzero(pth_eligible & ~channel_paths)),
        "network_file": "map/Rhine_15min/nextxy.nc",
        "elevation_background": "map/Rhine_15min/1min/1min.elevtn.nc",
    }

def draw_aoi(map_dir: Path, extent, map_data, out_peak: np.ndarray, path_result,
             output: Path, color_levels: np.ndarray, linthresh: float,
             linear_frac: float, dpi: int, line_width_scale: float, figure_height=9.0):
    """Draw the satellite-AOI view of the same independently timed signed peaks."""
    lon, lat, uparea, nextx, nexty, outlon, outlat, bif = map_data
    west, east, south, north = extent
    norm = VECTOR.RASTER.AsymmetricSignedLogNorm(
        float(color_levels[0]), float(color_levels[-1]), linthresh, linear_frac,
    )
    cmap = VECTOR.recenter_diverging_cmap(
        VECTOR.get_cmap("diverge_asymmetry"), norm.zero_position,
    )

    links = VECTOR.NETWORK.downstream_links(lon, lat, uparea, nextx, nexty)
    _, _, sr, sc, dr, dc, _, _, invalid = links
    if invalid:
        raise ValueError(f"Rhine nextxy has {invalid} out-of-map river links")
    outlet_valid = (
        np.isfinite(outlon) & np.isfinite(outlat) & (outlon != -9999) & (outlat != -9999)
        & (outlon >= -180) & (outlon <= 360) & (outlat >= -90) & (outlat <= 90)
    )
    valid_link = outlet_valid[sr, sc] & outlet_valid[dr, dc]
    sr, sc, dr, dc = sr[valid_link], sc[valid_link], dr[valid_link], dc[valid_link]
    main_segments = np.stack((
        np.column_stack((outlon[sr, sc], outlat[sr, sc])),
        np.column_stack((outlon[dr, dc], outlat[dr, dc])),
    ), axis=1)
    main_values = out_peak[sr, sc]
    areas = uparea[sr, sc]
    finite = np.isfinite(main_values) & np.isfinite(areas) & (areas > 0)
    main_segments, main_values, areas = main_segments[finite], main_values[finite], areas[finite]
    thresholds = np.quantile(np.log10(areas), [0.25, 0.5, 0.75])
    area_class = np.digitize(np.log10(areas), thresholds)
    order = np.argsort(areas, kind="stable")
    main_segments, main_values, area_class = main_segments[order], main_values[order], area_class[order]
    main_widths = np.asarray([0.55, 0.78, 1.08, 1.48])[area_class] * line_width_scale

    endpoints = path_result["endpoints"]
    path_ids = path_result["path_ids"]
    pth_values = path_result["peak"]
    pth_eligible = path_result["eligible"] & np.isfinite(pth_values)
    ix, iy, jx, jy = (endpoints[name].astype(int) - 1 for name in ("ix", "iy", "jx", "jy"))
    if np.any((ix < 0) | (ix >= len(lon)) | (jx < 0) | (jx >= len(lon)) |
              (iy < 0) | (iy >= len(lat)) | (jy < 0) | (jy >= len(lat))):
        raise ValueError("A Rhine bifurcation path endpoint lies outside the map")
    bif_segments = np.stack((
        np.column_stack((outlon[iy, ix], outlat[iy, ix])),
        np.column_stack((outlon[jy, jx], outlat[jy, jx])),
    ), axis=1)
    valid_bif = np.all(np.isfinite(bif_segments), axis=(1, 2)) & np.all(bif_segments != -9999, axis=(1, 2))
    pth_eligible &= valid_bif
    channel_paths = path_result["channel"]
    background_path = map_dir / "1min" / "1min.elevtn.nc"
    background, bg_extent, bg_min, bg_max, _, _ = VECTOR.BACKGROUND.read_elevation_background(
        background_path, extent,
    )

    fig, ax = plt.subplots(figsize=(9.5 * figure_height / 9.0, figure_height))
    fig.subplots_adjust(left=0.13, right=0.79, top=0.88, bottom=0.23)
    ax.set_facecolor("#FAFAFA")
    ax.imshow(background, extent=bg_extent, origin="upper", cmap="Greys",
              vmin=bg_min, vmax=bg_max, interpolation="nearest", alpha=0.60, zorder=0)
    for index in range(4):
        selected = area_class == index
        VECTOR.add_colored_links(
            ax, main_segments[selected], main_values[selected], cmap, norm,
            main_widths[selected], zorder=3,
        )
        reverse = selected & (main_values < 0)
        for segment, value, width in zip(main_segments[reverse], main_values[reverse], main_widths[reverse]):
            VECTOR.NETWORK.add_directional_arrow(
                ax, segment[::-1], cmap(norm(value)), linewidth=width,
                start_fraction=0.42, end_fraction=0.60, size=6.5, zorder=5,
            )

    bif_width = 1.35 * line_width_scale
    bif_display = np.abs(pth_values)
    for path_mask, path_style in (
        (channel_paths & pth_eligible, (0, (2.4, 1.6))),
        (~channel_paths & pth_eligible, (0, (0.7, 1.5))),
    ):
        VECTOR.add_colored_links(
            ax, bif_segments[path_mask], bif_display[path_mask], cmap, norm,
            np.full(np.count_nonzero(path_mask), bif_width), linestyle=path_style, zorder=4,
        )
    for segment, value in zip(bif_segments[pth_eligible], pth_values[pth_eligible]):
        flow_segment = segment if value >= 0 else segment[::-1]
        VECTOR.NETWORK.add_directional_arrow(
            ax, flow_segment, cmap(norm(abs(value))), linewidth=bif_width,
            start_fraction=0.42, end_fraction=0.60, size=7.0, zorder=6,
        )

    ax.set_xlim(west, east)
    ax.set_ylim(south, north)
    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")
    ax.set_title(
        "Tutorial 11 Fig. 15b — Maximum River Discharge: Area of Interest\n"
        "Local signed peaks; link and path peaks may occur at different hours",
        fontsize=13,
    )
    ax.tick_params(labelsize=9)
    ax.set_aspect(1.0 / np.cos(np.deg2rad((south + north) / 2)))
    ax._river_map_extent = extent
    legend_handles = [
        Line2D([0, 0.5, 1], [0, 0, 0], color="#333333", linewidth=1.2,
               marker=">", markevery=[1], markersize=5,
               label="Main channel (arrow shows reverse flow)"),
        Line2D([0, 0.5, 1], [0, 0, 0], color="#333333", linewidth=1.2,
               linestyle=(0, (2.4, 1.6)), marker=">", markevery=[1], markersize=5,
               label="Channel bifurcation (dashed)"),
        Line2D([0, 0.5, 1], [0, 0, 0], color="#333333", linewidth=1.2,
               linestyle=(0, (0.7, 1.5)), marker=">", markevery=[1], markersize=5,
               label="Overland-only pathway (dotted)"),
    ]
    fig.legend(handles=legend_handles, loc="lower center", ncols=1,
               bbox_to_anchor=(0.46, 0.025), frameon=False, fontsize=9)
    colorbar = add_aligned_colorbar(
        fig, ax, ScalarMappable(norm=norm, cmap=cmap),
        "Signed peak discharge scale (m³/s)\nBifurcation color uses |peak|; arrow shows sign",
        extend="both",
    )
    colorbar.set_ticks(color_levels)
    colorbar.ax.set_yticklabels([VECTOR.RASTER.format_color_level(x) for x in color_levels])
    colorbar.ax.tick_params(labelsize=8)
    output.parent.mkdir(parents=True, exist_ok=True)
    VECTOR.save_panel(fig, output, dpi, figure_height=figure_height)
    plt.close(fig)
    return {
        "main_network_links_displayed": int(len(main_segments)),
        "bifurcation_paths_displayed": int(np.count_nonzero(pth_eligible)),
        "channel_bifurcation_paths": int(np.count_nonzero(pth_eligible & channel_paths)),
        "overland_only_paths": int(np.count_nonzero(pth_eligible & ~channel_paths)),
        "elevation_background": "map/Rhine_15min/1min/1min.elevtn.nc",
    }


def main() -> None:
    """Resolve Step contracts, calculate/save local peaks, then draw the two map views."""

    #*** 1. Resolve configured model/map/domain contracts
    args = parse_args()
    tutorial_dir = args.tutorial_dir.resolve()
    step14_path = args.step14_metadata.resolve()
    domain_path = args.domain_metadata.resolve()
    step14 = read_metadata(step14_path)
    domain = read_metadata(domain_path)
    outflw_path, pthflw_path, map_dir = resolve_step14_inputs(step14, tutorial_dir, ROOT)
    configured_map_dir = args.map_dir.resolve()
    if configured_map_dir != map_dir.resolve():
        raise ValueError(
            f"Shell map directory {configured_map_dir} differs from Step 14 metadata {map_dir}"
        )
    geometry = read_geometry(map_dir / "params.txt")
    nx, ny, _, map_west, map_east, map_south, map_north = geometry
    sim_bbox = domain["simulation"]["domain"]["bbox_west_south_east_north"]
    expected_sim_extent = (map_west, map_south, map_east, map_north)
    if not np.allclose(sim_bbox, expected_sim_extent, rtol=0, atol=1e-6):
        raise ValueError(f"Step 2 simulation domain {sim_bbox} does not match the map edges")
    west, south, east, north = domain["satellite_analysis"]["domain"]["bbox_west_south_east_north"]
    aoi = (west, east, south, north)
    if west < map_west or east > map_east or south < map_south or north > map_north:
        raise ValueError("Step 2 satellite analysis domain extends outside Rhine map")
    expected_records = int(step14["simulation"]["period_hours"])

    #*** 2. Calculate independently timed signed local peaks
    map_data = read_map_data(map_dir)
    lon, lat = map_data[0], map_data[1]
    if (lon.size, lat.size) != (nx, ny):
        raise ValueError("Rhine map NetCDF dimensions do not match params.txt")
    out_peak, out_index, out_time, out_values, time_numeric, dates, valid_out_records, all_missing_cells = read_outflow(
        outflw_path, geometry, expected_records,
    )
    pth_result = read_bifurcation_peak(
        pthflw_path, map_data[7], time_numeric, expected_records,
    )
    levels = VECTOR.RASTER.parse_color_levels(args.color_levels)
    VECTOR.RASTER.AsymmetricSignedLogNorm(
        float(levels[0]), float(levels[-1]), args.linthresh, args.linear_frac,
    )

    #*** 3. Save derived peak/time fields
    with Dataset(outflw_path) as source:
        time_units = source.variables["time"].units
    analysis_path = args.analysis_file.resolve()
    write_analysis(
        analysis_path, lon, lat, time_numeric, time_units, out_peak, out_index,
        out_time, pth_result, [str(outflw_path), str(pthflw_path)],
        dates[0].strftime("%Y-%m-%d %H:%M:%S"), dates[-1].strftime("%Y-%m-%d %H:%M:%S"),
    )

    #*** 4. Render regional/AOI views and report diagnostics
    regional_stats = draw_regional(
        map_dir, out_peak, geometry, map_data, pth_result,
        args.regional_figure.resolve(), levels, args.linthresh,
        args.linear_frac, args.dpi, args.regional_height,
    )
    aoi_stats = draw_aoi(
        map_dir, aoi, map_data, out_peak, pth_result, args.aoi_figure.resolve(),
        levels, args.linthresh, args.linear_frac, args.dpi, line_width_scale=1.1, figure_height=args.aoi_height,
    )
    qfinite = out_values.compressed()
    valid_peaks = out_peak[np.isfinite(out_peak)]
    pth_peaks = pth_result["peak"][pth_result["eligible"]]
    print(json.dumps({
        "input_records": expected_records,
        "first_time": dates[0].strftime("%Y-%m-%d %H:%M:%S"),
        "last_time": dates[-1].strftime("%Y-%m-%d %H:%M:%S"),
        "input_valid_outflw_values": valid_out_records,
        "all_missing_grid_cells": all_missing_cells,
        "outflw_peak_valid_cells": int(valid_peaks.size),
        "outflw_peak_min": float(valid_peaks.min()),
        "outflw_peak_max": float(valid_peaks.max()),
        "outflw_peak_negative_cells": int(np.count_nonzero(valid_peaks < 0)),
        "outflw_raw_negative_values": int(np.count_nonzero(qfinite < 0)),
        "pthflw_active_paths": int(np.count_nonzero(pth_result["eligible"])),
        "pthflw_channel_paths": int(np.count_nonzero(pth_result["eligible"] & pth_result["channel"])),
        "pthflw_overland_only_paths": int(np.count_nonzero(pth_result["eligible"] & ~pth_result["channel"])),
        "pthflw_peak_min": float(pth_peaks.min()),
        "pthflw_peak_max": float(pth_peaks.max()),
        "pthflw_peak_negative_paths": int(np.count_nonzero(pth_peaks < 0)),
        "regional_grid": [nx, ny],
        "simulation_extent_wsen": [map_west, map_south, map_east, map_north],
        "aoi_extent_wsen": [west, south, east, north],
        "analysis_file": str(analysis_path),
        "figures": [str(args.regional_figure.resolve()), str(args.aoi_figure.resolve())],
        "regional": regional_stats,
        "aoi": aoi_stats,
    }, indent=2))


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, RuntimeError, KeyError) as exc:
        raise SystemExit(f"Tutorial 11 Step 15 visualization failed: {exc}") from exc

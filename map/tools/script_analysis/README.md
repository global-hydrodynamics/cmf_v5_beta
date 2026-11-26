# Portable map-analysis toolkit

`script_analysis/` contains educational command-line examples and their generated outputs. The examples call the maintained Python programs under `map/tools/code/`; the original Fortran implementations are preserved under `map/tools/code/legacy_fortran/`.

## Run the Python tools

No compilation or code symlink is required. `get_river_point_info.sh` resolves the shared Python program through `CMF_V50_ROOT`.

`a00-link_codes.sh` is retained as a legacy convenience for users who invoke preserved Fortran reference programs directly; the migrated Shell workflows do not use it.

Set `CMF_V50_ROOT` to the repository root before running the generic command or sample script.

Python scripts are portable across supported environments and are not copied into map-local directories. Existing Fortran executables, if any, are not modified by the Python workflow.

## Output directory

Existing output files owned by the Python programs are replaced by default on
rerun. Set an alternate `OUT_DIR` to retain earlier results; unrelated files in
the output directory are left untouched.

`a03` and `a04` write their files under `script_analysis/out_analysis/` by default. `a05` prints its diagnostic to the terminal and writes a dropped-path CSV there when requested. The scripts that use `OUT_DIR="out_analysis"` create that directory when writing output. Set `OUT_DIR="../out_analysis"` to save those outputs under the map root instead. The default and map-root output directories are ignored by Git.

`a02-sample_calc_upbasin.sh` writes `upbasin-sample.nc` directly under `script_analysis/`; `a03` writes threshold-labeled subbasin and color rasters; `a04` writes a text table of river-node coordinate pairs. Call `a05` with `--csv <filename>` to save dropped pathways; relative CSV filenames go under `OUT_DIR`.

## Direct command-line use

Run commands from the map-local `script_analysis/` directory so their `../` map-input paths resolve:

```sh
cd map/mekong_15min/script_analysis
./get_river_point_info.sh xy 62 93
./get_river_point_info.sh latlon 11.579 104.946
./get_river_point_info.sh xy 62 93 > river_point_info.txt
./calc_upbasin.sh xy 62 93
./calc_upbasin.sh xy 62 93 ./upbasin-sample.nc
./a02-sample_calc_upbasin.sh
python3 ../../tools/code/analysis_upbasin.py 62 93
python3 ../../tools/code/analysis_subbasin.py 50000
python3 ../../tools/code/analysis_river_node_latlon.py 90 110 5 35
```

`analysis_upbasin` and `analysis_subbasin` accept optional output paths; without them, the direct executables use their own documented analysis filenames. The example scripts provide explicit output paths under `OUT_DIR` so they do not replace standard products.

| Executable | Arguments and output |
| --- | --- |
| `get_river_point_info.sh` | `xy IX IY` or `latlon LAT LON`; reads NetCDF maps by default and prints cell and catchment details to standard output. `xy` uses one-based Fortran grid indices; `latlon` takes latitude then longitude in degrees. Lat/lon lookup uses high-resolution `catmxy` assignments in 15sec, then 1min NetCDF tiles when available, then coarse map-grid containment. |
| `calc_upbasin.sh` | `xy IX IY [OUTPUT.nc]`; accepts one-based indices only, writes an integer NetCDF mask, and defaults to `../upbasin-IX-IY.nc`. |
| `analysis_upbasin.py` | `IX IY [OUTPUT]`; the existing Python interface used by independent workflows, including `script_params/x02-upbasin.sh`. |
| `analysis_subbasin` | `THRESHOLD_KM2 [SUBBSN_OUTPUT SUBCOL_OUTPUT]`; its default outputs are threshold-labeled rasters in the map root. The threshold applies to upstream-area increases across links, not a simple basin-area cutoff. |
| `analysis_river_node_latlon` | `WEST EAST SOUTH NORTH` in degrees; prints directed connections between CaMa-Flood river-cell representative points. These points are not a high-resolution river centerline. |

## Example shell scripts

The `a01-sample_get_river_point_info.sh` script explains and runs both generic query forms. Its report is printed to standard output; use ordinary Shell redirection to save it. The `a02`–`a05` scripts demonstrate the other analysis programs; most run from `script_analysis/`, while `a05` runs from the map root because its diagnostic reads map files relative to that directory.

- [`get_river_point_info.sh`](get_river_point_info.sh) is the generic river-point query command.
- [`a01-sample_get_river_point_info.sh`](a01-sample_get_river_point_info.sh) demonstrates both supported coordinate modes with actual analysis results.
- [`calc_upbasin.sh`](calc_upbasin.sh) calculates an upstream mask for an explicitly selected one-based `xy` cell. It writes NetCDF by default, overwrites an existing target, and accepts an optional output path relative to `script_analysis/`.
- [`a02-sample_calc_upbasin.sh`](a02-sample_calc_upbasin.sh) explains and runs the generic command with cell (62, 93), writing `./upbasin-sample.nc`.
- [`a03-subbasin.sh`](a03-subbasin.sh) demonstrates an exploratory 50,000 km2 threshold.
- [`a04-river_node_latlon.sh`](a04-river_node_latlon.sh) extracts connections in a configured geographic rectangle.
- [`a05-mpi_dropped_bifurcation.sh`](a05-mpi_dropped_bifurcation.sh) checks an existing `mpireg-N.bin` and can write dropped pathways as CSV using `analysis_mpi_dropped_bifurcation.py`.

Before calculating a basin, use `get_river_point_info.sh` to inspect and confirm the target cell; geographic coordinates are deliberately not accepted by `calc_upbasin.sh`. Its mask values are 1 for cells draining to the selected cell (including that cell), 0 for other valid river cells, and -9999 outside the modeled river network. `script_params/x02-upbasin.sh` remains a separate GRDC-station example: it selects an allocated station and calls the Python IX/IY/OUTPUT interface directly, retaining its existing output behavior. The generic command and sample do not replace standard preparation workflows. `script_params/s05-subbasin.sh` and `x02-upbasin.sh` call shared Python programs directly for their distinct purposes. See the [parameter workflow guide](../script_params/README.md#river-network-analysis).

The separate `analysis_mpi_region_color` utility writes optional `bsncol_mpi-N.bin` maps; x01 does not invoke it. See the [MPI map-preparation guide](../script_params/README.md#mpi-map-preparation).

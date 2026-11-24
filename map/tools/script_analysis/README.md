# Portable map-analysis toolkit

`script_analysis/` contains educational command-line examples and their generated outputs. The examples call the maintained Python programs under `map/tools/code/`; the original Fortran implementations are preserved under `map/tools/code/legacy_fortran/`.

## Run the Python tools

No compilation or code symlink is required. The scripts resolve `map/tools/code/` from their own location or from `CMF5_ROOT`; set `PYTHON_CMD` when a non-default Python interpreter is needed.

`a00-link_codes.sh` is retained as a legacy convenience for users who invoke preserved Fortran reference programs directly; the migrated Shell workflows do not use it.

From a copied map-local script directory, set `CMF5_ROOT` to the repository root if the relative shared-code path is not available.

Python scripts are portable across supported environments and are not copied into map-local directories. Existing Fortran executables, if any, are not modified by the Python workflow.

## Output directory

Existing output files owned by the Python programs are replaced by default on
rerun. Set an alternate `OUT_DIR` to retain earlier results; unrelated files in
the output directory are left untouched.

The `a01`–`a04` examples write their files under `script_analysis/out_analysis/` by default. `a05` prints its diagnostic to the terminal and writes a dropped-path CSV there when requested. Each script has an editable `OUT_DIR="out_analysis"` setting near the top and creates that directory when it writes output. Set `OUT_DIR="../out_analysis"` to save under the map root instead. The default and map-root output directories are ignored by Git.

`a01` writes a text report; `a02` writes an outlet-specific upstream mask and report; `a03` writes threshold-labeled subbasin and color rasters; `a04` writes a text table of river-node coordinate pairs. Call `a05` with `--csv <filename>` to save dropped pathways; relative CSV filenames go under `OUT_DIR`.

## Direct command-line use

Run most programs from the map-local `script_analysis/` directory so their `../` map-input paths resolve:

```sh
cd map/mekong_15min/script_analysis
python3 ../../tools/code/analysis_river_point_info.py xy 62 93
python3 ../../tools/code/analysis_upbasin.py 62 93
python3 ../../tools/code/analysis_subbasin.py 50000
python3 ../../tools/code/analysis_river_node_latlon.py 90 110 5 35
```

`analysis_upbasin` and `analysis_subbasin` accept optional output paths; without them, the direct executables use their own documented analysis filenames. The example scripts provide explicit output paths under `OUT_DIR` so they do not replace standard products.

| Executable | Arguments and output |
| --- | --- |
| `analysis_river_point_info` | `xy IX IY` or `latlon LAT LON`; prints cell and catchment details. Lat/lon lookup may use `15sec/` or `1min/` `catmxy.bin`. |
| `analysis_upbasin` | `IX IY [OUTPUT]`; indices are one-based Fortran map cells. Its default output is a coordinate-labeled mask in the map root. |
| `analysis_subbasin` | `THRESHOLD_KM2 [SUBBSN_OUTPUT SUBCOL_OUTPUT]`; its default outputs are threshold-labeled rasters in the map root. The threshold applies to upstream-area increases across links, not a simple basin-area cutoff. |
| `analysis_river_node_latlon` | `WEST EAST SOUTH NORTH` in degrees; prints directed connections between CaMa-Flood river-cell representative points. These points are not a high-resolution river centerline. |

## Example shell scripts

The `a01`–`a05` scripts show the working directory and print each command before invoking its Python program. Their settings are editable near the beginning. Most examples run from `script_analysis/`; `a05` runs from the map root because its diagnostic reads map files relative to that directory. All migrated examples invoke the corresponding `.py` file through `PYTHON_CMD`.

- [`a01-river_point_info.sh`](a01-river_point_info.sh) demonstrates grid-index or geographic queries.
- [`a02-upbasin.sh`](a02-upbasin.sh) creates an exploratory mask for one configured cell.
- [`a03-subbasin.sh`](a03-subbasin.sh) demonstrates an exploratory 50,000 km2 threshold.
- [`a04-river_node_latlon.sh`](a04-river_node_latlon.sh) extracts connections in a configured geographic rectangle.
- [`a05-check_mpi_bifurcation.sh`](a05-check_mpi_bifurcation.sh) checks an existing `mpireg-N.bin` and can write dropped pathways as CSV.

These independent examples do not replace standard preparation workflows. `script_params/s06-subbasin.sh` and `s07-upbasin.sh` call the shared Python programs directly and write their intended standard/sample products. See the [parameter workflow guide](../script_params/README.md#river-network-analysis).

The separate `analysis_mpi_region_color` utility writes optional `bsncol_mpi-N.bin` maps; s04 does not invoke it. See the [MPI map-preparation guide](../script_params/README.md#mpi-map-preparation).

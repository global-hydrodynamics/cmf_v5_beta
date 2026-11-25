# CaMa-Flood v5 map tools

`map/tools/` contains shared v5 map-processing programs and reusable workflow templates. It is separate from the legacy v4 tools under `map/src/`. The GitHub repository also distributes `map/mekong_15min/` as its official development/test sample; the global source map `glb_15min` and some high-resolution/runoff inputs are distributed separately in CaMa-Flood data packages.

The Mekong map-local regionalization scripts are maintainer-operated **sample-preparation tools**. They create or refresh the distributed sample from package-only global source data. They are not automated tests. Adding or updating a sample does not constitute scientific validation of its river network or hydraulic properties.

## NetCDF-first products

Maintained Python map tools and model workflows use individual NetCDF products at the map root and NetCDF high-resolution tiles in `<map>/<resolution>/`. The shared `mod_map_io.py` layer selects NetCDF by default; use `--map-format binary` only for an explicit legacy Binary workflow. Generated map products use NetCDF by default. The dedicated INPMAT schema uses `inpx`, `inpy`, and `inpa` with `NX`, `NY`, `INPN`, `NXIN`, `NYIN`, `NLFP`, and domain metadata; it is kept separate from ordinary raster conversion. Binary products and their `.ctl` files belong under `binary/`, COG derivatives under `COG/`. The [architecture and migration procedure](../../docs/map_data_tools_plan.md#approved-v5-map-data-architecture) is authoritative.

## Shared code and execution

- `code/` contains maintained Python map-processing programs, shared Python modules, and the preserved Fortran reference sources under `legacy_fortran/`.
- `script_region/` is the reusable v5 regional-map preparation template.
- `script_params/` is the map-preparation and parameterization workflow family: channel parameters, user-configured runoff matrices, bifurcation/MPI setup, and gauge/dam allocation templates.
- `script_analysis/` is for independent map analysis and diagnostic workflows.

The map-tool Shell workflows invoke the maintained Python programs under `code/` directly; they do not require compiling or linking map executables. The original Fortran implementations are retained under `code/legacy_fortran/` for reference and regression comparisons. Script families remain `script_region/`, `script_params/`, `script_analysis/`, and `script_format_conv/`. `map/src/` is the separate historical v4 tool tree.

For maintained Fortran, Python and Shell tools, follow the
[shared preprocessing code conventions](../../docs/preprocessing_code_conventions.md)
and [map instructions](../AGENTS.md). These adapt portable principles from
`src_main/` while preserving local tool style, names, file contracts and
standalone responsibilities. Keep map metadata in the
[variable registry](../../variable_table/map_variables.csv), not duplicated
source tables.

Shell workflows hold user settings, choose working directories, sequence commands, and show progress. They call the maintained Python programs in `code/` directly; no map-tool build is required. Set `PYTHON_CMD` when Python is not available as `python3`. Map-local copies can set `CMF5_ROOT` to find the shared programs when the repository-relative path is unavailable. Existing output files owned by these Python tools are replaced by default on rerun; where provided, `--no-overwrite` preserves existing output. Inputs and unrelated files are not removed. The v5 map workflow scripts use consistent ASCII `[STEP]` and `[SUCCESS]` banners and a prominent `ERROR` banner on failure. Each script formats messages itself with a POSIX exit trap; there is no shared message helper. See the [shell-script guidance](../../AGENTS.md#shell-script-design-principles).

For example, the channel workflow sets its parameters once, selects the map-root working directory, and calls each program directly:

```sh
cd "$MAP_DIR"
"$PYTHON_CMD" "$OUTCLM" "$TYPE" "$INTERP" "$DIMINFO" "$CROFBIN"
"$PYTHON_CMD" "$RIVWTH" "$TYPE" "$DIMINFO" "$HC" "$HP" "$HO" "$HMIN" \
    "$WC" "$WP" "$WO" "$WMIN"
"$PYTHON_CMD" "$MERIT" "$DIMINFO"
```

The [runoff preset workflow](script_runoff_preset/README.md) computes a 365-day runoff climatology and long-term mean from source NetCDF, then applies a grid-only eight-neighbor daily minimum correction and exports identical float32 NetCDF/Binary in mm/s. It deliberately uses no river map or Input Matrix. Generated files under its dedicated output directory are overwritten on rerun; the canonical product in `map/data/` is not an output of this workflow.

The general-purpose runoff input-matrix generator is `param_inpmat_generate.py`. Its map-local wrapper template is [`script_params/s03-generate_inpmat.sh`](script_params/s03-generate_inpmat.sh); copy it into a target map's `script_params/` directory before configuring and running it. One `ROFFTAG` derives the paired `diminfo_<ROFFTAG>.txt` and `inpmat_<ROFFTAG>.nc` names. `HIRES_TAG` independently selects the high-resolution map source. The standard s03 grid is `ERA5land_global` (0.1 degree, 3600 × 1801), matching converted `inp/repo-ERA5land-glb_2day/runoff_200001.nc`. Its spatial tag is independent of the runoff period and model-map name: regenerate the matrix for each model map, but reuse it for longer forcing with identical coordinates/order on that same map. The resulting `diminfo_ERA5land_global.txt` and `inpmat_ERA5land_global.nc` are not generated by this settings update. This generator supports user-selected regular runoff grids and is distinct from `region_default_inpmat.py`, which creates the standard climatology matrix distributed with prepared maps. See the [parameter workflow guide](script_params/README.md) for required inputs, configuration, outputs, and regression status.

The optional flow-gauge, dam, and level-gauge allocation workflows are implemented as shared `allocate_*.py` programs and map-local wrapper templates in `script_params/`. They map input locations already allocated on MERIT Hydro onto CaMa-Flood catchments; configure the input list and explicit single-area `HIRES_TAG` before running. See the [allocation workflow guide](script_params/README.md#allocation-workflows) for files, columns, classifications, and regression limits.

The v5 [`script_params/s01-channel_params.sh`](script_params/s01-channel_params.sh) runs annual mean discharge estimation, power-law channel parameterization, and MERIT Hydro width merging only. It derives the standard paired `diminfo_test-1deg.txt` and `inpmat_test-1deg.nc` from `ROFFTAG=test-1deg`. The v5 tools include `param_channel_calc_outclm.py`, `param_channel_calc_rivwth.py`, and `param_channel_set_merit_width.py`; they preserve the legacy calculations and write the alternate merged width as `rivwth_merit.nc`. The legacy `gosh/` simulation scripts and the historical v4 tools under `map/src/` are preserved; v5 naming and workflow changes belong under `map/tools/`. The current model reader does not automatically select the v5 alternate output. The repository now tracks the annual-mean ELSE_GPCC sample at `map/data/ELSE_GPCC_clm-1981-2010.one`; the channel regression uses it by default. This maintainer-directed inclusion applies to this file and does not establish terms for other ELSE_GPCC products or derivatives.

The v5 [`script_params/s02-bifurcation.sh`](script_params/s02-bifurcation.sh) generates standard non-MPI bifurcation parameters and basin-connectivity products after `rivhgt.nc` is available. The Python generator writes finalized `bifprm.csv`; the independent `convert_bifprm_csv_to_netcdf.py` creates `bifprm.nc` from that table before the basin processor runs. The CSV remains at the map root. It preserves the legacy default `BIFLAYER=5` and filtered source-row order, and writes the standard products `bifprm.csv`, `bifprm.nc`, `bifbsn.nc`, and `bifcol.nc`. If `BIFLAYER` exceeds the layer count recorded in `bifori.txt`, the program warns and uses the available layer count. `bifcol.nc` is always generated because it is routinely used to visualize the merged basin map. Its palette is limited to colors 2–10 (with color 1 reserved for single-cell basins); if all candidate colors are occupied by neighbors, the code falls back to color 10, so neighboring basins can share a display color. This affects visualization only. With `s02-bifurcation.sh check_map`, `param_bif_set_params` additionally writes `check_bif_dphwth.nc` (depth, then width) and `param_bif_set_basin` writes `check_bif_bsnmod.nc` (basin modification class, then connection-point class). Both are optional inspection products, not simulation inputs; the corresponding variable rows use `sub_id=C` in [`variable_table/map_variables.csv`](../../variable_table/map_variables.csv) to mark that these variables are emitted only when explicitly requested. Without `check_map`, they are neither created nor overwritten; existing diagnostic files may therefore be stale. The v5 tool no longer creates separate `bifmod.bin` or `bpoint.bin`; those remain in the preserved legacy v4 tree. The v5 workflow does not include obsolete `biftag.bin`. MPI-specific processing is handled by [`s04-mpi_map_setup.sh`](script_params/README.md#mpi-map-preparation). Its basin-aggregation program writes `bifcol_mpi.nc` from the MPI-aggregated basins, independently of partition count; the colors may vary between `normal` and `MaxMPI`. The region partitioner writes only `mpireg-N.nc`, and s04 runs connectivity analysis for the configured default count. `analysis_mpi_region_color` remains an optional manual utility that writes `bsncol_mpi-N.nc` to visualize a selected region map; s04 does not invoke it. The wrappers invoke the Python programs directly and set the map-root and map-local working directories required by them.

Run the isolated s02 migration regression with:

```sh
python3 -B -m unittest map.tools.tests.test_bifurcation_migration -v
```

It compiles the shared and legacy tools in temporary directories and compares their outputs using the committed Mekong sample, without overwriting tracked map files. The s01-to-s02 chain uses the Git-tracked `map/data/ELSE_GPCC_clm-1981-2010.one` by default; set `CMF_RUNOFF_CLIMATOLOGY=/path/to/compatible-runoff.one` only to test an alternate compatible dataset. This is migration regression evidence, not scientific validation.

Regional processing is provided by the maintained Python programs under `code/`; no build is required. The focused optional-map check is:

```sh
python3 -B -m unittest map.tools.tests.test_region_cut_domain_optional_maps -v
```

Map-local scripts do not compile tools. Regional and parameter templates resolve shared Python programs from the repository-relative `map/tools/code/` path or from `CMF5_ROOT`, and set the CWD required by each utility. See the [regional workflow guide](script_region/README.md) and [parameter workflow guide](script_params/README.md) for configuration, inputs, outputs, and limitations.

## Regional map preparation

The reusable `script_region/` template is intended for preparing a new regional map: copy it into a target map directory, configure `SOURCE` and geographic bounds in `s01-regional_map.sh`, then run the script from the copied map-local `script_region/` directory. The workflow crops the base map, filters bifurcation paths, derives network products, crops supported high-resolution layers, and creates the standard annual-runoff-climatology input mapping matrix when a supported high-resolution map is available. `region_default_inpmat.py` produces this distributed map product for channel cross-section parameter estimation; it is distinct from the user-configured runoff-grid matrices generated later by `param_inpmat_generate.py`. Exact outputs depend on source-map contents and settings.

The sample-local script directory under `map/mekong_15min/` has a different operational role: it records the maintainer's procedure for preparing the official sample. Its original global map input is provided by the distribution package, not GitHub. Do not run it in CI or point its output at the tracked sample when ordinary testing or user workflow examples are intended.

## GrADS CTL files

CTL generation is a separate step; `s01-regional_map.sh` does not call it. Run `s02-write_ctl.sh` from the map-local `script_region/` directory. The wrapper scans binaries in the base map and immediate high-resolution subdirectories with `location.txt`. The generator reads base geometry from `params.txt`, high-resolution geometry from `location.txt`, and registered binary layouts from [`variable_table/map_variables.csv`](../../variable_table/map_variables.csv). The regionalization input matrix uses the standard `ROFFTAG=test-1deg` pair: simulation dimensions in `diminfo_*.txt`, input-to-model cell correspondence in `inpmat_*.bin`. The generator checks registered layouts and binary sizes, and follows the legacy `yrev little_endian` and cell-center conventions.

```sh
./s02-write_ctl.sh --dry-run
./s02-write_ctl.sh
```

The wrapper replaces CTLs by default; use `--no-overwrite` to retain existing descriptors. `variable_table/map_variables.csv` is the common variable registry; [`map_metadata_spec.md`](../../variable_table/map_metadata_spec.md) defines its schema and the relationship between map metadata files.

### Missing and special values

The registry's `missing_value` field contains one numeric sentinel stored in the binary. `special_values` describes meaningful codes such as river mouths, boundaries, sinks, and categories; the generator does not treat these values as missing or append them to CTL descriptions. Leave `missing_value` blank when the stored sentinel is unknown.

For a blank value, the generator uses a provisional CTL-only default and warns for each affected binary: `float32=-9999`, `int32=-9999`, `int16=-9999`, `int8=-9`. The run summary includes the number of files that used a fallback. The defaults do not update the CSV or binary data. Explicit values are checked for numeric validity, integer form and storage range as applicable. If variables in one binary resolve to different missing values, the generator refuses that file.

GrADS documents byte input as unsigned (`-1,40,1`), two-byte signed input as `-1,40,2,-1`, and four-byte integer input as `-1,40,4`; its documented byte format has no signed one-byte mode. CaMa-Flood int8 binaries are signed, so the generator writes their signed sentinel `-9` as unsigned-byte `undef 247` and leaves the binary unchanged. Other negative int8 data codes display as unsigned values (for example `-1` as `255`). Use a signed-aware tool when those original codes matter. See [GrADS Variable Formats](https://sources.debian.org/data/main/g/grads/3%3A2.2.1-1/doc/variableformats.html) and the [GrADS descriptor file format](https://sources.debian.org/data/main/g/grads/2%3A2.0.2-3/doc/descriptorfile.html#VARS).

## GitHub-only automated tests

Routine tests use code and data included in the repository. They do not execute `s01-regional_map.sh` and do not require or download `glb_15min`. The Mekong sample validator checks required sample files and validates type/dimensions/size for binaries listed in `variable_table/map_variables.csv`; unregistered user-created matrices and analysis binaries are allowed and skipped by that registry-based size check. At least one registered binary must still be checked, and a size mismatch in any registered binary fails validation.

```sh
python3 -B -m unittest map.tools.tests.test_generate_ctl -v
python3 -B map/tests/validate_map_variables.py
python3 -B map/tests/validate_mekong_sample.py
python3 -B -m unittest map.tools.tests.test_mekong_ctl_integration -v
python3 -B -m unittest map.tools.tests.test_mpi_map_tools -v
python3 -B -c 'from pathlib import Path; [compile(p.read_text(), str(p), "exec") for p in [Path("map/tools/code/generate_ctl.py"), *Path("map/tools/tests").glob("*.py"), *Path("map/tests").glob("*.py")]]'
for script in map/tools/script_region/*.sh; do sh -n "$script"; done
for script in map/tools/script_params/*.sh; do sh -n "$script"; done
for script in map/tools/script_analysis/*.sh; do sh -n "$script"; done
PYTHONPATH=map/tools/tests .venv/bin/python -B -m unittest map.tools.tests.test_shell_python_migration -v
```

The synthetic unit tests cover CTL layout, multi-record/multi-layer inputs, errors, fallbacks, conflicting sentinel declarations, overwrite handling, and integer types. A separate small synthetic crop test checks that optional `catmpx.bin` and `class.bin` are copied over the requested rectangle when present and remain optional when absent. The Mekong integration test copies all sample binaries and needed metadata to a temporary tree and invokes the actual map-local CTL wrapper there; it verifies descriptors for base and high-resolution data without modifying the tracked CTLs. The sample validator checks its dimensions, binary inventory, type/layout sizes, workflow status, and registry mapping. The registry validator checks the new metadata columns and numeric sentinel ranges. CI runs these source-only and committed-sample checks; the synthetic Fortran crop test runs when `gfortran` is available. No sample-preparation script or external map dataset is run or downloaded.

**PASS** means the check ran and met its criteria. **FAIL** means it ran but criteria were violated or an implementation defect prevented the required result. **SKIP** is only for an explicitly optional compiler/toolchain that is unavailable; missing package-only map data is not a test and is not reported as SKIP. A successful CTL or file-integrity check confirms metadata/layout compatibility only, not scientific correctness. Scientific validation is a separate activity.

The MPI utility test compiles the shared MPI tools into a temporary directory, runs normal-mode preprocessing against copies of the tracked Mekong map inputs, checks repeatability, layer-independent pathway sorting (including a same-key tie case), report/CSV count reconciliation, and binary sizes. The map-local `s04-mpi_map_setup.sh` itself is a maintainer/user preparation workflow and is not invoked in routine CI; no generated products are written into the tracked sample.

## High-resolution area handling

Different workflows have different `location.txt` contracts. Allocation tools intentionally accept one high-resolution river-network area; input-matrix generation, regional matrix generation, and permanent-water aggregation process multiple areas sequentially. See the [verified design rationale and validation boundary](../../docs/map_data_tools_plan.md#high-resolution-area-handling-contract).

## NetCDF output compression

The individual-map converter and consolidated-map writer produce NetCDF-4 with lossless deflate level 3 and shuffle. The high-resolution converter has the same default and supports an explicit level override. The channel-parameter writer retains its existing NetCDF classic 64-bit-offset format for compatibility, so that product is not compressed. See the shared [v5 NetCDF output conventions](../../docs/netcdf_output_conventions.md).

## Individual map NetCDF conversion

The model accepts independently stored Binary or NetCDF map rasters when `LMAPCDF=.FALSE.`. Convert an individual registered Binary map without modifying its source:

```sh
python3 map/tools/code/convert_map_binary_to_netcdf.py \
  --map-dir map/mekong_15min \
  --input map/mekong_15min/fldhgt.bin \
  --output /tmp/fldhgt_optimized.nc
```

The converter reads dimensions and geographic bounds from `params.txt`, and types, names, layers, and metadata from [`variable_table/map_variables.csv`](../../variable_table/map_variables.csv). The implemented/tested products are the core float32 2-D rasters, int32 two-record `nextxy` (`nextx` and `nexty` variables), and layered float32 `fldhgt`. Do not assume every optional or high-resolution registry product is supported by this base-map converter. Standard-library Python is used; the NetCDF C shared library must be installed and discoverable (typically via `nc-config`). The default byte order is little-endian as used by the distributed Mekong sample; use `--byte-order` only when the source dataset's storage order is known. Use `--variables` for a custom source basename that is not directly registered. Existing outputs are replaced by default; use `--no-overwrite` to preserve them.

NetCDF variables retain their logical names regardless of output filename, e.g. `rivhgt_optimized.nc` contains `rivhgt`. `nextxy_noedge.nc` contains `nextx` and `nexty`. The converter writes cell-center `lon`/`lat` coordinates, with CDL variable dimensions `(lat,lon)` or `(layer,lat,lon)` corresponding to Fortran-reader dimensions `(NX,NY)` or `(NX,NY,NLFP)`. It checks the output values by reading them back through the NetCDF library, but compatibility with the model is established by the separate mixed-format Mekong simulation tests documented in the [model workflow plan](../../docs/model_source_workflow_plan.md#individual-binarynetcdf-map-inputs). The standalone `convert_bifprm_csv_to_netcdf.py` converts finalized bifurcation CSV tables to static NetCDF-4; it does not recalculate parameters or reorder rows. The current simulation reader still consumes legacy `bifprm.txt`, so the new map-preparation outputs are not yet wired into model execution.

For the map format conversion Shell templates and human-edited candidate-list workflows, see the [map format conversion guide](script_format_conv/README.md). Copy the templates into a map-local `script_format_conv/` directory before configuring and using them. The guide documents the `s0X` NetCDF-to-Binary, `s1X` Binary-to-NetCDF, and `s21` NetCDF-to-COG workflows, including high-resolution tile processing.

The same guide documents the separate `t01-legacy_netcdf_map.sh` workflow, which assembles individual NetCDF rasters into the legacy consolidated `rivclim.nc` and `rivpar.nc` containers.

## River-network analysis

River-network analysis has two execution paths. Standard map preparation uses `script_params/s06-subbasin.sh` and `s07-upbasin.sh`, which call maintained Python programs in `map/tools/code/`. Both `s06` copies use editable example thresholds of 30,000 and 5,000 km2 and write `subbsn-sample.bin` and `subcol-sample.bin` directly. Stage 2 only assigns previously unassigned network regions; Stage 1 positive IDs and boundaries remain fixed. In both `subbsn` and `subcol`, zero marks an unassigned modeled river cell and -9999 marks a cell outside the network; positive `subcol` values 1–10 are categorical display colors for positive segment IDs. Set `AREA_THRESHOLD2_KM2` empty for the original single-stage behavior. These thresholds are examples, not universal parameters or guaranteed minimum segment areas. The CLI is `analysis_subbasin.py THRESHOLD1 [THRESHOLD2] [SUBBSN_OUTPUT SUBCOL_OUTPUT]`; existing one-threshold calls, including explicit output paths, remain supported. `s07` selects the valid GRDC allocation with the largest `area_CaMa`, reports its primary cell, and writes `upbasin-<GRDC_ID>.bin` (Mekong: `upbasin-2569002.bin`). These optional products are not standard simulation inputs.

Independent inspection utilities are in `script_analysis/`. The `a01`–`a05` examples call maintained Python programs through `PYTHON_CMD`; no compilation or code symlink is required. `a01`–`a04` write generated files to the ignored `out_analysis/` by default, while `a05` places its optional relative CSV there. Each script's `OUT_DIR` setting can select the map-root `out_analysis/` instead. Most examples run from `script_analysis/`, while the MPI connectivity diagnostic runs from the map root because its input paths require that working directory. See the [parameter workflow guide](script_params/README.md#river-network-analysis), [analysis toolkit guide](script_analysis/README.md), and [Phase C migration notes](../../docs/map_params_migration_plan.md#phase-c-river-network-analysis).

Detailed segmentation methods, alternative thresholds, and user-generated products are deferred to a future Map Analysis Tutorial; this task does not add that tutorial.


## Numeric COG conversion

The same [format-conversion guide](script_format_conv/README.md#numeric-netcdf-to-cog-caches-s05)
documents s05 and convert_netcdf_to_cog.py. This optional NumPy/netCDF4/Rasterio
workflow streams registered native rasters into numeric EPSG:4326 COG caches,
with full pixel-byte verification and internal display overviews. It does not
change scientific inputs, Binary/NetCDF conversion algorithms or Explorer readers.


## Experimental parallel Python implementations

Python implementations for all 23 standalone map tools are maintained under
`code/`; the original Fortran reference sources are preserved in
`code/legacy_fortran/`. Current analysis, parameter and regional Shell workflows
call the Python versions. Use explicit `--map-dir` and an output directory when
comparing results without changing a map. NumPy is required; only optional
channel-tools NetCDF interfaces need NetCDF4. No mandatory Numba dependency is
added. Program-owned outputs are replaced by default on rerun.

See [migration status and CLI examples](python_migration_status.md),
[measured correctness/performance and limits](python_migration_benchmark.md), and
[all benchmark cases (CSV)](python_migration_benchmark.csv). The comparisons identify
candidates at their tested workloads; see stated limits before use on larger maps.
Focused checks can be run with
`python3 map/tools/tests/test_python_parallel.py` from the repository root.

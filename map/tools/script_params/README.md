# Map parameterization and preparation workflows

`script_params/` contains reusable map-local recipes for parameterization and related map preparation. Run each maintained wrapper from its map-local `script_params/` directory and keep that directory as CWD; Python programs use `../` for map-root products and direct relative paths for script-local files. The wrappers use the common `python3`/`CMF_V50_ROOT` initialization and shared `cmf_check_*` progress/error reporting. Existing outputs owned by a workflow are replaced by default; use `--no-overwrite` where supported to preserve them. Inputs and unrelated files are not removed. See the [preprocessing conventions](../../../docs/preprocessing_code_conventions.md#shell).

The maintained wrappers use NetCDF map input/output by default. In s02, annual runoff is NetCDF and runoff interpolation uses the input matrix by default. Legacy modes are selected with `--map-binary`, `--runoff-binary`, and `--interp-near` on the relevant Python command. High-resolution NetCDF products are expected under `<map>/<tag>/`, and allocation inputs remain the external CSVs configured by each tXX wrapper.

```sh
cd map/<MAPNAME>/script_params
"$PYTHON_CMD" "$CODE_DIR/param_channel_calc_outclm.py" "../$DIMINFO" "$CROFNC"
"$PYTHON_CMD" "$CODE_DIR/param_channel_calc_rivwth.py" "../$DIMINFO" "$HC" "$HP" "$HO" "$HMIN" \
    "$WC" "$WP" "$WO" "$WMIN"
"$PYTHON_CMD" "$CODE_DIR/param_channel_set_merit_width.py" "../$DIMINFO"
```

`map/src/` is preserved as the historical v4 tree; v5 migrations belong under `map/tools/` and do not rewrite those legacy workflows. The `diminfo_` naming convention is shared with v4, while the maintained v5 descriptor now uses native Fortran Namelist (`.nml`) instead of positional TXT records. v5 workflows derive the descriptor and matrix names from `ROFFTAG`.

Base-map geometry is read from authoritative `params.nml`. TXT-only legacy
maps remain supported; when both files are present, their eight numeric values
must match. Python map workflows read `params.nml` first and accept TXT-only maps for compatibility.

## Implemented workflow organization

After regionalization, run the standard map preparation workflows (`s01`–`s04`)
in numerical order to generate the recommended standard map products.

The numbering indicates the recommended preparation sequence, not a strict
dependency for every script. Some outputs are optional for model simulation but
useful for standard map analysis and post-processing.

The standard workflow dependencies and the optional/alternative groups are:

```text
Regionalized base map
        |
        v
s01: Standard INPMAT
        |
        v
s02: Channel parameters
        |
        v
s03: Bifurcation parameters

s04: Permanent-water area
     (requires high-resolution map inputs)

Optional map analysis:
  a01: River-point information
  a02: Subbasin segmentation
  a03: Sample upstream-basin extraction
  a04: GRDC-selected upstream-basin extraction

Alternative input:
  i01: ERA5-Land INPMAT (select with the matching runoff tag)

Extra:
  x01: MPI map preparation
       (requires bifurcation/basin products)

  t01: Flow-gauge allocation
        |
        v
  a04: GRDC-selected upstream-basin example
```

This diagram is conceptual; it is not a workflow runner.

| Group | Script | Purpose | Status |
| --- | --- | --- | --- |
| Standard | `s01-inpmat_default.sh` | Generate the standard global 1-degree `test-1deg` runoff-grid matrix. | Implemented |
| Standard | `s02-channel_params.sh` | Calculate annual mean discharge and channel parameters using the selected runoff matrix. | Implemented |
| Standard | `s03-bifurcation.sh` | Generate non-MPI bifurcation parameters and basin-connectivity products. | Implemented |
| Standard | `s04-permanent_water.sh` | Aggregate high-resolution permanent-water area by unit catchment. | Implemented |
| Alternative input | `i01-inpmat_ERA5land.sh` | Generate an ERA5-Land global 0.1-degree runoff-grid matrix; select its tag in the downstream channel workflow as appropriate. | Implemented |
| Allocation | `t01-alloc_flow_gauge.sh`, `t02-alloc_dams.sh`, `t03-alloc_level_gauge.sh` | Optional flow-gauge, reservoir, and water-level-gauge allocation from MERIT Hydro to CaMa-Flood catchments. | Implemented |
| Extra | `x01-mpi_map_setup.sh` | Prepare MPI basin aggregation, coloring, and region products. | Implemented |
| Analysis | `a01-sample_get_river_point_info.sh` | Inspect sample river-point information. | Implemented |
| Analysis | `a02-sample_subbasin.sh` | Generate optional subbasin IDs and display colors with configured upstream-area thresholds. | Implemented |
| Analysis | `a03-sample_calc_upbasin.sh` | Extract an upstream-basin mask for the sample grid cell. | Implemented |
| Analysis | `a04-advanced_calc_upbasin.sh` | Select the largest valid GRDC allocation, print station/river information, and write its upstream mask. | Implemented |

Reusable river-network commands (`get_river_point_info.sh`, `calc_upbasin.sh`) and examples (`a01`–`a04`) are kept with map parameter workflows. No `script_analysis/` workflow directory is maintained; Python analysis programs remain under `map/tools/code/`. No `script_allocate/` directory is part of the approved design.

CTL generation is separate from this NetCDF-first workflow; NetCDF products do not need GrADS CTLs. For optional legacy Binary visualization, see the [map-tools CTL guide](../README.md#grads-ctl-files).

The principal dependency chain is `s01 → s02 → s03`: the standard INPMAT
supports channel parameterization, and s03 uses channel-height products from
s02. The map can proceed to the next standard preparation stage even when some
recommended products are not simulation-core requirements. s04 requires the
base map and selected high-resolution inputs. The optional a01–a04 analyses are
separate from standard parameter preparation.
The i01 matrix is an alternative runoff grid, not a replacement for the
standard s01 configuration; downstream scripts select it through the matching
runoff tag. x01 requires the relevant bifurcation/basin products. The
optional a04 GRDC example requires a valid `GRDC_alloc.txt`, normally created
by t01, but an existing suitable allocation does not need to be regenerated.
t01–t03 are optional and each uses its configured external allocation CSV.

## Channel parameter workflow

[`s02-channel_params.sh`](s02-channel_params.sh) performs only these three operations:

1. `param_channel_calc_outclm` computes annual mean discharge from the configured runoff climatology.
2. `param_channel_calc_rivwth` derives power-law channel width, depth, roughness, and infinite-depth products.
3. `param_channel_set_merit_width` combines the power-law width with the MERIT Hydro width layer.

It does not run bifurcation, MPI, or permanent-water processing. Configure the script's runoff path and coefficients before use. Its standard Python defaults use NetCDF maps and runoff with input-matrix interpolation; the wrapper supplies `ROFFTAG=test-1deg` and the height/width coefficients shown in the script. It reads the paired `diminfo_test-1deg.nml` and `inpmat_test-1deg.nc` without regenerating them. `ROFFTAG` identifies runoff/input-grid configuration and is distinct from `HIRES_TAG`, which selects high-resolution map data during map generation.

The expected annual-mean runoff input is `$CMF_V50_ROOT/map/data/ELSE_GPCC_clm-1981-2010.nc`. It contains a `runoff(latitude, longitude)` variable on the 360 × 180 grid, with units of mm s-1 and no time dimension. The Binary `.one` version remains available for explicit legacy use with `--runoff-binary`; the maintained wrapper uses the NetCDF file. The package guide identifies ELSE_GPCC and cites Kim et al. (2009). Its inclusion in this repository was directed by the maintainer; upstream terms for other ELSE_GPCC products or derivatives have not been established.

Copy the script into the target map's `script_params/`, edit its configuration, then run it from that directory. The wrapper and Python programs keep `script_params/` as CWD and use `../` paths for map-root data. The programs read the configured inputs and perform the calculations. The workflow writes or replaces `outclm.nc`, `rivwth.nc`, `rivhgt.nc`, `rivman.nc`, `rivhgt_inf.nc`, `rivpar.nc`, and `rivwth_merit.nc` in the map root. The supplementary `rivpar.nc` is part of the standard NetCDF run; add `--no-rivpar-netcdf` directly to Step 2 only when it is not needed. Use a separate map copy or output location when earlier products must be retained.

The standard channel workflow uses annual mean runoff. The historical `map/src/src_param/calc_outclmday.F90` remains legacy-only: it reflects the older maximum-30-day climatology approach associated with Yamazaki et al. (2011). The maintainer reports that later evaluation favored annual mean runoff. This migration does not revalidate the historical method scientifically.

`rivwth.nc` is the power-law width and `rivwth_merit.nc` is the separately named merged width product; the latter is not simply a copy of `width.bin`. The merge algorithm and thresholds are preserved from the legacy tool. The current core map reader selects `rivwth.nc` and does not automatically choose `rivwth_merit.nc`; this workflow produces the alternate product but does not change model-reader selection. See [`variable_table/map_variables.csv`](../../../variable_table/map_variables.csv) and the [Phase B2 migration plan](../../../docs/map_params_migration_plan.md) for product metadata and migration evidence.

## Permanent-water area

[`s04-permanent_water.sh`](s04-permanent_water.sh) runs
`param_water_calc_prmwat` to create `prmwat.nc` by default. Copy the current wrapper into
`<map>/script_params/`, then run `./s04-permanent_water.sh` from that
map-local directory.

The wrapper checks NetCDF high-resolution directories in coarsest-first order:
`1min`, `30sec`, `15sec`, `5sec`, `3sec`, `1sec`. It proposes the coarsest one
present and asks `Use this high-resolution map? [Y/n]`; Enter means Yes.
Answer No to see the available tags and type the resolution to use. Only after
selection does the calculation run. A map with only `15sec/` proposes `15sec`.
No matching directory stops execution; EOF does not accept a proposal.
The selected NetCDF directory must contain the required registered products.
Use `--map-format binary` only when processing a legacy Binary map.

Directory discovery is not input validation: the selected Python program checks the selected
tag, `location.txt` geometry and required NetCDF files. No resampling or change
to classification, area aggregation, missing-value handling or output format is
introduced. The script does not run preceding parameterization steps. Existing
map-local copies must be refreshed from the template to get this selection UI.

The source layout must use the non-tiled `location.txt` format. Inputs are `params.txt`, `nextxy.nc`, and `ctmare.nc` in the map root, plus `<HIRES_TAG>/location.txt` and per-area `catmxy.nc`, `rivwth.nc`, and `flddif.nc` NetCDF files; `grdare.nc` is optional. The output is one float32 `NX x NY` record in m2. Non-network cells are `-9999`; network cells with no selected water pixels are zero. For valid catchment assignments, selected pixels satisfy `(rivwth > 0 OR rivwth == -1) AND flddif <= 5 m`; `rivwth == -1` denotes water surface outside the channel centerline. Their pixel areas are summed and capped by `ctmare`. The legacy `flddif <= 5` condition also accepts `flddif=-9999`; the migrated program warns and preserves that behavior rather than silently adding a new scientific filter.

The elevation cutoff limits `prmwat` to permanent water within the flood area CaMa-Flood can reproduce. A permanent lake isolated high on a hill is outside the model's expected inundation domain, so its area must not be subtracted as pre-existing simulated floodwater. The maintainer described the intended criterion as `flddif < 5 m`. The legacy v4 and migrated v5 source use `flddif <= 5 m`, which includes pixels exactly at 5 m; this boundary difference is documented but has not been changed. The numerical derivation of the 5 m value remains unverified.

`prmwat.nc` is an aggregated estimate of permanent-water surface area per unit catchment for post-processing, such as excluding pre-existing water from newly inundated area. It is not a pixel mask and is not read by the current simulation core. If `grdare.nc` is absent, the legacy scaled `rgetarea` fallback is used; this computes an area from a rectangle ten times larger in both directions and divides by 100 to reduce round-off fluctuations at fine resolution. The method is preserved, but its accuracy has not been independently quantified. See [`variable_table/map_metadata_spec.md`](../../../variable_table/map_metadata_spec.md#permanent-water-area) and [`variable_table/map_variables.csv`](../../../variable_table/map_variables.csv) for product metadata.

## Standard bifurcation workflow

The Python `param_bif_set_params.py` validates `BIFLAYER` as an integer from 1 through 10; invalid values are rejected there rather than prechecked in the shell wrapper.

The Python generator writes only the finalized CSV; the standalone `map/tools/code/convert_bifprm_csv_to_netcdf.py` converts that same table to static NetCDF-4 (`path`, `layer`; `width(layer,path)`) with lossless shuffle/deflate level 3. It requires Python NumPy and netCDF4. Run it directly as `python3 map/tools/code/convert_bifprm_csv_to_netcdf.py map/<tag>/bifprm.csv`; omit the output argument to write `bifprm.nc` beside the CSV. The map-local s02 wrapper passes `bifprm.nc` explicitly, keeping the authoritative CSV at the map root. The s02 wrapper performs these steps in order and fails if conversion fails. `start_lat/start_lon` retain the pathway-source values; `end_lat/end_lon` are the unit-catchment outlet coordinates at `(jx,jy)` from `lonlat.nc` variables `lon`/`lat` respectively. Basin identifiers `ibsn/jbsn` remain numerically ascending, not directional. See the [map-product registry](../../../variable_table/map_variables.csv) and [metadata specification](../../../variable_table/map_metadata_spec.md#bifurcation-parameter-tables).

[`s03-bifurcation.sh`](s03-bifurcation.sh) is intended to follow `s02-channel_params.sh`, which produces the required channel-depth map `rivhgt.nc`. It generates ordinary bifurcation parameters and basin-connectivity products using map-root `nextxy.nc`, `basin.nc`, `bifori.txt`, `params.nml` (or legacy `params.txt`), and `diminfo_<ROFFTAG>.nml` (default `diminfo_test-1deg.nml`). `BIFLAYER` defaults to the legacy value `5`. If `bifori.txt` contains fewer layers than requested, the Python program warns and clamps processing to the available count.

The workflow runs both Python programs from the unchanged map-local `script_params/` CWD. It writes or replaces `bifprm.csv`, converts that finalized table to `bifprm.nc`, then writes `bifbsn.nc` and `bifcol.nc`. `bifcol.nc` remains unconditional because it is routinely used to visualize the merged basin map. The display palette has colors 2–10 and falls back to color 10 if no candidate is free among neighboring basins; adjacent regions can consequently share a color, without changing simulation products. To create the optional diagnostics, add `--check-map` directly to both corresponding Python commands in the wrapper. `param_bif_set_params` writes `check_bif_dphwth.nc` with two float32 records (`bifdph` depth, then `bifwth` width), and `param_bif_set_basin` writes `check_bif_bsnmod.nc` with two int32 records (`bifmod`, then `bpoint`). These are inspection-only products, not model inputs. Without the flag, neither diagnostic is created or overwritten; pre-existing check files can therefore reflect an earlier run. The v5 program no longer creates the legacy separate `bifmod.bin` and `bpoint.bin`; pre-existing files are left untouched. Older v4 `bifdph.bin` files are also left untouched. `bifprm.csv` preserves the filtered `bifori.txt` row order; `pth_id` is a consecutive, configuration-specific row ID and `(ix,iy,jx,jy)` identifies a path across configurations. The CSV-to-NetCDF converter does no path filtering or recalculation. The model simulation reader accepts the generated `bifprm.csv` directly, or the equivalent `bifprm.nc` in a NetCDF-enabled build; legacy `bifprm.txt` remains supported. The CSV is authoritative and the NetCDF converter preserves its finalized row order and values.

This wrapper retains the established non-MPI filtered pathway order written by `param_bif_set_params`. The v5 MPI workflow is separate and described below. The preserved Fortran calculations and `gosh/` workflows are not invoked by these Shell workflows. Regression tests compare standard outputs and consolidated diagnostic records with the legacy products on temporary Mekong copies; this demonstrates compatibility for that case, not independent scientific validation.

## MPI map preparation

[`x01-mpi_map_setup.sh`](x01-mpi_map_setup.sh) reads `bifprm.csv` produced by s02 and `basin.nc`; it never rewrites, reorders, or regenerates `bifprm.txt`. Copy this script into the map's `script_params/`, and configure `BASIN_MERGE_MODE` and `MPI_COUNTS` there. The defaults are `standard` and `4 8 16`. `standard` preserves the previous `normal` threshold (6%); `small_basins` preserves the previous `MaxMPI` threshold (3%). Both retain the legacy 0.1% small-basin exception. The old `normal` and `MaxMPI` CLI values remain accepted as aliases. Basin aggregation writes `bifcol_mpi.nc` before region partitioning; this display product is independent of N but can differ by basin-merge mode. The wrapper creates one `mpireg-N.nc` for each requested count, in the listed order, then runs the dropped-bifurcation diagnostic once for the largest requested count. The largest count is a representative choice and is not guaranteed to produce the greatest number of dropped pathways. No unnumbered `mpireg.nc` alias is created. The separate `analysis_mpi_region_color` utility can be run manually, for example `../tools/code/analysis_mpi_region_color.py mpireg-8.nc` from a map root, to produce optional `bsncol_mpi-8.nc`; x01 does not run it. Add `--check-map` directly to the `param_mpi_set_basin.py` command to write `check_bif_bsnmod_mpi.nc` during basin aggregation.

MPI basin integration is distinct from standard s02 basin connectivity. The `standard` mode uses the legacy 6% valid-river-cell threshold and `small_basins` uses 3%; both retain the legacy 0.1% small-basin exception. These are the former `normal` and `MaxMPI` behaviors, respectively. The algorithm still processes channel bifurcations (`wth(1)>0`) first, then remaining overland/floodplain paths in reverse order, applying the same repeated merge and strict size checks. Basin groups are assigned in ascending ID order to the currently least-loaded region; equal loads select the first region ID. The region map is one int32 `NX x NY` record with `-9999` outside assigned river basins. The optional `check_bif_bsnmod_mpi.nc` diagnostic is produced before region assignment and has two direct-access int32 `NX x NY` records: `bifmod_mpi` (record 1: 0 unchanged, 1 absorbed, 2 expanded; -9999 not applicable) and `bpoint_mpi` (record 2: 1 connection remains between aggregated basins, 2 merged floodplain path, 3 merged river-channel path; -9999 not applicable). It compares original `basin.nc` with the aggregated basin result; its classifications may vary between basin-merge modes, but not with requested MPI partition count. It is not required for model execution.

The legacy workflow sorted its MPI pathway table by columns 15, 16, and 6. Those basin-ID columns move when the number of width layers changes. The v5 aggregation tool parses the standard row and sorts by `ibsn`, `jbsn`, and `elv`, with source text as a deterministic equal-key fallback matching the legacy sort's whole-line tie behavior. This order is part of the order-sensitive basin-merge algorithm. For the Mekong v4.30 sample, both new modes reproduce the previous `normal`/`MaxMPI` basin groups and 4/8/16 maps byte-for-byte.

The persistent x01 products are `bifcol_mpi.nc` from MPI-aggregated basin IDs and `mpireg-N.nc` for every count in `MPI_COUNTS`. `bifcol_mpi.nc` is visualization-only, independent of N, and may vary by basin-merge mode; `check_bif_bsnmod_mpi.nc` is created only when explicitly requested. The optional `analysis_mpi_region_color` utility colors region IDs into `bsncol_mpi-N.nc` when run manually; the color raster does not encode rank assignment. In NetCDF mode, x01 removes its temporary `bifbsn_mpi.nc`, including on failure; explicit legacy Binary mode uses `binary/bifbsn_mpi.tmp`. The v5 workflow does not write legacy MPI products `bifprm_mpi.txt`, `bifprm-N.txt`, `bifmod_mpi.bin`, `bpoint_mpi.bin`, or standard non-MPI `bifcol.bin`. Historical `map/src/` tools remain unchanged. The separate `analysis_mpi_dropped_bifurcation.py` diagnostic reconstructs model-local vector retention for a selected `mpireg-N.nc`; it reports retained, dropped, and invalid pathways and can write only the dropped rows to CSV. It is verification-only and does not modify the MPI map. Run the Python diagnostic directly from the map root, for example `../tools/code/analysis_mpi_dropped_bifurcation.py mpireg-8.nc --csv dropped.csv`; this inspection does not modify the map.

Run the wrapper from the target map's `script_params/` directory:

```sh
cd map/<MAPNAME>/script_params
./x01-mpi_map_setup.sh
```

The programs read map geometry from `params.nml` (or legacy `params.txt`) and map files `basin.nc`, `bifprm.csv`, and `nextxy.nc` using paths relative to the unchanged map-local `script_params/` CWD; no package-only global map is required. A successful map-generation run does not establish scientific validity of the partition or of a subsequent simulation.

## Runoff input-matrix generators

The standard workflow entrypoint remains `s01-inpmat_default.sh`; use the
`iXX-` prefix for additional input-grid-specific recipes. Both wrappers call
`param_inpmat_generate.py` and create map-specific matrices from the selected
high-resolution catchment mapping.

[`s01-inpmat_default.sh`](s01-inpmat_default.sh) creates the standard global
1-degree `test-1deg` matrix pair. Its grid edges are west/east -180/180° and
north/south 90/-90°, with `NtoS` latitude order (360 × 180 cells). This is the
ELSE_GPCC grid used by the standard annual-runoff channel workflow. The output
names are `diminfo_test-1deg.nml` and `inpmat_test-1deg.nc` in the selected map
root.

[`i01-inpmat_ERA5land.sh`](i01-inpmat_ERA5land.sh) provides an alternative
ERA5-Land example: a global 0.1-degree grid with 3600 × 1801 cells, edges
-180.05/179.95° and 90.05/-90.05°, and `NtoS` row order. These bounds match the
coordinates in the inspected converted
`inp/repo-ERA5land-glb_2day/runoff_200001.nc`. It uses `ROFFTAG=ERA5land_global`,
which names the spatial grid rather than the dataset period. Reuse that matrix
only for forcing with identical coordinates/order and the same model map;
generate a separate matrix for every other model map. Other regular runoff
grids remain configurable by editing the wrapper settings.

The target map must provide `params.nml` (or legacy `params.txt`), a selected high-resolution
directory with `location.txt`, and each area's `catmxy.nc`; `grdare.nc` is
optional. The runoff values themselves are not read while constructing the
matrix. Set `HIRES_TAG` independently when the default high-resolution map
selection is unsuitable.

For the global map, generated matrices belong in Package Additional Data at
`cmf_v5_package_data/map/glb_15min/`, not in Git. These wrappers generate no
matrices until run and do not modify the external data store.

The Python dam-parameter estimation workflow under legacy `map/src/src_dam/` is separate from the Fortran dam-location allocation workflows listed below.

## Allocation workflows

The three optional wrappers use shared `allocate_*.py` programs in `map/tools/code/`. Copy the wrappers into a map-local `script_params/` directory, configure the input path, then run them from that directory. They call `cmf_select_hires_tag "$HIRES_TAG" --single-area`, which recommends the coarsest compatible resolution in `1min`, `30sec`, `15sec`, `5sec`, `3sec`, `1sec` order and allows an interactive alternative. It checks the structural single-area `location.txt` and `<TAG>.<VARIABLE>.nc`/`.bin` naming convention; the Python reader validates the scientific layers and independently rejects any map declaring multiple areas. Use `--map-format binary` on the Python invocation only for a legacy Binary map. This single-network topology/catchment contract is not a universal limit on map resolution.

The maintainer-confirmed map convention is that the coarsest high-resolution layer is a single-area, non-tiled river-network representation; finer layers may be tiled. Single-area files use `<TAG>.<VARIABLE>.nc`; tiled files use geographic area identifiers such as `n30e120.<VARIABLE>.nc`. Legacy Binary maps use the same basename with `.bin`. The v4.30 distribution package includes a single-area global `glb_15min/1min` layer and a single-area Japan `tej_01min/15sec` layer, which the maintainer identifies as intended CaMa-Flood allocation inputs. These are distinct from the global 30-arcsec MERIT Hydro and Japan 5-arcsec J-FlwDir maps used for the first-stage allocation. See the [area-handling rationale and validation plan](../../../docs/map_data_tools_plan.md#high-resolution-area-handling-contract).

The input tables are expected to have already been matched and reviewed on the high-resolution MERIT Hydro network using [AllocRiverGauge](../../../doc/Manual_AllocateRiverGauges.docx). CaMa-Flood performs the second-stage mapping from those allocated coordinates and drainage areas to its own unit catchments. This consistency rationale does not establish that each individual station or dam is correct. Inspect the outputs before using them in analysis.

| Wrapper | Default input | Required map files | Outputs in the map root |
| --- | --- | --- | --- |
| [`t01-alloc_flow_gauge.sh`](t01-alloc_flow_gauge.sh) | `../../data/GRDC_allocated.csv` | `params.nml` (or legacy `params.txt`), `uparea.nc`, `nextxy.nc`; `<HIRES_TAG>/location.txt`, `.uparea.nc`, `.catmxy.nc`, `.downxy.nc` | `GRDC_alloc.txt` |
| [`t02-alloc_dams.sh`](t02-alloc_dams.sh) | `../../data/GRanD_allocated.csv` | Flow-gauge files plus `ctmare.nc` | `GRanD_river.txt`, `GRanD_small.txt`, `GRanD_error.txt` |
| [`t03-alloc_level_gauge.sh`](t03-alloc_level_gauge.sh) | `../../data/MLIT_LevelGauge_allocated.csv` | Flow-gauge files plus `elevtn.nc` and `<HIRES_TAG>/<HIRES_TAG>.elevtn.nc` | `MLIT_levelgauge.txt` |

The allocation input readers skip one header row and read fields positionally; they do not implement general CSV quoting. Expected leading columns are `ID,lat_alloc,lon_alloc,area_alloc` for gauges and `ID,lat_alloc,lon_alloc,area_alloc,DamName,RiverName,CAP_MCM,YEAR` for GRanD. Coordinates are degrees and allocated drainage areas are km2. GRanD capacity is MCM and the year is passed through as an integer.

Output tables are whitespace-delimited fixed-width text, not CSV. They retain the legacy schemas and meanings:

- **Flow gauges (`GRDC_alloc.txt`):** `ID`, `lat`, `lon`, `area_Input`, `area_CaMa`, `error`, `diff`, `Type`, `ix1`, `iy1`, `ix2`, `iy2`, `area1`, `area2`. Coordinates are degrees; areas and `diff` are km2; `error` is the signed dimensionless relative area difference; indices are one-based CaMa-Flood grid indices. `area_CaMa` is the selected aggregate upstream area; `area1`/`area2` are the primary and optional secondary substitute areas. `Type` is the number of upstream substitute catchments (0–2). Unallocated rows use `Type=-9`, indices `-999`, and CaMa area/error/difference/substitute-area fields `-999`. Out-of-domain rows are omitted.
- **Dams (`GRanD_river.txt`, `GRanD_small.txt`, `GRanD_error.txt`):** `ID`, `lat`, `lon`, `area_CaMa`, `area_Input`, `error`, `diff`, `ix`, `iy`, `cap_mcm`, `year`, `damname`, `rivname`. Coordinates are degrees, areas and `diff` are km2, `error` is dimensionless, `cap_mcm` is MCM, and indices are one-based. `area_CaMa` is the selected upstream area; `diff=area_CaMa-area_Input`. The `small` class uses the legacy catchment-area criterion; it is not a verified physical mainstem/tributary class. Its sentinel is `-888` (`error=-8`). The error file uses `-999` for unmapped area/index/error fields. Out-of-domain rows and rows with negative capacity are skipped, matching v4.
- **Level gauges (`MLIT_levelgauge.txt`):** `ID`, `lat`, `lon`, `area`, `Type`, `ix1`, `iy1`, `ix2`, `iy2`, `elv_outlet`, `elv_gauge`, `elv_upst`, `dst_outlet`, `dst_upst`, `upa_outlet`. Coordinates are degrees, `area` and `upa_outlet` are km2, elevations are metres, distances along the river network are km, and indices are one-based. `ix1/iy1` identify the assigned catchment; `ix2/iy2` identify its selected upstream reference catchment where applicable. The elevation fields are CaMa outlet, high-resolution gauge, and upstream catchment-outlet elevations; `dst_outlet` and `dst_upst` are the corresponding along-network distances. `Type=1/2/3` denotes the legacy mainstem/tributary/small-stream path classes; `Type=-9` is unallocated. Missing index, elevation, distance, and outlet-area values use `-999` in unmatched rows; upstream-reference fields are also `-999` for Type 3.

For all three products, row order, formatting precision, classifications, and sentinels preserve legacy behavior. The dam input capacity and year columns pass through into the corresponding output fields.

Run the migration regression with:

```sh
python3 -B -m unittest map.tools.tests.test_allocation_regression -v
```

It compiles v4 and v5 programs in temporary directories, compares all six output products to the committed legacy snapshots, checks classifications and high-resolution selection, rejects a multi-area layout, and verifies that the Mekong inputs were not modified. Regression demonstrates parity for this sample/compiler, not independent scientific validation. Threshold rationale remains open; see the [allocation migration plan](../../../docs/map_allocation_migration_plan.md#8-knowledge-gaps-and-maintainer-questions).

## High-resolution areas in aggregation workflows

The general parameter input-matrix generator (`s01-inpmat_default.sh`) and permanent-water aggregator (`s04-permanent_water.sh`) read all rows in the selected `HIRES_TAG/location.txt` and accumulate across areas. This multi-area behavior is distinct from the intentional single-area allocation contract above. Source inspection confirms the loops; the Mekong sample and current focused fixtures do not validate full-package multi-area behavior. The [map-tools plan](../../../docs/map_data_tools_plan.md#high-resolution-area-handling-contract) gives the maintainer-operated large-data integration procedure.

## River-network analysis

### Reusable inspection commands and examples

Copy the shared command/examples from `map/tools/script_params/` into the target map's `script_params/` directory. Run them there so map-root inputs resolve consistently:

```sh
cd map/<MAPNAME>/script_params
./get_river_point_info.sh xy IX IY
./get_river_point_info.sh latlon LAT LON
./calc_upbasin.sh xy IX IY [OUTPUT.nc]
./a01-sample_get_river_point_info.sh
./a02-sample_subbasin.sh
./a03-sample_calc_upbasin.sh
./a04-advanced_calc_upbasin.sh
```

Indices are one-based Fortran grid indices. The lat/lon form takes latitude then longitude. The default upstream mask is `../upbasin-IX-IY.nc`; a03 writes `./upbasin-sample.nc`. The sample coordinates in a01 and a03 are for the Mekong map. The advanced example selects the largest valid GRDC allocation for the current map and is preferable to fixed coordinates when comparing maps with different grids or domains.


The shell layer sets locations and parameters; `analysis_river_point_info`, `analysis_upbasin`, `analysis_subbasin`, and other Python programs in `map/tools/code/` read and validate map data and perform the network calculations. No compilation is required; the standard a02–a04 analysis examples use these programs through the reusable Shell commands in the same `script_params/` directory.

`a02-sample_subbasin.sh` writes `subbsn-sample.nc` and `subcol-sample.nc` directly in the map root, using the registered internal NetCDF variable names `subbsn` and `subcol` respectively. The editable example settings are `AREA_SUBBSN=30000` and `AREA_SMLBSN=5000`; set the second value empty for single-stage operation. These are example defaults, not universal scientific parameters. Stage 1 uses the existing upstream-area-increase rule; Stage 2 applies the smaller threshold only to previously unassigned river-network regions, preserves all positive Stage 1 IDs and boundaries, and assigns new IDs after them. Links into Stage 1 segments are terminal boundaries. In each stage, a link is cut when the current upstream area exceeds its threshold and the valid downstream area exceeds the current area by more than that threshold. Neither threshold guarantees a minimum segment area. Positive `subbsn` values are segment IDs, 0 marks remaining unassigned network cells, and -9999 marks outside-network cells. `subcol` uses the same spatial mask convention: positive IDs receive display colors 1–10, 0 marks unassigned network cells, and -9999 marks cells outside the network. These optional products are not simulation inputs.

[`a04-advanced_calc_upbasin.sh`](a04-advanced_calc_upbasin.sh) requires map-local `GRDC_alloc.txt` (normally produced by `t01-alloc_flow_gauge.sh`). It filters unallocated/invalid records, chooses the largest positive `area_CaMa` (first file row wins a tie), and uses that row's primary `ix1,iy1` cell. It prints the selected station and river-point information to stdout, and writes only `upbasin-<GRDC_ID>.nc` as a scientific output. Repeated execution replaces that map-root mask. The Mekong sample is `upbasin-2569002.nc`. The primary-cell upstream mask is not guaranteed to represent the complete aggregate drainage area of a gauge mapped to multiple catchments, so do not treat its cell count/area as equal to `area_CaMa` or observed drainage area.

The generic commands and a01–a04 examples are optional map-specific inspection workflows. The sample point coordinates in a01 and a03 are for the Mekong map; use the allocated-point a04 example where a fixed coordinate may fall outside another map or on an unrelated cell.

### Standard ELSE_GPCC grid tag

The global 1-degree ELSE_GPCC mapping pair uses `test-1deg`, matching v4:
`diminfo_test-1deg.nml` and `inpmat_test-1deg.nc`. This replaces the interim
v5 tag `test-glb_1deg` without changing grid geometry or matrix values. The
descriptor's embedded matrix filename must also match, because channel
parameter tools read that name. The pair supports global ELSE_GPCC runoff and
`map/data/ELSE_GPCC_clm-1981-2010.nc` (annual-mean runoff in mm/s).
The annual `inp/ELSE_GPCC/runoffYYYY.nc` files contain daily runoff in
`mm day-1`. Both use 360 × 180 input cells, longitude centers −179.5…179.5°
and north-to-south latitude centers 89.5…−89.5°. The tag identifies spatial
geometry rather than period, units or storage format. Generate a distinct pair
for each model map: the same input grid does not make different model maps'
matrices interchangeable. See the [runoff registry](../../../inp/runoff_datasets.csv).
Mekong-only `repo-mek_1deg` and 0.1-degree `ERA5land_global` are separate grids
and retain their own tags. Existing map-local script copies should be refreshed after
updating their source defaults; external package data are updated separately.

### Coarsest high-resolution input selection

`s01-inpmat_default.sh` and `s04-permanent_water.sh` call the shared
`cmf_select_hires_tag` function loaded by `tools/cmf_shell_functions.sh`.
It checks `../<tag>` directories in `1min`, `30sec`, `15sec`, `5sec`, `3sec`,
`1sec` order. An explicit valid `HIRES_TAG` is proposed for confirmation;
when unset, the coarsest available tag is proposed. Enter accepts a proposal;
No displays the available tags and prompts for an alternative. Invalid input
and EOF fail without starting processing. The selected value is returned to
the wrapper, which passes it to the existing Python program.

`t01-alloc_flow_gauge.sh`, `t02-alloc_dams.sh` and `t03-alloc_level_gauge.sh`
use the same resolution order with the selector's `--single-area` filter.
Only layouts whose `location.txt` declares one area and whose layer filenames
use the resolution tag are offered. Python validates the required data and
retains the single-area restriction. Legacy Binary maps remain usable when
Binary is explicitly selected for the Python command. No allocation algorithm
is changed.

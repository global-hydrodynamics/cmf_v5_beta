# Map parameterization and preparation workflows

Base-map geometry is read from authoritative `params.nml`. TXT-only legacy
maps remain supported; when both files exist, their eight numeric values must
match. References to `params.txt` below describe compatibility inputs retained
for existing map-local tools.

`script_params/` contains reusable map-local recipes for parameterization and map preparation. Run wrappers from the map-local `script_params/` directory; they keep that working directory and resolve map-root paths with `../`. Each wrapper uses the shared shell error checker and Python programs under `map/tools/code/`. Set `PYTHON_CMD` only when a non-default interpreter is needed. Outputs owned by a workflow are overwritten by default; supported tools accept `--no-overwrite`. Inputs and unrelated files are preserved. See the [shell-script convention](../../../AGENTS.md#shell-script-design-principles).

The channel Python programs use NetCDF map input/output by default. The Rhine s01 sample keeps its legacy Binary runoff input by passing `--runoff-binary`; its input-matrix interpolation remains the default. Use `--map-binary` directly on a Python invocation only for a legacy Binary map. High-resolution NetCDF products are expected under `<map>/<tag>/`, and allocation inputs remain the external CSVs configured by each tXX wrapper.

```sh
cd "$MAP_DIR"
"$PYTHON_CMD" "$CODE_DIR/param_channel_calc_outclm.py" "$DIMINFO" "$CROFBIN" --runoff-binary
"$PYTHON_CMD" "$CODE_DIR/param_channel_calc_rivwth.py" "$DIMINFO" "$HC" "$HP" "$HO" "$HMIN" \
    "$WC" "$WP" "$WO" "$WMIN" --no-rivpar-netcdf
"$PYTHON_CMD" "$CODE_DIR/param_channel_set_merit_width.py" "$DIMINFO"
```

`map/src/` is preserved as the historical v4 tree; v5 migrations belong under `map/tools/` and do not rewrite those legacy workflows. The `diminfo_` naming convention is shared with v4; the v5 workflows derive both descriptor and matrix names from `ROFFTAG` without changing their formats.

## Implemented workflow organization

The v5 parameter and map-preparation workflows listed below are implemented. Numbering communicates a useful order for the standard workflow; it does not make every step mandatory or imply that every map uses every tool.

| Script | Purpose | Status |
| --- | --- | --- |
| `s02-channel_params.sh` | Annual mean discharge, power-law channel width/depth/roughness, and MERIT Hydro width merging. | Implemented |
| `s03-bifurcation.sh` | Standard non-MPI bifurcation parameters and basin-connectivity products. | Implemented |
| `s01-inpmat_default.sh` | Standard global 1-degree `test-1deg` runoff-grid matrix. | Implemented |
| `i01-inpmat_ERA5land.sh` | ERA5-Land global 0.1-degree runoff-grid matrix. | Implemented |
| `x01-mpi_map_setup.sh` | MPI basin aggregation and coloring, region assignment, and default-N connectivity report; optional pre-partition basin diagnostic with `--check-map`. | Implemented |
| `s04-permanent_water.sh` | Aggregate high-resolution permanent-water area by unit catchment. | Implemented |
| `a01-sample_get_river_point_info.sh` | Inspect sample river-point information. | Implemented |
| `a02-sample_subbasin.sh` | Generate optional subbasin IDs and display colors using one or two configured upstream-area-increase thresholds. | Implemented |
| `a03-sample_calc_upbasin.sh` | Extract an upstream-basin mask for the sample grid cell. | Implemented |
| `a04-advanced_calc_upbasin.sh` | Select the largest valid allocated GRDC station; print station/river information and write its upstream mask. | Implemented |
| `t01-alloc_flow_gauge.sh`, `t02-alloc_dams.sh`, `t03-alloc_level_gauge.sh` | Flow-gauge, reservoir, and water-level-gauge mapping from MERIT Hydro to CaMa-Flood catchments. | Implemented |

Reusable river-network commands (`get_river_point_info.sh`, `calc_upbasin.sh`) and examples (`a01`–`a04`) are kept with map parameter workflows. No `script_analysis/` workflow directory is maintained; Python analysis programs remain under `map/tools/code/`. No `script_allocate/` directory is part of the approved design.

CTL generation is separate from this NetCDF-first workflow; NetCDF products do not need GrADS CTLs. For optional legacy Binary visualization, see the [map-tools CTL guide](../README.md#grads-ctl-files).

Run only the workflows required for a map. The common dependency chain is s01 before s02, and s02 before s04; i01 creates an alternative runoff-grid matrix and is independent of s01 when its own `ROFFTAG` is used. a02 requires the base-map river-network and upstream-area products; it does not require high-resolution inputs. The optional a04 example requires a valid `GRDC_alloc.txt`, normally produced by t01. The t01–t03 allocation workflows are optional and each uses its configured external allocation CSV.

## Channel parameter workflow

[`s02-channel_params.sh`](s02-channel_params.sh) performs only these three operations:

1. `param_channel_calc_outclm` computes annual mean discharge from the configured runoff climatology.
2. `param_channel_calc_rivwth` derives power-law channel width, depth, roughness, and infinite-depth products.
3. `param_channel_set_merit_width` combines the power-law width with the MERIT Hydro width layer.

It does not run bifurcation, MPI, or permanent-water processing. Configure the script's runoff path and coefficients before use. Its standard Python defaults are NetCDF maps/runoff and input-matrix interpolation; the map-local Rhine wrapper explicitly selects Binary runoff with `--runoff-binary`. It uses `ROFFTAG=test-1deg` and the height/width coefficients shown in the script. It reads the paired `diminfo_test-1deg.nml` and `inpmat_test-1deg.nc` without regenerating them. `ROFFTAG` identifies runoff/input-grid configuration and is distinct from `HIRES_TAG`, which selects high-resolution map data during map generation.

The Rhine sample currently reads `../data/ELSE_GPCC_clm-1981-2010.one`, relative to the map root, as its legacy Binary input. The 360 x 180, one-record little-endian file is also included alongside the standard NetCDF runoff file; its CTL specifies runoff in mm/s. The CTL variable comment says "daily runoff climatology," despite the single record and the channel workflow's annual-mean use; treat this as an existing metadata inconsistency. The package guide identifies ELSE_GPCC and cites Kim et al. (2009). Its inclusion in this repository was directed by the maintainer; upstream terms for other ELSE_GPCC products or derivatives have not been established.

Copy the script into the target map's `script_params/`, edit its configuration, then run it from that `script_params/` directory. It keeps the current working directory and calls the Python programs in order. The programs read the configured inputs and perform the calculations. The workflow writes or replaces `outclm.nc`, `rivwth.nc`, `rivhgt.nc`, `rivman.nc`, `rivhgt_inf.nc`, and `rivwth_merit.nc` in the map root. The Rhine sample skips supplementary `rivpar.nc` to preserve its earlier Binary-runoff recipe. Use a separate map copy or output location when earlier products must be retained.

The standard channel workflow uses annual mean runoff. The historical `map/src/src_param/calc_outclmday.F90` remains legacy-only: it reflects the older maximum-30-day climatology approach associated with Yamazaki et al. (2011). The maintainer reports that later evaluation favored annual mean runoff. This migration does not revalidate the historical method scientifically.

`rivwth.nc` is the power-law width and `rivwth_merit.nc` is the separately named merged width product; the latter is not simply a copy of `width.bin`. The merge algorithm and thresholds are preserved from the legacy tool. The current core map reader selects `rivwth.nc` and does not automatically choose `rivwth_merit.nc`; this workflow produces the alternate product but does not change model-reader selection. See [`variable_table/map_variables.csv`](../../../variable_table/map_variables.csv) and the [Phase B2 migration plan](../../../docs/map_params_migration_plan.md) for product metadata and migration evidence.

## Permanent-water area

[`s04-permanent_water.sh`](s04-permanent_water.sh) runs
`param_water_calc_prmwat` to create `prmwat.nc` by default. Copy the current wrapper into
`<map>/script_params/`, then run `./s04-permanent_water.sh` from any
working directory.

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

The workflow runs `param_bif_set_params` from the map root, then runs `param_bif_set_basin` from the map-local `script_params/` directory because its input/output paths use `../`. It writes or replaces `bifprm.csv`, converts that finalized table to `bifprm.nc`, then writes `bifbsn.nc` and `bifcol.nc`. `bifcol.nc` remains unconditional because it is routinely used to visualize the merged basin map. The display palette has colors 2–10 and falls back to color 10 if no candidate is free among neighboring basins; adjacent regions can consequently share a color, without changing simulation products. When `--check-map` is added to both relevant Python commands in `s03-bifurcation.sh`, `param_bif_set_params` additionally writes `check_bif_dphwth.nc` with two float32 records (`bifdph` depth, then `bifwth` width), and `param_bif_set_basin` writes `check_bif_bsnmod.nc` with two int32 records (`bifmod`, then `bpoint`). These are inspection-only products, not model inputs. Without `--check-map`, neither diagnostic is created or overwritten; a pre-existing check file can therefore reflect an earlier run. The v5 program no longer creates the legacy separate `bifmod.bin` and `bpoint.bin`; pre-existing files are left untouched. Older v4 `bifdph.bin` files are also left untouched. `bifprm.csv` preserves the filtered `bifori.txt` row order; `pth_id` is a consecutive, configuration-specific row ID and `(ix,iy,jx,jy)` identifies a path across configurations. The CSV-to-NetCDF converter does no path filtering or recalculation. The model simulation reader accepts the generated `bifprm.csv` directly, or the equivalent `bifprm.nc` in a NetCDF-enabled build; legacy `bifprm.txt` remains supported. The CSV is authoritative and the NetCDF converter preserves its finalized row order and values.

This wrapper retains the established non-MPI filtered pathway order written by `param_bif_set_params`. The v5 MPI workflow is separate and described below. The preserved Fortran calculations and `gosh/` workflows are not invoked by these Shell workflows. Regression tests compare standard outputs and consolidated diagnostic records with the legacy products on temporary Mekong copies; this demonstrates compatibility for that case, not independent scientific validation.

## MPI map preparation

[`x01-mpi_map_setup.sh`](x01-mpi_map_setup.sh) reads `bifprm.csv` produced by s02 and `basin.nc`; it never rewrites, reorders, or regenerates `bifprm.txt`. Configure `BASIN_MERGE_MODE` and `MPI_COUNTS` in the copied script. The defaults are `standard` and `4 8 16`. `standard` preserves the former `normal` 6% threshold; `small_basins` preserves the former `MaxMPI` 3% threshold. Both retain the legacy 0.1% small-basin exception, and the old CLI names remain compatible aliases. x01 writes `bifcol_mpi.nc`, creates one `mpireg-N.nc` per requested count, then runs `analysis_mpi_dropped_bifurcation.py` once for the largest requested count. This is a representative diagnostic choice, not a guarantee that it has the most dropped pathways. No unnumbered `mpireg.nc` alias is created. The separate `analysis_mpi_region_color` utility may be run manually to create `bsncol_mpi-N.nc`; x01 does not invoke it. Add `--check-map` to the `param_mpi_set_basin.py` command to create the optional aggregation diagnostic.

MPI basin integration remains separate from standard s02 basin connectivity. The mode thresholds are 6% for `standard` and 3% for `small_basins`, with the existing 0.1% small-basin exception retained. The merger still processes channel bifurcations first, then remaining overland/floodplain paths in reverse order, with unchanged repeated merge and size checks. Region assignment and integer map contract are unchanged. The optional `check_bif_bsnmod_mpi.nc` records basin-size change and endpoint-merge classifications before region assignment; it is not required for model execution.

The v5 tool parses `ibsn`, `jbsn`, and `elv` rather than relying on width-layer-dependent text columns, preserving the source-row fallback for deterministic ties. On the Mekong v4.30 sample, `standard`/`small_basins` retain the previous `normal`/`MaxMPI` results, including byte-identical basin groups and 4/8/16 region maps.

The persistent products are `bifcol_mpi.nc` and the numbered `mpireg-N.nc` maps requested in `MPI_COUNTS`; the temporary `bifbsn_mpi.nc` is removed on success or failure. `check_bif_bsnmod_mpi.nc` remains opt-in. The renamed `analysis_mpi_dropped_bifurcation.py` checks model-local pathway retention for a selected partition and can export dropped rows with `--csv`; it is verification-only and does not modify maps. The historical Fortran source and `map/src/` workflows remain unchanged. Run `../tools/code/analysis_mpi_dropped_bifurcation.py` from the map root for its standalone CSV option.

Run the wrapper from the map-local `script_params/` directory after copying it into the target map:

```sh
./script_params/x01-mpi_map_setup.sh
# Add --check-map to the param_mpi_set_basin.py command in the script for diagnostics.
```

The programs read map geometry from `params.nml` (or legacy `params.txt`) and map files `basin.nc`, `bifprm.csv`, and `nextxy.nc`; no package-only global map is required. Basin aggregation and region assignment run from map-local `script_params/`, while the connectivity analysis runs from the map root. A successful map-generation run does not establish scientific validity of the partition or of a subsequent simulation.

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

[`i01-inpmat_ERA5land.sh`](i01-inpmat_ERA5land.sh) preserves the former s03
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

The three optional wrappers use shared `allocate_*.py` programs in `map/tools/code/`. Copy the wrappers into a map-local `script_params/` directory, configure the input path, then run them from that directory. They call `cmf_select_hires_tag "$HIRES_TAG" --single-area`, which recommends the coarsest compatible resolution in `1min`, `30sec`, `15sec`, `5sec`, `3sec`, `1sec` order and allows an interactive alternative. It checks the structural single-area `location.txt` and `<TAG>.<VARIABLE>.nc`/`.bin` naming convention; the Python reader validates scientific layers and independently rejects any map declaring multiple areas. Use `--map-format binary` on the Python invocation only for a legacy Binary map. This single-network topology/catchment contract is not a universal limit on map resolution.

The maintainer-confirmed map convention is that the coarsest high-resolution layer is a single-area, non-tiled river-network representation; finer layers may be tiled. Single-area files use `<TAG>.<VARIABLE>.nc`; tiled files use geographic area identifiers such as `n30e120.<VARIABLE>.nc`. Legacy Binary maps use the same basename with `.bin`. The v4.30 distribution package includes a single-area global `glb_15min/1min` layer and a single-area Japan `tej_01min/15sec` layer, which the maintainer identifies as intended CaMa-Flood allocation inputs. These are distinct from the global 30-arcsec MERIT Hydro and Japan 5-arcsec J-FlwDir maps used for first-stage allocation. See the [area-handling rationale and validation plan](../../../docs/map_data_tools_plan.md#high-resolution-area-handling-contract).

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


The shell layer sets locations and parameters; `analysis_river_point_info`, `analysis_upbasin`, `analysis_subbasin`, and other Python programs in `map/tools/code/` read and validate map data and perform the network calculations. No compilation is required; a02–a04 invoke shared Python programs under `map/tools/code/`, while a01 inspects river-point information.

The `a02-sample_subbasin.sh` writes `subbsn-sample.nc` and `subcol-sample.nc` directly in the map root. The editable Rhine-copy settings are `AREA_THRESHOLD1_KM2=30000` and `AREA_THRESHOLD2_KM2=5000`; set the second value empty for single-stage operation. These are example defaults, not universal scientific parameters. Stage 1 uses the existing upstream-area-increase rule; Stage 2 applies the smaller threshold only to previously unassigned river-network regions, preserves all positive Stage 1 IDs and boundaries, and assigns new IDs after them. Links into Stage 1 segments are terminal boundaries. In each stage, a link is cut when the current upstream area exceeds its threshold and the valid downstream area exceeds the current area by more than that threshold. Neither threshold guarantees a minimum segment area. Positive `subbsn` values are segment IDs, 0 marks remaining unassigned network cells, and -9999 marks outside-network cells. `subcol` uses the same spatial mask convention: positive IDs receive display colors 1–10, 0 marks unassigned network cells, and -9999 marks cells outside the network. These optional products are not simulation inputs.

[`a04-advanced_calc_upbasin.sh`](a04-advanced_calc_upbasin.sh) requires map-local `GRDC_alloc.txt` (normally produced by `t01-alloc_flow_gauge.sh`). It filters unallocated/invalid records, chooses the largest positive `area_CaMa` (first file row wins a tie), and uses that row's primary `ix1,iy1` cell. It prints the station selection and river-point information to stdout, and writes only `upbasin-<GRDC_ID>.nc` as a scientific output. Repeated execution replaces that map-root mask. The Mekong sample is `upbasin-2569002.nc`. The primary-cell upstream mask is not guaranteed to represent the complete aggregate drainage area of a gauge mapped to multiple catchments, so do not treat its cell count/area as equal to `area_CaMa` or observed drainage area.

The generic commands and a01–a04 examples are optional map-specific inspection workflows. The sample point coordinates in a01 and a03 are for the Mekong map; use the allocated-point a04 example where a fixed coordinate may fall outside another map or on an unrelated cell.

### Standard ELSE_GPCC grid tag

The global 1-degree ELSE_GPCC mapping pair uses `test-1deg`, matching v4:
`diminfo_test-1deg.nml` and `inpmat_test-1deg.nc`. This replaces the interim
v5 tag `test-glb_1deg` without changing grid geometry or matrix values. The
descriptor's embedded matrix filename must also match, because channel
parameter tools read that name. The pair supports global ELSE_GPCC runoff and
`map/data/ELSE_GPCC_clm-1981-2010.one` (annual-mean runoff in mm/s).
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

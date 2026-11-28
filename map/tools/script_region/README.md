# Regional map preparation

This guide documents the reusable v5 regional-map preparation template under `map/tools/`. It prepares a regional map from a compatible source map. The legacy v4 workflow remains under `map/src/src_region/` and is not modified here. Configure and execute `s01-regional_map.sh` for a target map; the Python programs under `map/tools/code/` perform each processing stage and should not be run separately for the standard workflow.

The scripts under `map/mekong_15min/` are maintained separately to create or update the official GitHub sample using the original global map distributed with CaMa-Flood packages. They are sample-preparation tools, not test scripts. GitHub CI does not run them. The reusable template documented here can be used to prepare other regional maps.

## Inputs and settings

The standard workflow reads map geometry from authoritative `params.nml` and
individual NetCDF products from the source map root. A TXT-only map may use
`params.txt` when the workflow is explicitly configured for Binary mode.

For the default NetCDF workflow, the source map must contain `params.nml`,
`nextxy.nc`, `downxy.nc`, `elevtn.nc`, `fldhgt.nc`, `ctmare.nc`, `grdare.nc`,
`uparea.nc`, `lonlat.nc`, `nxtdst.nc`, `rivlen.nc`, `width.nc`, and `bifori.csv`.
`catmpx.nc` and `class.nc` are optional supplementary int32 rasters; when
present, `region_cut_domain` crops their values over the full selected grid,
including non-river cells. `cut_bifway` filters `bifori.csv` using the crop
metadata and regional network. Explicit `--map-format binary` mode reads the
corresponding Binary products under `binary/`.

High-resolution cropping is optional. For each supported tag (`1min`, `30sec`, `15sec`, or `3sec`), the NetCDF source needs that directory's standard `location.csv`, which lists area names, bounds, dimensions, and cell size, plus the corresponding source layer files read by the combiner. Legacy Binary-only source maps may still have `location.txt`; migrate them to the standard inventory before using this NetCDF workflow. Some layers, including `flwdir`, are optional; when one is absent, the v5 combiner reports a `WARNING` and fills the corresponding output with its missing-value initialization. Missing required catchment lookup tiles (`catmxy`) remain errors and are skipped. If present, the workflow crops supported high-resolution tags in the order `1min`, `30sec`, `15sec`, `5sec`, `3sec`, `1sec`. INPMAT/DIMINFO generation is a separate Parameter workflow using explicit runoff-grid settings. These are external/source datasets; the repository's workflow code does not supply a replacement global map or runoff archive.

Copy the template into a map directory and edit the settings at the top of `s01-regional_map.sh`:

```sh
mkdir -p map/myregion_15min
cp -a map/tools/script_region map/myregion_15min/
```

```sh
SOURCE="../../glb_15min/"
WEST="90.0"
EAST="110.0"
SOUTH="5.0"
NORTH="35.0"
```

`SOURCE` is relative to the copied `script_region/` directory or absolute; keep the trailing slash. Choose bounds contained in the source map's coverage. The Mekong example uses the v400 global map and 90–110°E, 5–35°N.

## Build and run

No build is required. Run from the copied map-local `script_region/` directory and keep that directory as CWD throughout the workflow. The common initialization uses `CMF_V50_ROOT` to locate `map/tools/code/` and load shared error reporting. Map-root inputs and outputs are referenced relative to the script directory; script-local configuration and intermediate files use direct relative filenames. Each processing step calls its Python program directly and reports progress through `cmf_check_*`.

`s01-regional_map.sh` runs `region_cut_domain`, `region_cut_bifway`, `region_set_map`, and `region_combine_hires` for available source tags. It creates the regional base map and high-resolution layers only; it does not generate INPMAT/DIMINFO. After regionalization, run the Parameter `s01-inpmat_default.sh` or the appropriate input-grid-specific wrapper to create the mapping pair. The `test-1deg` settings describe the global 360 × 180 ELSE_GPCC grid used by `inp/ELSE_GPCC/runoffYYYY.nc` (daily, mm/day) and the annual mean climatology (mm/s). Each model map requires its own matrix. The wrapper obtains the input-grid edges and latitude order from its explicit settings; `HIRES_TAG` independently selects the high-resolution map source. Matrix generation uses `grdare` in km² where available and converts positive values to m² for overlap weights; coastal cells therefore contribute their land area.

## Outputs and checks

| Stage | Outputs | Role |
| --- | --- | --- |
| Script and crop metadata | `region_info.txt` and `dim_change.txt` in `script_region/` | Requested source/bounds and crop offsets/dimensions used by subsequent programs. |
| `cut_domain` | Parent map: authoritative `params.nml`; cropped `nextxy.nc`, `downxy.nc`, `elevtn.nc`, `fldhgt.nc`, `ctmare.nc`, `grdare.nc`, `uparea.nc`, `lonlat.nc`, `nxtdst.nc`, `rivlen.nc`, `width.nc`, `lsmask.nc`, and `nextxy_noedge.nc`; optional `catmpx.nc` and `class.nc` when supplied by the source | Cropped base-resolution NetCDF map fields and bifurcation-filter input. The optional supplementary rasters retain their source int32 values across every cell in the selected rectangle. |
| `cut_bifway` | Parent map: `bifori.csv` | Source bifurcation paths that remain within the regional network. |
| `set_map` | Parent map: `rivseq.nc`, `basin.nc`, `bsncol.nc`, `upgrid.nc`, `uparea_grid.nc`, `nxtdst_grid.nc`, `rivlen_grid.nc` | Derived river ordering, basin/visualization, and grid-based analysis products. `rivlen_grid.nc` intentionally contains the same downstream-distance array as `nxtdst_grid.nc` for rectangular-grid simulations. |
| `combine_hires` | Regional high-resolution tag directory, including `<tag>.<layer>.nc` files and `location.csv` | Cropped high-resolution NetCDF layers and standard geometry metadata, when corresponding source data are available. |
| Separate CTL step | `.ctl` files beside eligible binaries | GrADS descriptors based on base `params.nml` (or legacy `params.txt`) or high-resolution `location.txt`; not written by `s01`. |

Consult [`variable_table/map_variables.csv`](../../../variable_table/map_variables.csv) for per-product type, dimensions, record layout, numeric missing value, special codes, and model/runtime role. Core model inputs and preprocessing/analysis products are distinguished there; the table above names outputs without duplicating every variable definition.

## High-resolution downstream links

In high-resolution `downxy` files, record 1 (`downx`) and record 2 (`downy`) are signed 16-bit offsets on that same high-resolution grid. For a source pixel `(ix, iy)` with 1-based indices, add the two offsets to recover its downstream pixel: `(ix + downx, iy + downy)`. These are relative offsets, not absolute indices. FLOW adjusts the x offset for periodic wrapping at the global longitude seam. The paired sentinel values are `-999` for a river mouth and `-1000` for an inland termination. The output array starts at `-9999`; source inspection shows this remains when no downstream offset is assigned. The maintainer confirms `-9999` means sea in the low-resolution layer, but the high-resolution layer may use a different value for land pixels without an assigned unit catchment; that encoding remains unconfirmed. Consumers treat `downx <= -900` as a stop condition. The regional combiner preserves the offsets as-is. The common registry distinguishes the resolutions and records the unresolved high-resolution sentinel.

Review terminal output after each internal program. The shell stops on the first failed processing command and reports the current step. Confirm expected outputs exist, and NetCDF dimensions and coordinates agree with the generated `params.nml` / `location.csv` metadata. These checks establish file consistency only; they do not validate network correctness or scientific suitability. If GrADS descriptors are needed, run the separate Binary-format wrapper from the map-local `script_format_conv/` directory after reviewing map outputs:

```sh
cd ../script_format_conv
./s09-write_ctl.sh --dry-run
./s09-write_ctl.sh
```

The format-conversion wrapper uses map metadata to generate registered descriptors; existing CTLs are overwritten by default. The standard high-resolution `location.csv` has ordered fields `iarea,carea,west,east,south,north,nx,ny,csize`, with one data row per area. The explicit legacy Binary conversion boundary reads or writes `location.txt` as needed.

## Automated checks and scientific validation

The automated Mekong CTL check copies the tracked binary files and metadata to a temporary directory and runs the `s09-write_ctl.sh` wrapper from `script_format_conv/` there. It verifies CTL generation and file-format declarations without overwriting the checked-in sample. Other synthetic CTL generator checks and the sample/registry validators are listed in the [map-tools overview](../README.md#github-only-automated-tests). GitHub Actions does not execute this regionalization template or the Mekong sample-preparation scripts.

Successful regional product generation, binary size checks, and CTL generation do not establish that the river network or hydraulic fields are scientifically correct. No full simulation, independent river-network validation, or v4/v5 numerical equivalence test is claimed. Check the registry for variables whose meaning, special codes, or units remain provisional. The regionalization shell uses `set -eu` and stops at the first failed command; its error banner identifies the current step and preserves the command exit status. Inspect the expected products after a successful run.

## Multiple high-resolution areas

`location.csv` may list multiple source areas. `region_combine_hires` and regional default input-matrix generation iterate over the listed areas and combine contributions for the regional target. This source-level capability is separate from the single-area allocation tools. Full package-scale multi-area integration has not yet been run; see the [area contract and manual validation procedure](../../../docs/map_data_tools_plan.md#high-resolution-area-handling-contract).

The regional wrapper crops every available NetCDF source resolution in
`1min`, `30sec`, `15sec`, `5sec`, `3sec`, `1sec`. Explicit Binary mode reads
Binary-only inventories and layers from the corresponding `binary/` paths. Its
standard Input Matrix uses the first available regional grid in that same
coarsest-first order.

# River maps and map-preparation tools

For maintained code and workflow changes, see the [shared preprocessing code conventions](../docs/preprocessing_code_conventions.md) and local [agent instructions](AGENTS.md).

The `map/` directory connects CaMa-Flood's river and floodplain representation to the datasets and preprocessing tools used to prepare it. The GitHub source repository supplies map-processing code and documentation, plus the official `mekong_15min` development/test sample. Global source maps such as `glb_15min` are distributed separately in CaMa-Flood data packages. Check the map files included with your package and obtain any additional datasets required by the simulation.

For model setup and example runs, see the [v5 developer execution guide](../gosh_test/README.md). This page is an overview; tool-specific details remain in the component documentation linked below.

## Global additional data

The authoritative global 15-minute map is
`cmf_v5_package_data/map/glb_15min/`, outside the repository; a local
`map/glb_15min/` development copy is ignored by Git. The package catalog keeps
model-grid Binary, `netcdf/`, standard generated parameters and auxiliary text.
High-resolution distribution uses compressed `1min_nc/` and its `location.txt`;
`1min/` Binary is restored on demand, not shipped as a duplicate. Generation
scripts remain in GitHub under `map/tools/`. See the
[package selection policy](../package/README.md#global-15-minute-map-selection)
and [Binary restoration guide](tools/script_format_conv/README.md#restore-high-resolution-binary-working-files-s04).

## Japan additional data

`TE-Japan_01min/` is supplied through Package Additional Data, with authoritative
source `cmf_v5_package_data/map/TE-Japan_01min/`. Its model grid is 1-minute
(1500 × 1320 cells, 123–148°E, 24–46°N); supporting high-resolution maps are
15-second. Package selection includes model-grid Binary, `netcdf/`, standard
parameters and auxiliary text, plus compressed `15sec_nc/` and `location.txt`.
High-resolution `15sec/` Binary is restored on demand rather than distributed
in duplicate. Installed data are ignored locally, while map-specific preparation
scripts and their README files remain in Git. See the
[Japan selection policy](../package/README.md#japan-1-minute-map-selection).
Registration does not establish scientific validation or redistribution clearance.

## Development and test sample

`map/mekong_15min/` is the official GitHub development/test sample. The scripts retained in its map-local preparation directory are maintainer-operated tools to create or refresh this distributed sample from source data in the separate CaMa-Flood distribution package. They are not automated tests; the dataset's presence does not establish scientific validation or production suitability.

## What is a CaMa-Flood river map?

CaMa-Flood represents a river network as **unit catchments**: drainage areas associated with cells on a regular longitude/latitude grid. A map records how those cells connect downstream and supplies the geographical and hydraulic information needed to route water and diagnose river and floodplain conditions.

The model reads the downstream network, converts active grid cells into a river sequence for calculation, and combines that topology with catchment area, elevations, channel dimensions, reach lengths, and floodplain topography. These sub-grid parameters describe channel and floodplain properties that a model grid cell cannot represent explicitly. The map and parameters therefore work together; a river-network file alone is not a complete simulation map.

The source includes binary map readers and an optional NetCDF map path. The active map files and formats are selected in the model namelist. Consult the [scientific and user manuals](../doc/CaMa-Flood_Guideline.md) for the scientific formulation and detailed model setup.

## Obtain official map datasets

Use the [official CaMa-Flood website](https://global-hydrodynamics.github.io/CaMa-Flood/) for current package, map, registration, and download information. Map archives are distributed separately from the development repository; access may require registration and a license agreement. The website lists global maps at several resolutions and specialized Japan maps, with their current availability and download instructions.

The official page describes basic map datasets under CC BY 4.0 and notes that some advanced high-resolution data have separate access conditions. Dataset terms can differ. Check the current website and the license or agreement supplied with the exact dataset you use; the source-code license does not automatically apply to map data.

The GitHub repository includes the Mekong development/test map and v5 tools under `map/tools/`, plus historical templates under `map/src/`. The tracked Mekong inputs support the intended minimal repository test; larger maps belong to separately supplied data. The planned user package combines a selected source revision with approved Package Additional Data. The v5 assembler and complete fresh-clone regression workflow remain under development; see [the design specification](../docs/development_and_distribution_design.md).

## Directory organization

| Path | Role | Notes |
| --- | --- | --- |
| `map/tools/` | Shared v5 map-processing implementations, a unified Makefile, and reusable map-local workflow templates. | See the [v5 tools overview](tools/README.md) and [regional workflow guide](tools/script_region/README.md). |
| `map/src/src_param/` | Legacy v4 reusable source template for preparing or inspecting map parameters and forcing-to-map input matrices. | Has a [component README](src/src_param/README.md); copy the component into a target map directory to work with that map. |
| `map/src/src_region/` | Legacy v4 reusable source template for regional map preparation. | See the [v4 regional-map guide](src/src_region/README.md). |
| `map/tools/script_region/` | v5 regionalization template; copied into a target map directory and run with shared tools. | See the [v5 regional workflow guide](tools/script_region/README.md). |
| `map/src/src_dam/` | Legacy v4 reusable source template for preparing dam/reservoir locations and parameters for a target map. | Has an existing [reservoir-preparation README](src/src_dam/ReadMe.md). |
| `map/src/` | Historical v4 map-preparation tools, retained for users of the v4 workflows. | Contains `src_param/`, `src_region/`, and `src_dam/`; new v5 map-tool development belongs under `map/tools/`. It is separate from the model's numerical `src/`. |
| `map/<map-tag>/` | A map instance: downloaded map data, metadata, derived products, and any map-local processing copies needed for that workflow. | Examples include `glb_15min` and `conus_06min`; these datasets are supplied through distribution packages or separate map downloads. |
| `map/data/` | Tracked reference inputs and supporting data for map-preparation workflows. | Git tracks the curated `GRDC_allocated.csv`, `GRanD_allocated.csv`, `GRanD_alloc+Mekong.csv`, `MLIT_FlowGauge_alloc_final.csv`, and `MLIT_LevelGauge_allocated.csv` tables, plus the ELSE_GPCC runoff climatology used by the sample channel workflow. These processed tables are the approved allocation inputs; this does not imply unrestricted redistribution of source workbooks or databases. Other data such as GRSAD and ReGeom samples may be package-specific; check their availability and terms separately. |

### Reusable sources and map-local working copies

The legacy v4 directories `map/src/src_param/`, `map/src/src_region/`, and `map/src/src_dam/` are reusable workflow sources intended to be copied into the relevant map directory when preparing or extending that map. The v5 regional template is `map/tools/script_region/`; its shared programs remain under `map/tools/code/`. For example, the channel-parameter workflow is run from a map-local `src_param/`; the regionalization and reservoir workflows similarly use map-local working directories and relative paths. Copy only the components needed for the task. Some data-rich packages already include selected copies, but not every map directory contains every component.

Keep the distinction clear: `map/src/` holds source templates, while paths such as `map/glb_15min/src_param/` are working copies associated with an individual map. Copying creates a separate working copy; edits to a template do not automatically update copies already placed in map directories. These map tools operate on map data; they are not the model's numerical source tree at repository `src/`.

The v4.30 package-preparation workflow assembles `glb_15min/`, `conus_06min/`, and `tej_01min/` for the standard examples. Other maps require the corresponding downloads or regional preparation. If a map directory is a symbolic link, check that its target is accessible before running the model or preprocessing tools.

`glb_15min/` is the global 15-minute (0.25-degree) river map; `params.txt` records its dimensions and geographical coverage. Higher-resolution supporting files, such as those under `glb_15min/1min/`, are used by selected preprocessing and downscaling workflows. They do not change the base river-map resolution. Packages may also include prepared working copies such as `glb_15min/src_param/`; check which components and supporting layers are included with your map release.

The v5 map-processing programs use the ignored `config/Mkinclude`, configured through the [v5 build guide](../config/README.md). Historical v4 tools still expect their legacy adm settings. The v5 shared Makefile builds executables directly under `map/tools/code/`; regional scripts call them from map-local working directories. Map tools are separate from the numerical model executable in `src_main/`.

### Dataset, tools, and products are different things

| Category | Examples | How to treat it |
| --- | --- | --- |
| Distributed datasets | Global or Japan river-map archives and high-resolution supporting layers. | Obtain from the official project download page and follow the specific dataset terms. |
| Repository tools | Legacy v4 tools under `map/src/` and v5 shared code/templates under `map/tools/`. | These are source code for preparing, inspecting, or transforming data; they are not the datasets themselves. |
| Generated products | Regional network files, channel parameters, runoff input matrices, MPI region maps, and dam parameter tables. | Generate or obtain these for the selected map and configuration; keep their metadata and inputs together. |
| Optional ancillary data | Groundwater-delay, sea-level, reservoir, gauge, and high-resolution information. | Prepare only when a selected feature or workflow requires it; requirements are feature-specific. |

A successful build of the map tools does not supply external source datasets or create a complete ready-to-run map by itself. Conversely, a downloaded map may include precomputed products, so check its archive contents before regenerating parameters.

## Global and regional maps

A **global map** supplies a connected network and parameters over its published global domain at a selected grid spacing; `glb_15min/` is the global 15-minute example used by the standard runs. A **regional map** is derived for a smaller domain, usually by starting from a compatible global map and selecting region bounds. The regional tools adjust the network and related arrays to the regional grid and can combine available higher-resolution map information. Source global maps used for preparation are package data, not GitHub fixtures.

The legacy v4 regionalization template is under `map/src/src_region/`; the reusable v5 template is under `map/tools/script_region/`. These are map-preparation workflows, not automated tests. The v5 template can be copied to another target map directory, configured with a compatible source map and bounds, and run from its map-local `script_region/` directory. `s02-write_ctl.sh` is a separate CTL-generation step. See the [v5 regional workflow guide](tools/script_region/README.md) and [v5 tools overview](tools/README.md) for commands and limitations.

GitHub-only map-tools checks validate metadata, source functionality, and CTL generation using synthetic fixtures and the committed Mekong binary sample. They do not execute regionalization or require the distribution package's global data. See [GitHub-only automated tests](tools/README.md#github-only-automated-tests).

Examples of maps used by sample runs are listed in [the v5 workflow guide](../gosh_test/README.md). A regional map must remain consistent with its source resolution and extent, downstream connectivity, metadata, and parameter files. Do not substitute files from a different map tag merely because their filenames match.

## Shared map-product registry

[`variable_table/map_variables.csv`](../variable_table/map_variables.csv) is the source-linked variable and data-product registry for CaMa-Flood maps. It uses symbolic dimensions such as `NX`, `NY`, and `NLFP`, so the definitions apply across map resolutions and regional domains. It is the primary source for variable names, proposed long names and units, data types, record layouts, numeric stored missing values, meaningful special codes, product variants, distribution roles, and current model-reader mappings.

[`variable_table/map_metadata_spec.md`](../variable_table/map_metadata_spec.md) explains the CSV schema and how it relates to per-map `params.txt`, `mapdim.txt`, runoff/input-grid descriptors, and GrADS CTL files. v5 workflows pair `diminfo_<ROFFTAG>.txt` with `inpmat_<ROFFTAG>.bin`; legacy `diminfo_*.txt` names remain supported for existing v4 data and callers. `ROFFTAG` identifies the runoff/input-grid configuration, while `HIRES_TAG` selects high-resolution map data. The s03 standard is now `ROFFTAG=ERA5land_global`, matching the converted `repo-ERA5land-glb_2day` 0.1-degree runoff grid (3600 × 1801). The tag describes spatial geometry, not a time period or the model-map name (`glb_15min`, for example). Generate the paired matrix/descriptor separately for each model map; identical runoff geometry/order allows reuse across periods on that map. Global-map products are intended for Package Additional Data, and are not generated here.

The bifurcation workflow writes authoritative named `bifprm.csv` at the map root and its static NetCDF-4 counterpart at `netcdf/bifprm.nc`; the simulation reader accepts both plus legacy `bifprm.txt`. IDs in these products are configuration-specific row IDs, with endpoint indices used to identify paths across configurations. The channel-parameter entries describe products users generate or verify for a target map. Data-rich packages may include prepared examples; check the actual package contents before generating replacements. The v5 workflow writes the alternative MERIT Hydro merged width as `rivwth_merit.bin`; the preserved v4 workflow retains its historical `rivwth_gwdlr.bin` output.

### GrADS CTL generation

The v5 CTL generator is [`map/tools/code/generate_ctl.py`](tools/code/generate_ctl.py), invoked by the map-local [`s02-write_ctl.sh`](tools/script_region/s02-write_ctl.sh) wrapper. It reads `variable_table/map_variables.csv` and map geometry metadata, then validates registered binary layouts and file sizes before writing GrADS descriptors. The maintained [format-conversion workflow](tools/script_format_conv/README.md) also provides Binary-to-NetCDF, high-resolution NetCDF-to-Binary restoration, and optional numeric NetCDF-to-COG caches.

```sh
cd map/<map-tag>/script_region
./s02-write_ctl.sh --dry-run
./s02-write_ctl.sh
```

See the [v5 tools guide](tools/README.md#grads-ctl-files) for supported registry formats, missing-value handling, and current limitations. NetCDF map-reading support in the model is separate from map conversion tooling.

## Map parameters and preprocessing

`src/src_param/` supports several kinds of preparation:

- Estimating channel width and depth from long-term discharge inputs using the configured empirical relationships.
- Fusing channel-width estimates with Global Width Database for Large Rivers (GWD-LR) information where configured.
- Preparing bifurcation parameters and other river-network lookup data.
- Generating an `inpmat` lookup table that maps an external runoff grid onto the CaMa-Flood unit catchments. One matrix is specific to a map and a forcing-grid definition; it must match the forcing grid and its orientation.
- Allocating gauges, dams, or level stations, and creating basin, sub-basin, or other diagnostic products.

The [legacy v4 parameter-tools README](src/src_param/README.md) and the v5 [parameter workflow guide](tools/script_params/README.md) document the available workflows. Check each workflow's grid and format assumptions before reusing an input matrix; the v4 and v5 naming conventions are intentionally distinct.

### Reservoir and dam information

Reservoir operation uses additional dam locations and parameter data associated with the selected river map. The scripts in `src/src_dam/` link to reservoir datasets and combine them with naturalized simulation statistics to prepare a map-specific `dam_param.csv`. The procedure and fields are described in the [reservoir workflow README](src/src_dam/ReadMe.md) and the [Reservoir Operation manual](../doc/Manual_ReservoirOperation_v420.docx).

The dam table is optional and is needed only when reservoir operation is configured. Its locations and drainage areas must correspond to the target CaMa-Flood map. External reservoir source datasets have their own availability and license conditions.

## Other optional map information

A simulation may need map files beyond the basic network and topography, depending on its runtime options and build. Examples in the model namelist include:

- Bifurcation-channel parameters when bifurcation flow is enabled.
- Groundwater-delay and mean-sea-level parameters when those options are enabled.
- A dam-parameter table for reservoir operation.
- MPI region information for a distributed run.
- Higher-resolution layers used by selected regional, diagnostic, or specialized workflows.

Not every feature uses a file generated under `map/`, and some optional products are prepared under `etc/` or another component directory. Check the option's source, its namelist group, and its dedicated documentation before preparing additional files.

## Typical workflows

### Use an existing map

1. Obtain a map archive from the official project download page and review its terms.
2. Extract or reference the map in the location expected by your namelist and execution script.
3. Check that all required map files, metadata, grid dimensions, and optional products belong to the same map release and resolution.
4. Configure the map paths in the run namelist or sample script, then follow the appropriate [v5 run guide](../gosh_test/README.md).

### Create a regional map

1. Obtain a compatible source map and any high-resolution layers or sample runoff data the workflow needs.
2. Build the shared v5 regional programs with `make -C map/tools/code region`.
3. Copy `map/tools/script_region/` into the target map directory, configure `SOURCE` and the domain bounds in `s01-regional_map.sh`, then run it from the copied `script_region/` directory.
4. Review the program output and map dimensions/products; run `s02-write_ctl.sh` separately if GrADS descriptors are needed.
5. Prepare simulation-specific channel parameters and runoff input matrices in the separate `script_params/` workflow when available; the regionalization sample matrix is only for channel parameterization from sample runoff.

The [v5 regional workflow guide](tools/script_region/README.md) lists the current source requirements, outputs, and verification limits. The v4 template remains documented under `map/src/src_region/README.md`.

### Prepare additional parameters

1. Identify the exact missing parameter and which model option or forcing workflow needs it.
2. Confirm the target map tag, grid dimensions, resolution, orientation, units, and required source datasets.
3. Use the corresponding `src_param/` or specialized tool, following its own documentation.
4. Verify the generated file belongs with the target map and has the layout expected by the model reader or consuming workflow.

### Prepare optional map information

Check the feature-specific manual or workflow first. For reservoirs, see `src/src_dam/ReadMe.md`; for levees, see [`doc/levee.md`](../doc/levee.md). Optional features can require external datasets, build options, namelist groups, and matching map metadata in addition to an extra file.

## Map file organization and compatibility

Map directories are commonly named by region and grid spacing, for example `glb_15min` or `conus_06min`. The model's namelist explicitly names the map paths; scripts commonly set a base such as `FMAP` and build those paths from it. A directory name alone does not establish that its contents are complete or compatible.

The standard binary map path uses files such as `nextxy.bin` (downstream grid indices), `ctmare.bin` (unit-catchment area), `elevtn.bin`, `nxtdst.bin`, `rivlen.bin`, and `fldhgt.bin`; channel parameters may include `rivwth.bin`, `rivhgt.bin`, and `rivman.bin`. Runoff/input-grid descriptors carry dimensions and map bounds: v5 tools name them `diminfo_<ROFFTAG>.txt`, while existing v4 configurations retain `diminfo_*.txt`. The model's namelist key remains `diminfo_file`. Optional files and required names depend on the selected model options. The `NMAP` namelist in `src/cmf_ctrl_maps_mod.F90` shows the paths read by the model, while sample execution scripts show concrete configurations.

Many legacy `.bin` files are Fortran unformatted direct-access records, but the record contents and numeric types vary by file. For example, the `nextxy` reader expects two integer records; other readers expect real-valued parameters. Text metadata and tables may use `.txt` or `.csv`. The code also contains an optional NetCDF map reader, which requires a NetCDF-enabled build and matching NetCDF variables. Do not infer a complete file specification from the extension alone.

When combining or generating map products, keep dimensions, grid spacing, geographic bounds, latitude/longitude ordering, stored missing values and special codes, data types, and units consistent with the target map and reader. An input matrix must additionally match the runoff grid and orientation. Detailed format specifications belong with the relevant tool or manual rather than in this overview.

## Relationship to other directories

| Directory | Relationship to `map/` |
| --- | --- |
| [`src_main/`](../src_main/README.md) | Reads the configured network and map parameters and uses them during model initialization and simulation. |
| [`gosh_test/`](../gosh_test/README.md) | Provides sample build/run scripts that point to prepared maps and forcing data. |
| [`config/`](../config/README.md) | Supplies compiler and build configuration for the map tools and model. |
| [`inp/`](../inp/README.md) | Prepares runoff forcing; map input matrices connect that forcing grid to the selected river map. |
| `etc/` | Contains specialized workflows, some of which consume or prepare additional map-related data. |
| [`doc/`](../doc/CaMa-Flood_Guideline.md) | Holds user guidance and scientific/technical manuals. |

## Related documentation

- [Official CaMa-Flood website: maps, package downloads, and license information](https://global-hydrodynamics.github.io/CaMa-Flood/)
- [CaMa-Flood user guideline](../doc/CaMa-Flood_Guideline.md)
- [Main user manual](../doc/Manual_CaMa-Flood_v420.docx)
- [Reservoir operation manual](../doc/Manual_ReservoirOperation_v420.docx)
- [Parameter-processing tools](src/src_param/README.md)
- [Dam/reservoir parameter workflow](src/src_dam/ReadMe.md)
- [Model source architecture](../src_main/README.md)
- [Sample simulation workflows](../gosh_test/README.md)

## Simulation dimension information

`diminfo_<TAG>.txt` is **Simulation dimension information**, containing both
model-grid dimensions (`NX`, `NY`, `NLFP`) and runoff/input-grid dimensions
(`NXIN`, `NYIN`, `INPN`), plus geographic bounds when applicable.
`inpmat_<TAG>.bin` separately stores input-to-model cell correspondence.
The previous v5 `inpdim` name was reverted because it described only part of
the descriptor's role. File contents and scientific processing are unchanged;
there is no old-name fallback. Existing `CDIMINFO`/`diminfo_file` interfaces
are retained. See the [metadata specification](../variable_table/map_metadata_spec.md#diminfo_rofftagtxt--simulation-dimension-information).


## Numeric visualization caches

[script_format_conv](tools/script_format_conv/README.md#numeric-netcdf-to-cog-caches-s05)
replaces the maintained script_bin2nc directory. Scientific Binary/NetCDF inputs
remain authoritative. Optional COGs are generated at `COG/<model-variable>.tif`
from `netcdf/`, and `COG/<HIRES>/<area>.<variable>.tif` from `<HIRES>_nc/`.
Native numeric types/values and multiband record/layer order are preserved;
internal overviews use average for floats and nearest for integer codes/pairs.
COG trees are ignored by Git. Explorer COG consumption and package inclusion are
not implemented here. Untracked installed map workflows are not renamed automatically.

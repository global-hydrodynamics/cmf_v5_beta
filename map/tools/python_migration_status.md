# Experimental parallel Python map tools

Date: 2026-11-25 · Task DT-0184 · branch `feature/package-builder`.

## Workflow follow-up on `feature/package-builder`

The Python implementations are now the maintained execution path for the
`script_params/`, `script_region/`, and `script_format_conv/` Shell workflows.
Shell wrappers resolve shared code from `CMF5_ROOT` or the repository-relative
`map/tools/code/` path and use `PYTHON_CMD` (default `python3`). Fortran sources
remain preserved under `code/legacy_fortran/` for reference comparisons; this
does not alter model equations or map data formats. The status below records
the original implementation-comparison stage and is retained as historical
evidence; its statement that Shell workflows remain unchanged predates this
follow-up.

Maintained Python programs and their wrappers overwrite only their own existing
outputs by default. Explicit `--no-overwrite` is available on selected tools;
ordinary reruns do not require `--force`, prompts, or manual output cleanup.

## Scope and current decision

All **23 standalone programs** and **3 Fortran shared modules** in `code/` have
parallel Python implementations. `mod_map_io.py` is one additional small shared
Binary-I/O helper. Python implementations are experimental: the Fortran sources,
Makefile/compiler configuration, executable names, Shell templates, scientific
inputs and production defaults are unchanged. No production migration is made.

This is an L1 implementation/comparison task, with focused scientific-contract
checks. The maintainer explicitly permits rounding differences caused by changed
calculation order and prioritizes concise, efficient code. Integer/categorical
values, indexing, record layout, masks, thresholds and legacy scientific criteria
remain reference contracts.

## Program inventory and evidence

Every row has an independent `.py` executable, a successful reference build and
three repeated Mekong comparison runs. See the [performance report](python_migration_benchmark.md)
and [machine-readable cases](python_migration_benchmark.csv) for measurements.
A means a candidate at tested workloads; B means compatible with optimization
recommended. These classifications support a later researcher decision, not a
recommendation to replace the current production implementation automatically.

| Fortran / Python stem | Purpose | I/O contract | Evidence / readiness |
| --- | --- | --- | --- |
| [`allocate_dam.F90`](code/allocate_dam.F90) / [`.py`](code/allocate_dam.py) | Dam/main-river/subgrid allocation | Station CSV + base/native maps → three allocation tables | PASS; A |
| [`allocate_flow_gauge.F90`](code/allocate_flow_gauge.F90) / [`.py`](code/allocate_flow_gauge.py) | One/two-cell discharge station allocation | Station CSV + base/native maps → gauge_alloc.txt | PASS; A |
| [`allocate_level_gauge.F90`](code/allocate_level_gauge.F90) / [`.py`](code/allocate_level_gauge.py) | Level station/channel-position allocation | Station CSV + elevations/topology → gauge_alloc.txt | PASS; A |
| [`analysis_check_mpi_bifurcation.F90`](code/legacy_fortran/analysis_check_mpi_bifurcation.F90) / [`analysis_mpi_dropped_bifurcation.py`](code/analysis_mpi_dropped_bifurcation.py) | Reconstruct local-vector pathway retention | MPI regions + nextxy + bifprm.csv → counts/dropped CSV | PASS; A |
| [`analysis_mpi_region_color.F90`](code/analysis_mpi_region_color.F90) / [`.py`](code/analysis_mpi_region_color.py) | MPI region display colors | MPI region IDs → bsncol_mpi-N.bin | PASS; A |
| [`analysis_river_node_latlon.F90`](code/analysis_river_node_latlon.F90) / [`.py`](code/analysis_river_node_latlon.py) | List directed river links | Binary topology/outlets + bounding box → text | PASS; A |
| [`analysis_river_point_info.F90`](code/analysis_river_point_info.F90) / [`.py`](code/analysis_river_point_info.py) | Inspect river cell and immediate neighbors | NetCDF maps by default (explicit Binary legacy mode) + xy/latlon → labelled text | PASS; A |
| [`analysis_subbasin.F90`](code/analysis_subbasin.F90) / [`.py`](code/analysis_subbasin.py) | Two-stage upstream-area jump segmentation | nextxy/uparea + thresholds → segment/color int32 maps | PASS; A |
| [`analysis_upbasin.F90`](code/analysis_upbasin.F90) / [`.py`](code/analysis_upbasin.py) | Selected cell upstream mask | nextxy + 1-based target → int32 mask | PASS; A |
| [`param_bif_set_basin.F90`](code/param_bif_set_basin.F90) / [`.py`](code/param_bif_set_basin.py) | Channel/overland basin merging | basin + bifprm.csv → bifbsn/bifcol + optional diagnostic | PASS; A |
| [`param_bif_set_params.F90`](code/param_bif_set_params.F90) / [`.py`](code/param_bif_set_params.py) | Filter widths and estimate bifurcation depth | bifori + depth/outlets/basin → bifprm.csv + optional diagnostic | PASS; A |
| [`param_channel_calc_outclm.F90`](code/param_channel_calc_outclm.F90) / [`.py`](code/param_channel_calc_outclm.py) | Route annual-mean runoff | DIMINFO/INPMAT + Binary or NetCDF runoff → outclm.bin | PASS; A |
| [`param_channel_calc_rivwth.F90`](code/param_channel_calc_rivwth.F90) / [`.py`](code/param_channel_calc_rivwth.py) | Discharge-based width/depth/roughness | outclm + topology + coefficients → four Binary maps; optional rivpar.nc | PASS; A |
| [`param_channel_set_merit_width.F90`](code/param_channel_set_merit_width.F90) / [`.py`](code/param_channel_set_merit_width.py) | MERIT/power-law width combination | width/rivwth/nextxy → rivwth_merit.bin | PASS; A |
| [`param_inpmat_generate.F90`](code/param_inpmat_generate.F90) / [`.py`](code/param_inpmat_generate.py) | Configurable runoff-grid overlap matrix | native catmxy/pixel areas → diminfo + mixed int32/float32 INPMAT | PASS; A |
| [`param_mpi_set_basin.F90`](code/param_mpi_set_basin.F90) / [`.py`](code/param_mpi_set_basin.py) | MPI-specific iterative basin aggregation | basin + sorted bifprm.csv → temporary IDs/color + optional diagnostic | PASS; A |
| [`param_mpi_set_region.F90`](code/param_mpi_set_region.F90) / [`.py`](code/param_mpi_set_region.py) | Greedy basin-to-MPI-region assignment | temporary basin IDs + process count → mpireg-N.bin | PASS; A |
| [`param_water_calc_prmwat.F90`](code/param_water_calc_prmwat.F90) / [`.py`](code/param_water_calc_prmwat.py) | Permanent-water area aggregation | catmxy/rivwth/flddif/pixel area → capped prmwat.bin [m2] | PASS; A |
| [`region_combine_hires.F90`](code/region_combine_hires.F90) / [`.py`](code/region_combine_hires.py) | Native-tile crop/combine/copy | dim_change + binary high-resolution areas → regional native products | PASS; B |
| [`region_cut_bifway.F90`](code/region_cut_bifway.F90) / [`.py`](code/region_cut_bifway.py) | Crop original bifurcation paths | dim_change + bifori + edge-masked topology → regional bifori.txt | PASS; A |
| [`region_cut_domain.F90`](code/region_cut_domain.F90) / [`.py`](code/region_cut_domain.py) | Crop coarse river domain | region_info + source Binary maps → regional maps + dim_change | PASS; B |
| [`region_default_inpmat.F90`](code/region_default_inpmat.F90) / [`.py`](code/region_default_inpmat.py) | Fixed global 1-degree default matrix | native catmxy/pixel areas → default diminfo/INPMAT | PASS; A |
| [`region_set_map.F90`](code/region_set_map.F90) / [`.py`](code/region_set_map.py) | Derived coarse-grid network properties | nextxy/grdare → sequence/area/count/distance/basin/color maps | PASS; A |

Shared equivalents: [`mod_allocation_map_io.py`](code/mod_allocation_map_io.py),
[`mod_bifprm_csv.py`](code/mod_bifprm_csv.py), and
[`mod_map_color.py`](code/mod_map_color.py). Allocation matching helpers are shared
by the three allocation programs; there is no new package hierarchy or workflow
engine. Binary primitives are in [`mod_map_io.py`](code/mod_map_io.py).

## Independent execution

Use Python with NumPy; NetCDF4 is optional and only needed for the existing
channel-tools' `cdf` interfaces. No mandatory Numba dependency is introduced.
The reference programs' positional arguments are retained, with explicit
`--map-dir` and `--output-dir` options for isolated comparisons. Relative explicit
file arguments still resolve from the invocation directory. Without an explicit
output directory, the existing program's Fortran CWD convention applies (allocation
lists are written in CWD). At the initial comparison stage, existing output files were refused rather than replaced;
choose a new destination when rerunning. Console banners/spacing can differ.

```bash
# From the repository root; choose a new output directory.
python3 map/tools/code/analysis_upbasin.py 62 93 \
  --map-dir map/mekong_15min --output-dir /tmp/cmf-python-upbasin
python3 map/tools/code/param_inpmat_generate.py \
  1min 1 -180 180 90 -90 NtoS diminfo_trial.nml inpmat_trial.nc \
  --map-dir map/mekong_15min --output-dir /tmp/cmf-python-inpmat
```

Do not point a reference Fortran comparison run at an active map. The benchmark
scripts create independent map copies and only link high-resolution **inputs**.

## Scientific and format behavior

- Binary arrays use little-endian int32/float32 coarse records, int16 native
  catmxy/downxy, and int8 native classifications, matching the tested reference
  platform and [registry](../../variable_table/map_variables.csv). Python axes
  are `(record, north-to-south row, west-to-east column)`; x varies fastest.
  One-based indices and special `nextxy`/`catmxy` codes are retained.
- `catmxy` gives stored pixel assignments; `nextxy` gives river connectivity.
  Neither is reconstructed from geographic containment. Allocation remains
  intentionally limited to one native area, like the shared Fortran reader.
- INPMAT stores all X-index planes, then Y-index planes, then float32 overlap
  areas. Sparse slots retain first encounter order. The fixed regional default
  retains its distinct one-pixel area approximation; the configurable generator
  retains its legacy 10-by-10 scaled approximation when `grdare` is absent.
- Basin/MPI IDs, heap ties, greedy partition ties, channel-versus-overland
  ordering, convergence, and diagnostic classifications retain reference rules.
  River properties use NumPy topological fronts; small float32 accumulation
  differences are permitted by the maintainer's instruction.
- Regional cropping retains the edge-connected river exclusion in
  `nextxy_noedge.bin`. This is a separate product; the complete `nextxy.bin`
  remains complete. Optional `catmpx` and `class` are copied without river masks.
- High-resolution combined outputs keep first-filled catchment assignments and
  their classification companions, while auxiliary rasters use the last source
  area. Large-domain mode copies whole named tiles and preserves the reference's
  `catmx > -100` translation test; small combined mode uses `catmx > 0`.
  The reference's omission of `grdare` in the tiled branch and 3sec combined
  output is retained. Missing optional layers retain reference sentinels.
- Permanent water retains `(rivwth > 0 or rivwth == -1) and flddif <= 5`,
  including the documented legacy inclusion of `flddif == -9999`, and is capped
  at `ctmare`. The exact-5-m boundary and the missing-height interpretation are
  researcher-review questions, not silently corrected in this port.
- Bifurcation CSV start-coordinate ordering follows the current reader despite
  the older `bifori` header's lon/lat label discrepancy. End coordinates come
  from stored outlets. The inherited MERIT width branch order is unchanged.
- Optional NetCDF channel interfaces retain Binary map inputs. Runoff reads the
  first NetCDF time record; `rivpar.nc` retains dimensions, float32 data, units,
  long names and `missing_value=1e20`, including the reference's Binary -9999
  values. No new general NetCDF map interface is implied.

## Verification and limits

**PASS:** 23 CLI pairs / 68 output-or-stdout checks per repetition on Mekong;
13 focused tests (including both MPI modes and diagnostic records, 0.5-degree
south-to-north INPMAT, invalid mixed catmxy, fallback areas and overlapping tiles);
Binary and NetCDF channel interfaces; 1200² and 12000² synthetic 3sec inputs;
large coarse synthetic crop/network; whole-tile output branch. All 32 new Python
source/test files parse. Exact integer/mask/format checks are separate from
floating-point comparisons. Details and observed errors are in the performance
report. Source/Makefile/Shell protection checks are documented in
[VR-0228](../../research/records/validation_runs/VR-0228.md).

**Not established:** universal scientific correctness, real 3sec-map integration,
full global 30sec performance, multiple native areas in allocation, big-endian
platform compatibility, or a production migration decision. No local map supplied
a 3sec tile; high-resolution 3sec benchmarks are explicitly synthetic. Real Mekong
native data are 1min. Windows/Linux were not benchmarked. No model simulation or
full map-generation pipeline was run.

A full global **30arcsec coarse map has 43,200 columns**, beyond signed int16
catmx capacity (32,767). The inherited native assignment format therefore needs
an explicit format/indexing decision before claiming support for that future
coarse-grid resolution. INPMAT retains the reference 100-slot allocation for
three four-byte arrays per coarse cell (about 1.0 TiB at 43200 × 21600), before
other arrays/dictionaries; sparse/block construction needs further work at that
scale. Large arrays, per-basin structures, sequential merges,
and edge-connected tracing are further scaling risks. Existing scientific
inputs and format registries are deliberately unchanged.

# Variable tables

This directory contains shared, machine-readable specifications for variables and data structures used by CaMa-Flood v5. These tables describe model and file contracts across datasets; they are not dataset catalogs. The map registry includes binary, text-table, and static NetCDF products; bifurcation CSV/NetCDF products are generated together from one finalized CSV table. The model accepts the authoritative CSV, its NetCDF representation, and legacy TXT input. Schema and compatibility details are described in [map_metadata_spec.md](map_metadata_spec.md#bifurcation-parameter-tables).

- [`map_variables.csv`](map_variables.csv) documents map variables and products, including their meanings, units, types, dimensions, record layouts, missing values, and processing roles. See [`map_metadata_spec.md`](map_metadata_spec.md) for its schema and design notes.
- [`output_variables.csv`](output_variables.csv) documents model output names, meanings, units, internal variables, file precision, dimensions, temporal semantics, and output conditions.
- [`restart_variables.csv`](restart_variables.csv) documents Restart state names, meanings, units, internal and file precision, Binary record order, conditional state, and Storage-only behavior. Binary record positions after river and floodplain storage depend on `LSTOONLY` and the enabled groundwater, reservoir, and levee schemes; see the [Restart design and format notes](../src_main/README.md#normal-and-storage-only-restart-design).

Each table has its own schema and purpose; combining them into one CSV is not intended. Dataset registries describe specific products, sources, coverage, licensing, and access. For example, [`inp/runoff_datasets.csv`](../inp/runoff_datasets.csv) remains the registry for runoff datasets and is not part of this directory.

A separate `input_variables.csv` may be considered if future work needs a shared inventory for multiple time-varying model inputs. No such table is defined here yet.

In `map_variables.csv`, the `filename` column names the standard NetCDF product
for raster records (`.nc`). Binary compatibility filenames are derived by
changing `.nc` to `.bin` and placing the result under `binary/`; the Binary
record order and metadata remain unchanged. Text metadata keeps its actual
actual filename and format, including Fortran Namelist files. Input matrices
use one generic registry definition:
`diminfo_<ROFFTAG>.nml` and `inpmat_<ROFFTAG>.nc`. This template also covers
the existing Mekong `test-1deg` map configuration without a tag-specific
registry row. Conversion wrappers derive `binary/inpmat_<ROFFTAG>.bin` without
changing the three-record `inpx`, `inpy`, `inpa` layout.

For `output_variables.csv`, `alias_of` is the authoritative relationship between compatibility names and canonical outputs. Runtime initialization reads and validates the complete registry once, resolves columns by header, and caches the metadata selected for the run. Alias rows inherit long name, units, temporal type, and missing value from their canonical row; their required-option condition must agree as well. `internal_variable` and `internal_dtype` are informational and are not used to resolve model memory. The runtime reader uses `CMF_BASE` and `COUTVAR_TABLE` in `&NOUTPUT`: the latter defaults to `${CMF_BASE}/variable_table/output_variables.csv` and can point to another registry. The Fortran dispatcher associates each selected name with an explicit array argument to `OUTPUT_WRITE(name, array)`; metadata alone never determines which array is written. The `runoff`/`rofsfc` pair and `runoffsub`/`rofsub` pair use identical model arrays while preserving the requested output name.

## Current input-grid examples

Input matrices use `diminfo_<ROFFTAG>.nml` and
`inpmat_<ROFFTAG>.nc`; the existing `test-1deg` map pair is an instance of
this generic convention, not a separate registry definition. The configurable
example is `ERA5land_global`, matching `script_params/s01-inpmat_default.sh`
and the 3600 × 1801 global 0.1-degree grid of
`inp/repo-ERA5land-glb_2day/`. Its Binary compatibility file is
`binary/inpmat_ERA5land_global.bin`. The old E2O example is no longer
registered. Each model map requires a separate pair.
The ERA5 entry describes the current source/grid settings and does not claim
a generated, validated pair in the Mekong repository sample. The regional
`repo-mek_1deg` mapping is deliberately dataset-specific and is not registered
in this shared table. Migration source references point to current code;
references with no verified current counterpart have been removed.


Map Binary variants reuse standard rows through `--reference-binary`; specific
experimental filenames belong in Shell settings, not duplicate variable rows.
The Mekong `subbsn-sample` / `subcol-sample` definitions therefore resolve from
`subbsn.bin` / `subcol.bin`. See [the variant contract and separate future
input-matrix design](map_metadata_spec.md#standard-definitions-and-experimental-binary-names).


MPI-region metadata uses only `mpireg.bin` / `mpireg`. Numbered `mpireg-N.bin`
files are standard MPI process-count products automatically handled by s01/s02,
not s90 variants. See the [MPI-region conversion contract](../map/tools/script_format_conv/README.md#standard-numbered-mpi-region-maps).

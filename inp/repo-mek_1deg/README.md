# Repository Mekong 1-degree NetCDF runoff

This long-term, repository-sample dataset contains 32 annual files,
`runoff1979.nc` through `runoff2010.nc` (11,688 daily records). It replaces
`test-mek_1deg_nc/`; NetCDF is the standard input format, so `_nc` is omitted.
The independent [`repo-mek_1deg_bin/`](../repo-mek_1deg_bin/README.md) fixture
remains the short January–February 2000 Binary input dedicated to mek01.

## Data contract

- Region: cell edges 90–110°E, 5–35°N, identical to the Binary fixture.
- Grid: 20 longitude centers, 90.5–109.5°E; 30 descending latitude centers,
  34.5–5.5°N; 1-degree resolution.
- Variable: float32 `runoff(time, latitude, longitude)`, units `mm day-1`,
  missing value `-999`; no rescaling, averaging or precision reduction.
- Daily CF time coordinate with midnight-to-midnight `time_bounds`, calendar
  `proleptic_gregorian`; 365 or 366 records per annual file.
- NetCDF-4 with lossless deflate level 3 and shuffle.

The current 32 files total **16,348,190 bytes (about 15.6 MiB)**. The previous
six annual files (2000–2005) were tracked under the former directory name;
the renamed/expanded files remain unstaged for maintainer review. They are
eligible for Git tracking, not additional-data files to be ignored.

The source is the optional global additional dataset
`inp/ELSE_GPCC/runoffYYYY.nc`, supplied separately from the repository.
The regional sample's existing maintainer-approved redistribution scope is
retained; this does not establish redistribution permission for the global
source. Provenance: ELSE_GPCC, associated with Kim et al. (2009),
[doi:10.1029/2009GL039006](https://doi.org/10.1029/2009GL039006).

## Generate or regenerate

Use a Python environment with the repository's NumPy and netCDF4 dependencies.
From the repository root, generate all years into a **fresh output directory**:

```sh
bash inp/repo-mek_1deg/s00-extract_ELSE_GPCC.sh \
  --output-dir /tmp/mekong-netcdf-new --jobs 4
```

The defaults are years 1979–2010, four workers, input `inp/ELSE_GPCC/`, and
output beside this script (`inp/repo-mek_1deg/`). Both directory defaults are
resolved from the script location, independently of the caller's directory.
With the current files present, omitting `--output-dir` deliberately reports
existing-file errors. Existing data are never overwritten or deleted.

For sequential execution or a smaller retry:

```sh
bash inp/repo-mek_1deg/s00-extract_ELSE_GPCC.sh \
  --start-year 2000 --end-year 2001 --jobs 1 \
  --input-dir inp/ELSE_GPCC --output-dir /tmp/mekong-netcdf-check
```

`--jobs` must be positive. Each year runs the shared
[`extract_ELSE_GPCC.py`](../tools/extract_ELSE_GPCC.py) in a separate process,
with `--format netcdf --file-unit year`; no extraction algorithm is duplicated.
Workers run in batches of at most `--jobs` processes. Year-tagged results and
errors are printed together as each batch is collected. The wrapper uses
`python3` from the active PATH; activate the intended Python environment first. Other
years continue after a failure; the final summary lists failed years and exits
nonzero. Successful files remain available. Retry failed year ranges into a
fresh destination after correcting the cause; there is no overwrite option.

## Checks and model use

All 32 generated annual regional arrays were compared exactly with the matching
global NetCDF window. Leap-day counts were checked. The existing six files
were also compared against freshly generated files for values, coordinates,
decoded times/bounds, units, missing values and compression, then retained
without overwriting. Parallel and sequential execution, per-year failure
reporting and overwrite refusal were checked. These establish extraction
fidelity, not independent scientific validation or a new model regression run.

`gosh_test/mek02-2year_netcdf.sh` selects `ROFFTAG="repo-mek_1deg"` and retains
its existing 2000–2001 run interval, `CROFFREQ="YEAR"`, and
`INPMAT_TAG="test-mek_1deg"`. That input matrix describes this same grid;
its historical tag does not refer to a required runoff directory.

See [input tools and format guidance](../README.md#regional-extraction-from-global-netcdf)
and [NetCDF output conventions](../../docs/netcdf_output_conventions.md).

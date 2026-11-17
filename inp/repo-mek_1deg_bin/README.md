# Repository Mekong 1-degree Binary runoff sample

This small Git-tracked sample is dedicated to `gosh_test/mek01-default_run.sh`.
It contains daily runoff for **2000-01-01 through 2000-02-29**, grouped into two
monthly files, rather than monthly averages. The experiment still runs its
original 40-day interval (2000-01-01 through 2000-02-10, end exclusive).

| File | Daily records | Bytes |
| --- | ---: | ---: |
| `runoff/Roff____200001.one` | 31 | 74,400 |
| `runoff/Roff____200002.one` | 29 | 69,600 |

The grid has 20 longitude columns and 30 latitude rows: cell edges 90–110°E,
5–35°N; centers 90.5–109.5°E and 34.5–5.5°N. Each daily record is 2,400 bytes:
little-endian float32, longitude fastest, north-to-south rows, with no Fortran
record markers. Units remain `mm day-1`, missing value `-999`, with no scaling,
aggregation or precision reduction. The existing map-specific
`inpmat_repo-mek_1deg.bin` and its dimension file describe exactly this grid.

Use `CROFFREQ="MON"`, `CROFPRE="Roff____"`, `CROFSUF=".one"`,
`LINPCDF=.FALSE.`, `IFRQ_INP=24`, and `DROFUNIT=86400000`.
The model indexes records from 00:00 on the first day of each month.

## Regeneration

Install the repository's NumPy and netCDF4 Python dependencies and provide the
optional global annual NetCDF files under `inp/ELSE_GPCC/`. From this directory:

```sh
sh s01-extract_runoff.sh
```

Existing output files are never overwritten. Generate into another directory
for comparison, or deliberately remove reviewed generated files before rerunning.
The general CLI and its boundary/date rules are documented in
[the input guide](../README.md#regional-extraction-from-global-netcdf).

This sample replaces the former `test-mek_1deg/` daily Binary collection. Its
60 daily fields were compared byte-for-byte with that collection and matched;
the generated monthly data also matched the corresponding global NetCDF slices
exactly. These are extraction/format checks, not independent scientific validation.
The source product is ELSE_GPCC, associated with Kim et al. (2009),
[doi:10.1029/2009GL039006](https://doi.org/10.1029/2009GL039006).
The existing maintainer-approved regional sample redistribution scope is retained;
this does not establish permission to redistribute the full global product.

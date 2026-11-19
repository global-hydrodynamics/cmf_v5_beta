# ERA5-Land runoff download and NetCDF conversion

Shell holds user settings, selects jobs, manages concurrency and retains logs.
Python handles CDS requests, calendar planning, NetCDF conversion and metadata.
This replaces `inp/ERA5-Land_download/`. Binary conversion is retired.

## Why three layers?

| Layer | Responsibility |
| --- | --- |
| **Product Shell — user configuration** (`sample-global_2day.sh`, `sample-japan_hourly.sh`) | Set the dataset, region, period, timestep and file grouping; pass these settings to s01 and s02; execute download then conversion. Users normally edit only this layer. |
| **s01 — download** (`s01-download.sh`) | Split the requested period into daily or monthly CDS requests, retain original NetCDF and manage download jobs. Does not convert runoff values. |
| **s02 — convert** (`s02-convert_CMF_nc.sh`) | Read downloaded files, convert accumulated runoff to timestep runoff, combine/reorganize inputs as needed, and save the selected daily/monthly/yearly output grouping. Does not contact CDS. |

This separation supports download reliability and restartability. Smaller
requests limit request size and the impact of timeouts or transfer failures.
Successful files can be reused, and failed periods can be requested again
without retrieving the entire product. Requests can run in parallel when
appropriate. Neither daily nor monthly requests are always preferable: choose
according to CDS limits, network conditions and the requested domain.
Retaining originals also allows conversion to be repeated or regrouped without
another download. `workflow.sh` shares the stages' orchestration; Python performs
the requests and scientific data processing.

## File grouping versus time resolution

| Setting | Purpose | Supported values |
| --- | --- | --- |
| `DOWNLOAD_UNIT` | CDS request/source-file grouping | `daily`, `monthly` |
| `OUTPUT_UNIT` | Converted CaMa-Flood NetCDF file grouping | `daily`, `monthly`, `yearly` |
| `TSTEP` | Runoff time resolution, in hours | `1`, `2`, `3`, `4`, `6`, `8`, `12`, `24` |

**File grouping does not imply temporal averaging.** Hourly runoff stored in
monthly files still has hourly records. Download and output grouping are
independent and need not match:

- **A — daily download → daily output (supported):** hourly data occupy 24
  records in each full-day file; the Japan hourly sample uses this layout.
- **B — daily download → monthly output (supported):** s01 makes small daily
  requests; s02 combines the files into monthly NetCDF, keeping hourly records
  when `TSTEP=1`.
- **C — monthly download → yearly output (supported):** s02 combines monthly
  inputs into yearly NetCDF (12 inputs for a complete year), retaining the
  timestep records without averaging.

These examples explain storage and request organization. Splitting downloads
or combining files does not resolve the scientific time-attribution issue in
KG-0019, described below; the conversion calculation is unchanged by this
documentation update.

## Tools and output locations

| File | Role |
| --- | --- |
| `s01-download.sh` | Argument-driven download stage (daily/monthly source NetCDF) |
| `s02-convert_CMF_nc.sh` | Argument-driven conversion stage (daily/monthly/yearly NetCDF and information) |
| `sample-global_2day.sh` | Download, convert and summarize global January 1–2, 2000 |
| `sample-japan_hourly.sh` | Download, convert and summarize Japan, September 1–10, 2007 |
| `workflow.sh` | Shared Shell arguments, execution, jobs and logs |
| `download_era5land.py` | Standalone CDS client and request dry-run |
| `convert_CMF_nc.py` | Standalone accumulated-runoff conversion |
| `make_CMF_runoff_info.py` | Standalone NetCDF grid/forcing information |
| `plan_periods.py` | Validate destinations and split inclusive job periods |
| `tests/` | Offline request, compatibility and wrapper checks |

No downloaded or generated data belong in this tool directory. Output belongs
in a dataset directory directly beneath `inp/`:

```text
inp/repo-ERA5land-jpn_hourly/
├── original/ERA5-Land_runoff_20070901.nc
├── README.md
├── runoff_20070901.nc
├── ...
├── runoff_20070910.nc
├── runoff_info_CaMaFlood.txt
└── logs/
    ├── download.<run-id>/20070901.log
    └── convert.<run-id>/20070901.log
```

The converted repository products are [`repo-ERA5land-glb_2day`](../repo-ERA5land-glb_2day/README.md)
(one monthly file, two daily records) and
[`repo-ERA5land-jpn_hourly`](../repo-ERA5land-jpn_hourly/README.md)
(ten daily files, 24 hourly records each). Both exist locally; the Japan files
are already tracked, and the renamed global product is eligible for tracking.
Only the converted files and README belong in Git; originals, logs and generated
information remain ignored. Review download-specific attribution/licence
information before publication. Header inspection is not model or scientific
validation; GOSH/input-matrix integration and KG-0019 remain open.

## Standard workflow and registry

Edit a Product Shell and run it: s01 saves source data under `original/`, then
s02 differences accumulated runoff, converts metres to timestep millimetres,
reorganizes file grouping and writes CaMa-Flood variables/dimensions/metadata.
Use the finished `runoff_*.nc` as forcing; normally do not point the model at
`original/`. The [runoff registry](../runoff_datasets.csv) describes finished
products. Their source files are provenance in `data_source`, `source_url`
and `notes`, not parallel standard-input records. The registry is descriptive,
not read by the model at runtime; metadata review does not establish scientific
validation.

## Settings and execution

Use Bash (including macOS Bash 3.2) and a Python environment with `cdsapi`,
NumPy, pandas, xarray and netCDF4; see root `requirements.txt`. Real downloads
require CDS credentials and acceptance of the
[ERA5-Land dataset's access/licensing terms](https://cds.climate.copernicus.eu/datasets/reanalysis-era5-land).
Keep credentials out of scripts/commits; redistribution requires review.

Each `sample-*.sh` is a product-generation Shell with a `User settings` section using explicit
`VAR=value` assignments for dataset, period, domain, timestep and grouping.
Edit these assignments or use explicit CLI options; inherited environment
values do not override these experiment settings. The Japan product uses literal `PYTHON_CMD="python3"` and `NCPUS=2`.
The global product retains its documented runtime environment
overrides; explicit `--python` and `--ncpus` options take precedence in either product.
Sample settings:

| Setting | Global sample | Japan sample |
| --- | --- | --- |
| `DATASET` | `repo-ERA5land-glb_2day` | `repo-ERA5land-jpn_hourly` |
| `START_DATE`, `END_DATE` | 2000-01-01, 2000-01-02 | 2007-09-01, 2007-09-10 |
| `WEST`, `EAST`, `SOUTH`, `NORTH` | -180, 180, -90, 90 | 120, 150, 20, 50 |
| `TSTEP` | 24 hours | 1 hour |
| `DOWNLOAD_UNIT`, `OUTPUT_UNIT` | monthly, monthly | daily, daily |
| `NCPUS` | 1 | 2 |

Inspect requests without network access or output files:

```sh
bash inp/download_ERA5-Land/sample-global_2day.sh --dry-run
bash inp/download_ERA5-Land/sample-japan_hourly.sh --dry-run
```

After reviewing settings and configuring CDS, omit `--dry-run` to download,
convert and display the report. Absolute-path invocation works from any working
directory. A failed download stops the product before conversion. Neither
stage has independent scientific/experiment defaults to edit; the Product Shell
passes them explicitly to both stages.

The only supported format is `FORMAT="netcdf"` / `--format netcdf`. Binary
conversion remains retired. To repeat conversion independently, supply its
settings explicitly, for example:

```sh
bash inp/download_ERA5-Land/s02-convert_CMF_nc.sh \
  --dataset repo-ERA5land-jpn_hourly \
  --start-date 2007-09-01 --end-date 2007-09-10 \
  --tstep 1 --download-unit daily --output-unit daily --format netcdf
```

`--help` lists period, area, timestep, grouping, `--ncpus` and `--python`
overrides. `PYTHON_CMD`/`--python` selects an executable, not a command string.
Dataset names must be single names containing letters, digits, `_` or `-`;
path separators and symlinks escaping the dataset are rejected. The standard `original/`, `logs/`, `runoff_*.nc` and information-file
layout is Git-ignored even when a custom dataset name is chosen, except for the
explicitly enabled converted files in the two `repo-ERA5land-*` samples.

Existing data and information files are skipped/retained by default. Only
explicit `--overwrite` permits replacement. A skip does not verify contents or
refresh old metadata; use a new dataset name when changing period/resolution,
or explicitly regenerate the relevant files.

Each job owns its Python process and log. At most `NCPUS` jobs run in a batch; 1 is sequential.
Failures identify the period/log, allow other jobs in the stage to finish,
and exit nonzero before the next stage. Logs from earlier runs are retained.
Dry-run prints CDS request dictionaries and conversion plans without requiring
source files, contacting CDS or creating directories. Python tools remain
independently callable; consult their `--help` options.

Daily conversion requires the complete expected sequence of timestamps:
for `TSTEP=1`, exactly 00–23 UTC, once each. Missing/duplicate records cause an
error before writing; no missing hours are synthesized. After conversion, s02
lists the output destination and generated NetCDF files. Checking 24 records
establishes structural completeness, not physical time attribution.

## Advanced usage

Run `s01-download.sh` alone when only source acquisition is needed, or rerun
`s02-convert_CMF_nc.sh` independently against retained originals. No conversion
skip option is needed. Direct original-NetCDF model input is an advanced option
only when the reader supports its layout. Verify accumulation period and time
labels, variable/coordinate/time names, units and `DROFUNIT`, grid geometry and
the matching Input Matrix. Raw metadata compatibility does not validate physical
time attribution. This is not the standard sample configuration.

## Scientific behavior and unresolved time attribution

Calculation is preserved: within each UTC-date group, keep its first accumulated
value by default (`--first-step keep`), difference subsequent values, substitute
the current accumulation after a negative difference, and clip negative
increments by default. The Python CLI retains `zero`/`missing` first-step
options and `--no-clip-negative`. Missing values keep the existing handling.
Multiply metres by 1000 to obtain **millimetres per input timestep**, with
units `mm`; no rate conversion, new resampling or timestamp shift is introduced.
Longitude stays as downloaded; latitude defaults to N-to-S. The writer explicitly
orders `runoff(time, lat, lon)`, preventing xarray differencing from moving time
to the final file dimension for subdaily input. NetCDF-4 uses float32, fill
value `1e20`, lossless deflate level 3 and shuffle.

For CaMa-Flood, select the actual grid/input matrix and coordinate names,
`LINPCDF=.TRUE.`, `CROFFREQ="DAY"`/`"MON"`/`"YEAR"`, `CROFPRE="runoff_"`,
`CROFSUF=".nc"`, `CVNROF="runoff"`, `IFRQ_INP=TSTEP`, and
`DROFUNIT=1000*TSTEP*3600`. The model does not derive unit conversion from the
NetCDF units attribute. The information helper derives edges from coordinate
centers; requested geographic bounds need not equal the downloaded cell edges.
For example, the historical global source had 3600 × 1801 centers,
longitude -180..179.9 and latitude 90..-90; cell edges at 0.1 degree are
-180.05..179.95 and -90.05..90.05. Confirm each product's actual geometry.

**KG-0019 remains unresolved:** ERA5-Land's 00 UTC accumulation can belong to
the preceding 24-hour interval. First-record attribution and period-boundary
coverage are not scientifically verified. The existing calendar-date grouping
and timestamp treatment are compatibility behavior, not a resolution of this
question. See [KG-0019](../../research/records/knowledge_gaps/KG-0019.md).
A successful sample or synthetic check does not establish scientific correctness
or correct temporal attribution.

## Offline checks

```sh
python3 -B -m unittest discover -s inp/download_ERA5-Land/tests -v
```

Tests check requests/dry-run, small synthetic accumulated fields, reset/missing
behavior, units, dimension order, lossless compression, paths, skip/overwrite
and failed-job reporting. They never contact CDS. This reorganization performs
no real download, full global conversion or model simulation.

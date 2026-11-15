# ERA5-Land runoff download and NetCDF conversion

Shell holds user settings, selects jobs, manages concurrency and retains logs.
Python handles CDS requests, calendar planning, NetCDF conversion and metadata.
This replaces `inp/ERA5-Land_download/`. Binary conversion is retired.

## Tools and output locations

| File | Role |
| --- | --- |
| `s01-download.sh` | Argument-driven download stage (daily/monthly source NetCDF) |
| `s02-convert_CMF_nc.sh` | Argument-driven conversion stage (monthly/yearly NetCDF and information) |
| `sample-global_2day.sh` | Download, convert and summarize global January 1–2, 2000 |
| `sample-japan_1month.sh` | Download, convert and summarize Japan, January 2000 |
| `workflow.sh` | Shared Shell arguments, execution, jobs and logs |
| `download_era5land.py` | Standalone CDS client and request dry-run |
| `convert_CMF_nc.py` | Standalone accumulated-runoff conversion |
| `make_CMF_runoff_info.py` | Standalone NetCDF grid/forcing information |
| `plan_periods.py` | Validate destinations and split inclusive job periods |
| `tests/` | Offline request, compatibility and wrapper checks |

No downloaded or generated data belong in this tool directory. Output belongs
in a dataset directory directly beneath `inp/`:

```text
inp/ERA5land-jpn_1month/
├── original/ERA5-Land_runoff_200001.nc
├── runoff_200001.nc
├── runoff_info_CaMaFlood.txt
└── logs/
    ├── download.<run-id>/200001.log
    └── convert.<run-id>/200001.log
```

Existing Japan source/converted data and logs were relocated without
regeneration. Historical Binary CTL/report files are preserved only in
`inp/ERA5land-jpn_legacy_bin/`, with no maintained Binary conversion workflow.
Generated `ERA5land-*` dataset directories are Git-ignored. The historical
global source metadata in the input registry do not validate a new download
or converted global sample.

## Settings and execution

Use Bash (including macOS Bash 3.2) and a Python environment with `cdsapi`,
NumPy, pandas, xarray and netCDF4; see root `requirements.txt`. Real downloads
require CDS credentials and acceptance of the
[ERA5-Land dataset's access/licensing terms](https://cds.climate.copernicus.eu/datasets/reanalysis-era5-land).
Keep credentials out of scripts/commits; redistribution requires review.

Each `sample-*.sh` is a product-generation Shell with a `User settings` section using explicit
`VAR=value` assignments for dataset, period, domain, timestep and grouping.
Edit these assignments or use explicit CLI options; inherited environment
values do not override these experiment settings. `PYTHON_CMD` and `NCPUS`
intentionally retain environment overrides for Python selection and job
resources (`${VAR:-default}`); `--python` and `--ncpus` take precedence.
Sample settings:

| Setting | Global sample | Japan sample |
| --- | --- | --- |
| `DATASET` | `ERA5land-glb_2day` | `ERA5land-jpn_1month` |
| `START_DATE`, `END_DATE` | 2000-01-01, 2000-01-02 | 2000-01-01, 2000-01-31 |
| `WEST`, `EAST`, `SOUTH`, `NORTH` | -180, 180, -90, 90 | 122, 154, 24, 46 |
| `TSTEP` | 24 hours | 24 hours |
| `DOWNLOAD_UNIT`, `OUTPUT_UNIT` | monthly, monthly | monthly, monthly |
| `NCPUS` | 1 | 1 |

Inspect requests without network access or output files:

```sh
bash inp/download_ERA5-Land/sample-global_2day.sh --dry-run
bash inp/download_ERA5-Land/sample-japan_1month.sh --dry-run
```

After reviewing settings and configuring CDS, omit `--dry-run` to download,
convert and display the report. Absolute-path invocation works from any working
directory. Each product Shell explicitly invokes `s01-download.sh` and then
`s02-convert_CMF_nc.sh`, passing the same dataset, period, domain, timestep,
file grouping, format, Python executable and concurrency as arguments. A failed
download stops the product before conversion. Neither stage has independent
scientific/experiment defaults to edit; `workflow.sh` contains their shared
implementation, not the product configuration.

The only supported format is `FORMAT="netcdf"` / `--format netcdf`. Binary
conversion remains retired. To repeat conversion independently, supply its
settings explicitly, for example:

```sh
bash inp/download_ERA5-Land/s02-convert_CMF_nc.sh \
  --dataset ERA5land-jpn_1month \
  --start-date 2000-01-01 --end-date 2000-01-31 \
  --tstep 24 --download-unit monthly --output-unit monthly --format netcdf
```

`--help` lists period, area, timestep, grouping, `--ncpus` and `--python`
overrides. `PYTHON_CMD`/`--python` selects an executable, not a command string.
Dataset names must be single names containing letters, digits, `_` or `-`;
path separators and symlinks escaping the dataset are rejected. The standard `original/`, `logs/`, `runoff_*.nc` and information-file
layout is Git-ignored even when a custom dataset name is chosen.

Existing data and information files are skipped/retained by default. Only
explicit `--overwrite` permits replacement. A skip does not verify contents or
refresh old metadata; use a new dataset name when changing period/resolution,
or explicitly regenerate the relevant files.

Downloads support daily/monthly files; conversions support monthly/yearly
files. Grouping retains timestep records without averaging. Each job owns its
Python process and log. At most `NCPUS` jobs run in a batch; 1 is sequential.
Failures identify the period/log, allow other jobs in the stage to finish,
and exit nonzero before the next stage. Logs from earlier runs are retained.
Dry-run prints CDS request dictionaries and conversion plans without requiring
source files, contacting CDS or creating directories. Python tools remain
independently callable; consult their `--help` options.

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
`LINPCDF=.TRUE.`, `CROFFREQ="MON"`/`"YEAR"`, `CROFPRE="runoff_"`,
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

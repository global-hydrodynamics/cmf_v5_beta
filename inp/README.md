# Runoff input data and preparation

The `inp/` directory contains tools for preparing runoff forcing used by CaMa-Flood. Runoff supplies water per unit land area over time; CaMa-Flood converts it to a flow rate for routing through the river network. The GitHub repository includes an ERA5-Land download and conversion workflow with small Japan examples. Distribution packages also include sample forcing for selected `gosh/` runs. Obtain or prepare additional forcing when the chosen experiment requires data beyond those supplied with the package.

The GitHub repository also tracks the Binary `repo-mek_1deg_bin/` and annual NetCDF `repo-mek_1deg/` samples for minimal Mekong development runs; these do not require the larger additional-data package. The current v5 execution examples are under `gosh_test/`. Package Additional Data and the generated user package have distinct roles in [the maintained design](../docs/development_and_distribution_design.md); v5 assembly is planned, not an existing download/build procedure.

For format and compression settings used by NetCDF files generated with v5 tools, see the shared [NetCDF output conventions](../docs/netcdf_output_conventions.md). External NetCDF forcing inputs are not required to use those output settings.

## Using Your Own Runoff Dataset

1. Prepare runoff files in a supported [Binary or NetCDF layout](#supported-input-formats-and-simulation-settings).
2. Identify the input-grid resolution and geographic boundaries, latitude row order, temporal resolution, runoff units and accumulation meaning, missing-value encoding, and filename pattern from the source data and documentation.
3. Copy the shared [`s03-generate_inpmat.sh` template](../map/tools/script_params/s03-generate_inpmat.sh) into the target map's `script_params/`, configure its settings, and [generate the Input Matrix](#preparing-the-input-matrix). The runoff grid may have a different spatial resolution and extent from the CaMa-Flood river map.
4. Configure the relevant v5 `gosh_test/` or tutorial simulation script with matching file paths and format, `IFRQ_INP`, `DROFUNIT`, and the matching `CDIMINFO`/`CINPMAT` pair; see [simulation settings](#supported-input-formats-and-simulation-settings).
5. Run a short simulation and check the log, dates, and runoff/discharge values for correct loading and reasonable magnitudes.
6. Optionally document the dataset and its provenance in [`runoff_datasets.csv`](runoff_datasets.csv) when sharing it with other users.

## Directory organization

NetCDF is the standard v5 input format: new NetCDF dataset names normally omit `_nc`, while Binary variants use `_bin` where necessary. Existing sample names remain unchanged until their compatibility is reviewed.

| Path | Purpose and contents |
| --- | --- |
| `tools/` | Shared runoff dataset helpers: [`extract_ELSE_GPCC.py`](tools/extract_ELSE_GPCC.py) extracts regional daily data from global annual NetCDF, and [`validate_runoff_datasets.py`](tools/validate_runoff_datasets.py) checks the input registry without reading datasets. Execution examples appear below. |
| `download_ERA5-Land/` | Shell settings/job control and standalone Python CDS/NetCDF tools. No data are stored here; see the [ERA5-Land guide](download_ERA5-Land/README.md). Binary conversion is retired. |
| `ERA5land-glb_2day/` | Destination for the optional global two-day sample: source files in `original/`, converted monthly NetCDF and logs in the dataset root/subdirectories. This refactor does not download or validate a new global sample. Git-ignored. |
| `ERA5_land/daily/` | Canonical north-south half-grid geometry (90° to −90° cell centers; 3,600 × 1,801 at 0.1°). Only one local daily-named binary sample (1960-01-01) is currently present; its units, missing-value meaning, longitude order, and full coverage are unconfirmed. |
| `ERA5_land/Roff/` | Legacy 1981–2020 daily binary series, 3,600 × 1,800. The maintainer confirms it omits the north-south half-grid shift and is not the canonical geometry. Neither series is tracked or distributed; see both registry entries. |
| `ELSE_GPCC/` | Optional global daily NetCDF runoff, 1979–2010, one `runoffYYYY.nc` file per year. Supplied through the separate additional-data store and ignored by Git; see the [package catalog](../package/package_data.csv). Formerly named `ELSE_GPCC_nc/`; the previous Binary dataset at this path has been removed. Redistribution conditions and model-input validation remain unconfirmed. |
| `test-glb_1deg/` | Historical global 1-degree, daily two-year test extraction (2000–2001) from the former Binary `ELSE_GPCC/Roff/`. Regeneration requires a separately supplied Binary source; the new NetCDF directory cannot be used directly. Scripts and metadata are tracked; generated `Roff/` binaries are Git-ignored pending redistribution review. See the [sample README](test-glb_1deg/README.md). |
| `repo-mek_1deg_bin/` | Minimal Git-tracked Mekong Binary sample for mek01: 60 daily fields for January–February 2000, grouped into two monthly files (144,000 bytes total). See the [sample README](repo-mek_1deg_bin/README.md). |
| `repo-mek_1deg/` | Long-term Mekong NetCDF test data, 1979–2010: 32 annual files extracted from global `ELSE_GPCC/`. See the [dataset README](repo-mek_1deg/README.md) for parallel generation and validation. |

## Runoff Dataset Registry

[`runoff_datasets.csv`](runoff_datasets.csv) is a human-readable metadata registry of runoff datasets that can be used with CaMa-Flood. The model does not read this CSV at runtime, and registration is optional: users can run their own runoff data without modifying it. They must still identify the dataset's spatial grid, temporal interval and meaning, units, missing-value convention, and file format, then configure those values correctly in the map-preprocessing and simulation scripts.

An entry is recommended when sharing a dataset with collaborators or other users. It records the configuration needed to reproduce the setup, along with file patterns, provenance, and access or distribution information. Empty fields are not established values; check `configuration_status` and `notes` before reusing an entry. For usability and maintenance, use the naming convention `dataset_id = ROFFTAG = runoff dataset directory name`. This is a human-facing convention, not a technical requirement imposed by the model. The generated Input Matrix remains specific to its target map even when two maps use the same `ROFFTAG`.

### Available Runoff Samples

The table below summarizes the sample locations and review state. The CSV is the full reference for product grids, file patterns, units, temporal meaning, model settings, provenance, and availability. Package examples describe v4.30; other releases may include different periods or files, so check actual coverage before selecting simulation dates.

| Package directory | Format and grid/time coverage | Unit evidence and relevant example |
| --- | --- | --- |
| `ELSE_GPCC/` | Global annual NetCDF runoff for 1979–2010. The inspected 2000 file has `runoff(time, latitude, longitude)`, float32 `mm day-1`, missing value `-999`, and a 180 × 360 grid. | Header inspection only; values and model ingestion have not been validated. This replaces the former Binary directory, not the Binary extraction interfaces. |
| `test-glb_1deg/` | Regenerable global 360 × 180 daily plain-binary sample (`Roff____YYYYMMDD.one`) for 2000-01-01 through 2001-12-31, extracted byte-for-byte from ELSE_GPCC. | `mm/day`, `IFRQ_INP=24`, `DROFUNIT=86400000`; scripts and metadata are tracked, generated data are ignored. See the sample README. |
| `test_1deg/` | Legacy package sample on the same global 1-degree grid and dates. The maintainer identifies it as a two-year extraction from ELSE_GPCC. | The `.ctl` declares runoff in `mm/day`. `gosh/test1-glb_15min.sh` uses `IFRQ_INP=24` and `DROFUNIT=86400000`. |
| `repo-mek_1deg_bin/` | Mekong 20 × 30 grid (90–110°E, 5–35°N); daily January–February 2000 data in two monthly Binary files. | Float32 `mm/day`, N-to-S, little-endian, missing value `-999`; `CROFFREQ=MON`, `IFRQ_INP=24`, `DROFUNIT=86400000`. Replaces the former long daily Binary collection. |
| `repo-mek_1deg/` | Mekong 20 × 30 daily NetCDF runoff for 1979–2010, one file per year (32 files, about 15.6 MiB). | Float32 `mm day-1`, longitude centers 90.5–109.5°E, descending latitude 34.5–5.5°N, missing value `-999`, CF daily bounds; `CROFFREQ=YEAR`. All regional values were checked against global NetCDF; this is extraction fidelity, not model/scientific validation. |
| `test_jpn_1hr/` | Original/source reference: daily binary files (`runoff_YYYYMMDD.bin`) plus `runoff.ctl`; Japan 1/60-degree grid (1500 × 1320), 1-hour records for 2007-09-03 through 2007-09-09. Locally available through an ignored symlink; large binaries are not tracked. | Maintainer-confirmed provenance: 1-arcmin simulations using the Today’s Japan system, provided by Yoshimura Laboratory. The maintainer identifies the original CTL `mm/day` label as erroneous and assesses the values as `mm/hour`, consistent with `gosh/test3-jpn_fcast.sh` (`IFRQ_INP=1`, `DROFUNIT=3600000`); this interpretation is not independently verified. |
| `repo-ERA5land-jpn_hourly/` | Planned Japan hourly NetCDF fixture: September 1–10, 2007, 120–150°E/20–50°N, ten daily files. | [Dataset specification](repo-ERA5land-jpn_hourly/README.md); no real download yet. Planned hourly CaMa-Flood input sample; GOSH integration remains future work. Size/license review required before data registration. KG-0019 remains open. |
| `ERA5land-jpn_legacy_bin/` | Preserved historical Binary CTL/report only; no maintained conversion workflow. | Binary conversion was retired; use the NetCDF workflow. These local historical files are Git-ignored. |
| `ERA5_land/daily/` | Canonical north-south geometry. The only observed local file, `ERA5-Land_Runoff_daily_19600101.bin`, is headerless float32 with 3,600 × 1,801 values (25,934,400 bytes). | Maintainer confirms the half-grid shift: input-grid limits 90.05 to −90.05 produce centers 90 to −90 under the map-tool convention. Units, missing-value meaning, longitude order, provenance, and long-term coverage are unconfirmed; not ready for a configured simulation. |
| `ERA5_land/Roff/` | Legacy 1981–2020 global daily binary series, 3,600 × 1,800 values per date. | The maintainer confirms the north-south half-grid shift is absent, so this is not the canonical daily geometry. Existing legacy input settings use 90/−90 limits (centers 89.95…−89.95). Metadata and scientific validity remain unverified; see `runoff_datasets.csv`. |

### Data Sources and Acquisition

Package-only data are not added by cloning the GitHub repository. Obtain the v4.30 distribution package or prepare equivalent inputs separately, then check the actual files against the selected run script. For source and acquisition details, see the [Copernicus ERA5-Land dataset page](https://cds.climate.copernicus.eu/datasets/reanalysis-era5-land) and the [ERA5-Land workflow guide](download_ERA5-Land/README.md). The [v5 execution guide](../gosh_test/README.md) describes current maintained runs; the listed package-only examples refer to v4.30 data, not an available v5 package. File spacing alone does not establish physical units or whether values are rates or accumulated depths; see [Choosing `DROFUNIT`](#choosing-drofunit).

## Preparing the Input Matrix

The runoff input grid and CaMa-Flood river map are separate grids. They may have different resolution, dimensions, and geographic extent. Use the runoff product's own regular latitude/longitude grid geometry to configure [the map-local `s03-generate_inpmat.sh` workflow](../map/tools/script_params/s03-generate_inpmat.sh). The workflow maps high-resolution map-pixel centers into runoff cells and accumulates overlap area for each map catchment. If the runoff grid does not cover part of the map, some catchments may have incomplete or no runoff coverage.

Configure the runoff-grid settings in the copied script, for example:

```sh
ROFFTAG="repo-mek_1deg"
GRSIZEIN=1.0
WESTIN=90.0
EASTIN=110.0
NORTHIN=35.0
SOUTHIN=5.0
OLAT="NtoS"
```

The example describes the `repo-mek_1deg` 1-degree Mekong grid. `GRSIZEIN` is the runoff-cell spacing in degrees; `WESTIN`, `EASTIN`, `NORTHIN`, and `SOUTHIN` are the grid edges. The generator derives dimensions from the edge spans and spacing, and treats cell centers as half a cell inward from each edge. `OLAT` must match stored row order: `NtoS` or `StoN`. It does not read runoff values or validate source coordinates. Generate the matrix only after the product has been converted to the same grid and ordering it will use at runtime.

Copy the workflow into the target map's `script_params/` directory, edit the settings, then run it there (or invoke the copied script by path). It writes `inpdim_<ROFFTAG>.txt` and `inpmat_<ROFFTAG>.bin` in the map root. Set `CINPMAT` in the simulation's `NFORCE` group to the map-root path for `inpmat_<ROFFTAG>.bin`. Keep the dataset's actual coordinates and longitude convention consistent between the forcing file and matrix; the model does not compare NetCDF coordinate values against the matrix.

The generated pair is linked: set `CDIMINFO` in `NDIMTIME` to `inpdim_<ROFFTAG>.txt` and `CINPMAT` in `NFORCE` to `inpmat_<ROFFTAG>.bin`. The descriptor supplies the map/input dimensions and geographic bounds used with the matrix. Both files are map-specific and must be regenerated for another target map. See the [Map Tools guide](../map/tools/README.md) and [parameter workflow guide](../map/tools/script_params/README.md) for build and map-local setup details. If you optionally add a registry row, check its CSV structure and grid arithmetic with the standard-library-only checker:

```sh
python3 inp/tools/validate_runoff_datasets.py
```

The checker does not require package data, CDS access, or NetCDF Python packages.

## Runoff forcing and units

The runoff field is water supplied per unit area over time. It may be stored as:

- **Accumulated depth per record**, for example millimetres accumulated during a 3-hour record (`mm/3 h`).
- **A depth rate**, for example millimetres per hour (`mm/h`) or metres per second (`m/s`).
- **A mass flux**, for example kilograms per square metre per second (`kg m-2 s-1`), which can be converted to water-depth rate using an assumed water density.

Runoff is not river discharge: discharge is a volume flow rate such as `m3/s`. In the forcing code, CaMa-Flood divides runoff values by `DROFUNIT` to obtain a depth rate in `m/s`, then multiplies by catchment area (or input-matrix area weights) to obtain `m3/s`. The model does not infer the runoff variable's physical units from its NetCDF `units` attribute; set the conversion from the actual data definition.

### Choosing `DROFUNIT`

Use the numerical divisor that converts one input value to `m/s`. For values in millimetres accumulated over each forcing record, convert millimetres to metres and divide by the duration of that record in seconds:

```text
DROFUNIT = 1000 × record_duration_seconds
runoff_m_per_s = input_runoff_value / DROFUNIT
```

For other units, derive the factor from the units themselves. These are illustrative examples, not an exhaustive product reference:

| Input value represents | Example `DROFUNIT` | Result after division |
| --- | ---: | --- |
| `m/s` | 1 | `m/s` |
| `mm/s` | 1,000 | `m/s` |
| `mm/h` rate, or `mm` accumulated over 1 hour | 3,600,000 | `m/s` |
| `mm/day` rate, or `mm` accumulated over 24 hours | 86,400,000 | `m/s` |
| `m/day` rate | 86,400 | `m/s` |
| `mm` accumulated over 3 hours | 10,800,000 | `m/s` |
| `mm` accumulated over 6 hours | 21,600,000 | `m/s` |
| `kg m-2 s-1` mass flux | 1,000 | `m/s`, assuming water density of 1,000 kg/m3 |

The file interval and the unit are separate facts. A daily file may contain an amount accumulated over one day, or a rate expressed per day. A 3-hourly record may contain a 3-hour amount, or a rate in `mm/day`. Those values need different interpretation even if their timestamps are 3 hours apart. Check the variable definition, units, time axis, and accumulation/reset semantics before choosing `DROFUNIT`. `IFRQ_INP` should describe the forcing update interval expected by the run configuration; file grouping (daily versus monthly files) does not by itself define either the runoff unit or time step.

For example, the standard daily `gosh/` samples use `DROFUNIT=86400000` for runoff values in `mm/day` (numerically also the same factor for a 24-hour accumulated depth in mm). The included ERA5-Land converters instead produce each-record accumulated depth in mm and write the time-step-specific factor to `runoff_info_CaMaFlood.txt`.

See the [map overview](../map/README.md) and [Map Tools parameter workflow guide](../map/tools/script_params/README.md) for map-specific requirements. The historical v4 programs under `map/src/` are separate from the v5 workflow described here.

## ERA5-Land source and conversion workflow

The ERA5-Land-specific [download and NetCDF conversion workflow](download_ERA5-Land/README.md) separates Shell settings/jobs from Python requests and conversion. `sample-global_2day.sh` and `sample-japan_hourly.sh` offer complete workflows with `--dry-run`; data and logs belong under dataset directories outside the tool directory. The planned `repo-ERA5land-jpn_hourly/` daily converted files and README are eligible for Git tracking after size/license review; original downloads and logs remain ignored. Binary conversion is retired. The separate `ERA5_land/Roff/` laboratory series is not regenerated by these scripts. The term ERA5-Land is deliberate; ERA5 atmospheric reanalysis is a separate product.

## Supported Input Formats and Simulation Settings

CaMa-Flood reads runoff from plain Binary or NetCDF. File format, file grouping, record interval, and runoff units are separate settings:

- `LINPCDF` selects Binary (`.FALSE.`) or NetCDF (`.TRUE.`).
- `CROFFREQ` is required and selects how records are grouped into files. `DAY`, `MON`, and `YEAR` are the standard, recommended modes; `SEQ` is an advanced option for a continuous file.
- `IFRQ_INP` sets the interval between forcing records in hours; the model derives `DTIN = IFRQ_INP × 3600` seconds.
- `DROFUNIT` converts stored runoff values to a depth rate in `m/s`. It does not select a file or interval.

### File grouping and names

| `CROFFREQ` | Records in each file begin at | Date inserted between `CROFPRE` and `CROFSUF` | Example |
| --- | --- | --- | --- |
| `DAY` | 00:00 of the calendar day | `YYYYMMDD` | `runoff_20000101.bin` |
| `MON` | 00:00 on the first day of the month | `YYYYMM` | `runoff_200001.nc` |
| `YEAR` | 00:00 on January 1 | `YYYY` | `runoff_2000.nc` |
| `SEQ` | The explicitly configured or CF-resolved start time | none | `runoff.bin` or `CROFCDF` |

`CROFFREQ` must be present in every v5 `NFORCE` group. `LINPDAY` was removed from v5; an old Namelist containing it is rejected with the Fortran Namelist error. Binary `SEQ` uses the fixed file `CROFDIR/CROFPRE+CROFSUF` and requires all four of `SYEARIN`, `SMONIN`, `SDAYIN`, and `SHOURIN` to identify its first record. NetCDF `SEQ` uses `CROFCDF` and keeps its CF-time or explicit-start behavior.

For `DAY`, `MON`, and `YEAR`, the filename identifies the calendar period and the first record is at 00:00 on that period's first day. Record indices use the model calendar and `DTIN`; a simulation starting partway through a period selects the matching record. `IFRQ_INP` must divide 24 hours exactly, and requested times must align with `DTIN`. Do not set `SYEARIN`, `SMONIN`, `SDAYIN`, or `SHOURIN` with these modes; arbitrary first-record offsets are not supported. The resolver uses normalized model time (`KMIN` converted by `MIN2DATE`) for filenames.

This v5 interface intentionally has one file-grouping setting: `CROFFREQ`. It is required, and the supported values are `DAY`, `MON`, `YEAR`, and `SEQ`.

### Plain Binary requirements

Each Binary record is headerless direct-access data containing one `NXIN × NYIN` field of 4-byte floating-point values. Longitude/x varies fastest. Latitude row order must match the `OLAT` used to generate the Input Matrix. `LINPEND=.FALSE.` reads native byte order; set it `.TRUE.` when the file uses the opposite byte order. The reader does not use CTL metadata to infer dimensions, coordinates, units, record count, or missing values.

For Binary `DAY`, `MON`, and `YEAR`, the date-tagged filename follows the table above and records are indexed from the model calendar. These modes always begin at 00:00 on the first day of the named period; explicit start-date fields are rejected. For `SEQ`, each record represents one `DTIN` interval in the fixed file, and all four `SYEARIN`, `SMONIN`, `SDAYIN`, and `SHOURIN` values define its first record. Binary has no calendar metadata, so the user must make its record dates consistent with `LLEAPYR`: Gregorian leap days when `.TRUE.`, or 365-day years when `.FALSE.`. The reader reuses each active file and closes it when changing periods or when forcing is finalized. With `LROSPLIT`, total and subsurface runoff remain separate Binary files with matching grouping and record indices, using `CROF*` and `CSUB*` settings respectively.

### NetCDF requirements and time validation

Build with NetCDF support (`UseCDF_CMF`) and set `LINPCDF=.TRUE.`. The selected numeric runoff variable must be three-dimensional with Fortran-interface shape `(NXIN, NYIN, time)`. Supplied examples use NetCDF dimension order `(time, latitude, longitude)`, with x/longitude varying fastest in each field; arbitrary dimension orders are not guaranteed. `CVNROF` selects runoff, and `CVNSUB` selects the optional subsurface variable when `LROSPLIT` is enabled. The model does not use runoff `units`, coordinate values, or `_FillValue` to convert/check the field against the Input Matrix.

For `DAY`, `MON`, and `YEAR`, the reader selects the date-tagged file and caches it until a period switch. Every opened grouped NetCDF file must provide `CVNTIME` as both the time dimension and a same-named one-dimensional CF coordinate variable; its first record or CF interval lower bound must begin at the file period boundary. The resolver checks the requested timestamp, time interval, calendar, increasing and evenly spaced records, coverage, supported units, and optional contiguous time bounds. Supported CF units are seconds, minutes, hours, or days `since` a reference date; supported calendars are `standard`, `gregorian`, `proleptic_gregorian`, `365_day`, and `noleap`, and must agree with `LLEAPYR`. Explicit start-date fields are not accepted with these standard grouped modes.

For NetCDF `SEQ`, set `CROFCDF` to the file containing the series. When `SYEARIN<=0`, omit `SMONIN`, `SDAYIN`, and `SHOURIN`; `CVNTIME` names the dimension and coordinate variable used to resolve the simulation start from CF metadata. When `SYEARIN>0`, provide all four date fields to specify the first-record time, and the existing elapsed-time record indexing is used. NetCDF `SEQ` keeps one file open for the run. NetCDF grouped files are opened and validated when first needed, cached while active, then closed on a file switch or at finalization.

`LWEVAP` behavior is not extended by this refactor. `CMF_FORCING_PUT` expects a third input-buffer field when it is enabled, while the current runoff reader only loads runoff and optional subsurface runoff; do not assume these runoff formats supply evaporation through this path. Verify the relevant coupled setup before enabling it.

### Runtime settings and examples

| Setting | Group | Role |
| --- | --- | --- |
| `CDIMINFO` | `NDIMTIME` | Path to `inpdim_<ROFFTAG>.txt`, the map and input-grid dimensions/bounds for the matrix. |
| `IFRQ_INP` | `NDIMTIME` | Runoff record interval in hours; independent of file grouping and units. |
| `LINPCDF` | `NFORCE` | `.FALSE.` selects Binary; `.TRUE.` selects NetCDF and requires a NetCDF-enabled executable. |
| `CROFFREQ` | `NFORCE` | Required: `DAY`, `MON`, `YEAR`, or advanced `SEQ`. |
| `DROFUNIT` | `NFORCE` | Divisor converting stored runoff to `m/s`; derive it from units and temporal meaning. |
| `CROFDIR`, `CROFPRE`, `CROFSUF` | `NFORCE` | Directory, prefix, and suffix for date-grouped Binary/NetCDF files; the grouping tag is inserted between prefix and suffix. Binary `SEQ` uses the same components without a tag. |
| `CROFCDF` | `NFORCE` | Single NetCDF file used by `SEQ`. |
| `CVNROF`, `CVNSUB` | `NFORCE` | NetCDF variable names for runoff and optional subsurface runoff. |
| `CVNTIME` | `NFORCE` | NetCDF time dimension name; auto-CF mode also requires a same-named coordinate variable. |
| `SYEARIN`, `SMONIN`, `SDAYIN`, `SHOURIN` | `NFORCE` | Use only with `SEQ`. All four are required for Binary `SEQ`; NetCDF `SEQ` uses CF time when `SYEARIN<=0`, or all four for an explicit first-record time. |
| `LINPEND` | `NFORCE` | Binary byte-order conversion; false means native order. |
| `LINTERP`, `CINPMAT` | `NFORCE` | Enable Input Matrix mapping and select `inpmat_<ROFFTAG>.bin`. |

`ROFFTAG` is a preprocessing-script setting used in matrix filenames; it is not a model Namelist parameter. For example, the recommended annual NetCDF configuration is:

```text
&NDIMTIME
  CDIMINFO = "/data/map/inpdim_my-runoff.txt"
  IFRQ_INP = 24
/
&NFORCE
  LINPCDF  = .TRUE.
  CROFFREQ = "YEAR"
  DROFUNIT = 86400000       ! mm per 24-hour record -> m/s
  CROFDIR  = "/data/my-runoff"
  CROFPRE  = "runoff"
  CROFSUF  = ".nc"
  CVNROF   = "runoff"
  CVNTIME  = "time"
  LINTERP  = .TRUE.
  CINPMAT  = "/data/map/inpmat_my-runoff.bin"
/
```

The legacy daily Binary convention remains valid:

```text
&NFORCE
  LINPCDF  = .FALSE.
  CROFFREQ = "DAY"
  LINPEND  = .FALSE.
  DROFUNIT = 86400000       ! mm per 24-hour record -> m/s
  CROFDIR  = "/data/my-runoff"
  CROFPRE  = "Roff____"
  CROFSUF  = ".one"
  LINTERP  = .TRUE.
  CINPMAT  = "/data/map/inpmat_my-runoff.bin"
/
```

Use one explicit `CROFFREQ` in every v5 configuration. For `SEQ`, users are responsible for preparing complete files whose first-record time and record alignment match the simulation. For every mode, compare requested dates and sample records with the source data, and check plausible runoff/discharge ranges.

The model converts NaN values to its internal `RMIS` sentinel (default `1.0e20`) and clamps negative runoff to zero. It does not generally interpret a CTL `undef` or NetCDF `_FillValue` as missing data. Convert missing source values explicitly to configured `RMIS` or to zero when zero runoff is intended; do not leave positive fill values such as `1.0e20` unless that value matches `RMIS`.

The temporal label and accumulation/reset interpretation must be checked against the dataset documentation. File grouping does not establish whether values are instantaneous rates or accumulated depths. For unit conversion, see [Runoff forcing and units](#runoff-forcing-and-units).

## Troubleshooting

| Symptom or risk | Check |
| --- | --- |
| Discharge is far too large or small | Confirm the input variable's units and whether it is an accumulated depth or a rate; derive `DROFUNIT` from those units and the record's temporal meaning. |
| Forcing records are skipped, repeated, or mis-timed | Compare `IFRQ_INP`, the NetCDF time coordinate or binary `.ctl` `tdef`, and the simulation dates. Daily/monthly file grouping is not the same as record spacing. |
| Some catchments have no or incomplete runoff mapping | Check that the runoff grid covers the intended map area and that the Input Matrix was generated for this exact map and runoff grid. |
| Spatial field is shifted or reversed | Check coordinate limits, longitude convention, grid-cell centers versus bounds, `OLAT`, and the order of latitude rows. |
| Model cannot find the forcing | Check `CROFDIR`, prefix, suffix, dates, and the chosen NetCDF or binary mode. |
| NetCDF run reads the wrong or no runoff variable | Confirm `CROFCDF`, `CVNROF`, and the variable in the actual file; NetCDF input requires a compatible build. |

These checks distinguish configuration mismatches from software defects; a suspicious result alone does not establish a code bug.

## Future development: generic runoff metadata analyzer

**TODO:** Develop a product-independent tool that inspects runoff files and produces a readable CaMa-Flood configuration summary. Where metadata permit, it should identify the grid, dimensions, spacing, bounds, longitude convention, row order, time interval, variable units, and temporal accumulation semantics; suggest `GRSIZEIN`, `WESTIN`, `EASTIN`, `NORTHIN`, `SOUTHIN`, `OLAT`, `IFRQ_INP`, and `DROFUNIT`; and warn when values cannot be inferred reliably. Users should be able to review and copy the summary into their preprocessing and run scripts.

`download_ERA5-Land/make_CMF_runoff_info.py` already generates related information for the ERA5-Land conversion workflow and inspects the converted NetCDF format. Its settings, assumptions, and call sites are part of that workflow; it is not established as a fully generic analyzer for arbitrary runoff products. The TODO is a future development direction only; no analyzer is implemented here.

## Related documentation

- [ERA5-Land download and conversion guide](download_ERA5-Land/README.md)
- [Map and Input Matrix overview](../map/README.md)
- [v5 Input Matrix generation workflow](../map/tools/script_params/s03-generate_inpmat.sh)
- [V5 execution guide](../gosh_test/README.md)
- [V5 forcing implementation](../src_main/cmf_ctrl_forcing_mod.F90)

## Regional extraction from global NetCDF

[`tools/extract_ELSE_GPCC.py`](tools/extract_ELSE_GPCC.py) generalizes the former Binary-window
extractor to annual global `ELSE_GPCC/runoffYYYY.nc` inputs. NumPy and netCDF4
are required (see the root requirements). Run from the repository root:

```sh
python3 inp/tools/extract_ELSE_GPCC.py --input-dir inp/ELSE_GPCC \
  --output-dir /tmp/mekong-runoff --west 90 --east 110 --south 5 --north 35 \
  --start-date 2000-01-01 --end-date 2000-02-29 --format binary --file-unit month
```

All shown arguments are required. `--format` accepts `binary` or `netcdf`;
`--file-unit` accepts `day`, `month`, or `year`. Dates are inclusive and may span
years. Grouping never averages daily values. Filenames are
`Roff____YYYYMMDD.one`, `Roff____YYYYMM.one`, `Roff____YYYY.one` for Binary,
or `runoffYYYYMMDD.nc`, `runoffYYYYMM.nc`, `runoffYYYY.nc` for NetCDF;
use the corresponding Reader grouping `DAY`, `MON`, or `YEAR`.

Monthly/yearly files retain the entire calendar group's daily slots. For a
partial group, dates outside the requested interval are filled with the source
missing value, never with zero or unrequested source data. This keeps record 1
at the calendar period start as the Reader requires. Run simulations only within
the requested interval; padded dates are not valid forcing. NetCDF records have
midday CF time coordinates and midnight-to-midnight bounds, using a Gregorian
calendar. Binary records are little-endian float32, longitude fastest and rows
north-to-south. Configure the compiler/runtime to read little-endian files on
other architectures. NetCDF uses lossless deflate level 3 and shuffle; runoff
units and missing values are preserved.

Bounds specify **cell edges**, not center coordinates; all edges must align
with the regular source grid, otherwise extraction fails without rounding or
interpolation. Both -180–180 and 0–360 source longitude axes are supported.
For a dateline-crossing region, give east greater than west on an unwrapped
branch, for example `--west 170 --east 190`. Output longitudes use that branch
and increase eastward; latitude always decreases north-to-south. Source daily
CF time bounds and unpacked float32 runoff are checked. Missing dates, changed
grids between years, unsupported calendars and existing output filenames are
errors. Completed files are published without overwriting; inputs are read-only.
Only a regional daily slice is loaded at once. If a later group fails, earlier
completed groups remain; inspect them before retrying.

`ELSE_GPCC/` is optional global additional data, ignored by Git. In contrast,
`repo-mek_1deg_bin/` is the small Git-tracked mek01 fixture. The former Binary
collection's extraction scripts have been replaced by this shared CLI; historical
Binary-to-NetCDF regeneration workflows may require separate integration work.

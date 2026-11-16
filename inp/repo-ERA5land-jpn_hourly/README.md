# ERA5-Land Japan hourly repository sample

**Status: ten converted files exist and are Git-tracked; format metadata inspected.
Scientific time attribution and model integration remain unvalidated.**

This dataset is an example of the ERA5-Land download/NetCDF conversion
workflow and an hourly CaMa-Flood runoff input fixture. GOSH
integration and input-matrix preparation remain future work. This is not
yet a validated GOSH input.

## Specification and layout

| Item | Requested specification |
| --- | --- |
| Product Shell | [`sample-japan_hourly.sh`](../download_ERA5-Land/sample-japan_hourly.sh) |
| Dataset | `repo-ERA5land-jpn_hourly` |
| Period | 2007-09-01 through 2007-09-10, inclusive |
| Requested area | 120–150°E, 20–50°N |
| Resolution | ERA5-Land standard 0.1 degree |
| Time resolution | 1 hour; no daily averaging or aggregation |
| Download/output grouping | daily/daily |
| Expected converted files | 10 files, each with 24 hourly records |
| Storage | NetCDF-4, float32, deflate level 3, shuffle |

```text
repo-ERA5land-jpn_hourly/
├── README.md
├── original/ERA5-Land_runoff_20070901.nc ... ERA5-Land_runoff_20070910.nc
├── runoff_20070901.nc ... runoff_20070910.nc
├── runoff_info_CaMaFlood.txt
└── logs/
```

Ten converted files total 17,229,869 bytes (about 16.43 MiB). Header/time/coordinate
inspection confirms 24 hourly records per file, a 301 × 301 grid with longitude
centers 120..150 and latitude 50..20, float32 `runoff(time,lat,lon)`, units `mm`,
fill `1e20`, deflate=3 and shuffle. Derived edges are 119.95..150.05 and
19.95..50.05 degrees. Raw files exist locally but remain ignored. These checks
do not verify runoff values or model ingestion.

## Execution

With the repository's Python dependencies installed, inspect the ten requests:

```sh
bash inp/download_ERA5-Land/sample-japan_hourly.sh --dry-run
```

After reviewing the requests and configuring CDS access, omit `--dry-run` to
retrieve and convert. The Product Shell passes the same explicit configuration
to s01 and s02. Defaults are `NCPUS=2` and `PYTHON_CMD="python3"`; use explicit
`--ncpus`/`--python` overrides as needed. Existing files are skipped unless
`--overwrite` is supplied. Outputs and logs remain in this dataset directory,
not in the tool directory. See the [workflow guide](../download_ERA5-Land/README.md).

Daily conversion requires every expected hour exactly once, from 00 to 23 UTC;
it rejects missing/duplicate timestamps and does not invent replacement records.
Accumulation differencing, reset/negative handling, missing values, conversion
from metres to timestep millimetres, and timestamp labels retain the existing
converter behavior. Output is `runoff(time, lat, lon)`, units `mm` per hourly
record, with missing value `1e20`. The intended model conversion is
`IFRQ_INP=1`, `DROFUNIT=3600000`, and `CROFFREQ="DAY"`, subject to later integration.

**Scientific limit:** [KG-0019](../../research/records/knowledge_gaps/KG-0019.md)
leaves the physical attribution of 00 UTC accumulations and period boundaries
unresolved. Exactly 24 records per day proves structural completeness, not
correct physical interval attribution. Splitting or joining files does not
resolve this issue.

## Source, redistribution and Git policy

Source: ECMWF / Copernicus Climate Change Service (C3S),
[ERA5-Land hourly data](https://cds.climate.copernicus.eu/datasets/reanalysis-era5-land),
[DOI:10.24381/cds.e2161bac](https://doi.org/10.24381/cds.e2161bac).
The [official CDS catalogue metadata](https://cds.climate.copernicus.eu/api/catalogue/v1/collections/reanalysis-era5-land)
was checked on 2026-11-15 and identifies **CC-BY-4.0** (licence `cc-by`, revision 1).
[CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) permits sharing and
adaptation with attribution, a licence link and identification of changes;
retain supplied notices and do not imply provider endorsement.

Before publishing actual files, retain the applicable download-time licence
and notices, record the retrieval date/source edition, include ECMWF/C3S and
Copernicus attribution and the dataset DOI, and describe regional extraction,
accumulation conversion, unit conversion and layout changes. This README
records the previously checked source terms; download-specific notices still
need review before publication. This task does not clear particular files for
redistribution.

The README and `runoff_YYYYMMDD.nc` are eligible for Git tracking. Original CDS
files, logs and the generated information file remain ignored. **Do not git add
or push generated data until their actual sizes, attribution/licence metadata
and validation results have been reviewed.** The measured sizes and header
checks above are limited evidence, not scientific validation. The converted files were already tracked before this task.

## Required real-data checks

Before model integration/publication, verify 240 distinct hourly labels,
source/output coordinate consistency, units, masks, negative/reset behavior,
float32 layout and compression, and the first/last records at each daily boundary.
Retain the measured file sizes and establish download-specific attribution
before publication. A separate scientific review must address KG-0019; a later integration task must supply the
matching input matrix and validate the GOSH/model reader. The current offline
checks use only tiny synthetic fields.

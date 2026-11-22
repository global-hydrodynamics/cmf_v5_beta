# ERA5-Land Hourly Runoff Preparation — Survey Report

## Summary

ERA5-Land hourly runoff has been selected by the researcher as an input for a
future CaMa-Flood event simulation. The hourly product provides time-varying
runoff input around the July 2021 flood, while its physical accumulation and
time attribution must be interpreted under the existing ERA5-Land workflow
and KG-0019. This report concerns data preparation only; it is not a simulation
or model evaluation.

The Product Shell requests **2021-07-01 through 2021-07-20**, an inclusive
period that starts before the event to provide a preparation interval. This is
distinct from (1) the Step 1 core event context, 2021-07-13 to 2021-07-15,
(2) the initial candidate analysis window, 2021-07-10 to 2021-07-25, and
(3) the still-undecided simulation and evaluation period. July 1 does not by
itself establish sufficient model spin-up. Evaluation after July 20 will need
additional forcing dates.

The regional map outer bounds are 3–13°E and 45–53°N. The researcher-selected
CDS request extends 0.5° beyond each edge: 2.5–13.5°E, 44.5–53.5°N. Inspection
of the returned files confirms 0.1° grid centers at longitudes 2.5–13.5°E and
latitudes 53.5–44.5°N, ordered north to south. The corresponding cell-edge
bounds are 2.45–13.55°E, 44.45–53.55°N. The requested area, cell centers and
cell edges are different spatial descriptions and should not be conflated.

## Existing dataset inspection

The local output directory already contains 20 original daily files and 20
converted daily files for every date from July 1 through July 20. Retained
download and conversion logs contain a success/output record for each date.
No new download or conversion was run for this task.

Each converted file contains 24 hourly records with dimensions
`runoff(time,lat,lon) = (24,91,111)`. The raw and converted daily files contain a continuous
480-record sequence labeled 2021-07-01 00:00 UTC through 2021-07-20 23:00 UTC,
with no duplicate or missing hourly labels. The variable is float32 `runoff`,
units `mm`, with `_FillValue` and `missing_value` of `1e20`. Across the
converted files the observed range is 0 to about 71.43 mm per hourly record;
16,392 values per day are masked. These checks describe the stored data, not
the hydrological correctness of the conversion.

The raw ERA5-Land files contain source variable `ro` in metres. The shared
converter differences accumulated values and writes millimetres accumulated
over each input timestep. Daily download/output units describe file grouping;
they do not average the hourly records. The generated information file reports
`IFRQ_INP=1`, `DROFUNIT=3600000`, `CROFFREQ=DAY`, `CVNTIME=time`, and
`CVNROF=runoff`. Step 13 should check these against its actual namelist and
forcing configuration.

## Relation to the Rhine map

Step 11's regional map includes `diminfo_ERA5land_global.txt` and
`inpmat_ERA5land_global.bin`. The map-specific mapping is based on a 0.1°
global ERA5-Land grid (3600 × 1801 centers, longitude increasing and latitude
decreasing). The downloaded regional subset uses the same 0.1° center lattice
and north-to-south latitude order. The existing matrix is therefore the
relevant mapping candidate and was not regenerated. Coordinate compatibility
does not prove every map cell is adequately represented by the matrix, and no
model input or simulation check was performed.

Because this dataset is specific to one event and remains local/ignored, it
was not added to the shared `inp/runoff_datasets.csv` registry. The reusable
Product Shell and shared workflow remain the reproducible acquisition and
conversion method.

## Scientific limitations and next action

KG-0019 remains unresolved. ERA5-Land's valid-time label at 00 UTC corresponds
to the preceding 24-hour accumulation according to the maintained scientific
record. The converter's within-day differencing and treatment of the first
record do not establish complete temporal attribution or correct interval
coverage at the beginning/end of the requested dates. No timestamp shift or
algorithm change was made.

Use the converted files as Step 13 forcing candidates, not the raw source
files. Before simulation, choose the simulation period and spin-up, ensure
forcing covers all run/evaluation dates, and verify actual input settings and
map matrix pairing. Any claim about event performance must wait for a completed
model run and observation matching.

See the machine-readable [Step 12 metadata](../metadata/12_era5land_runoff.json),
the [Step 12 Prompt](../p12-era5land_runoff_preparation.md),
and the [event process](../00_event_evaluation_process.md).

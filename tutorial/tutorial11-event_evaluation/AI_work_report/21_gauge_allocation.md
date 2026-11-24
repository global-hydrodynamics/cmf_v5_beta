# Step 21 — Gauge Allocation Work Report

## Inputs

- `observation/stations_data/allstations.csv`
- `metadata/02_gauges.csv`
- `metadata/04_discharge_inventory.csv` and Step 4 unit/provenance notes
- `metadata/14_simulation_setup.json`
- `map/Rhine_15min/params.txt` and `netcdf/{lonlat,uparea,nextxy}.nc`
- `map/Rhine_15min/netcdf/rivwth_merit.nc` and `basin.nc`
- `metadata/01_impact_locations.csv` and
  `metadata/01_reported_flood_timing.csv`
- `map/data/GRDC_allocated.csv` and `map/Rhine_15min/GRDC_alloc.txt`

## Method and execution

Ran `bash s21-gauge_allocation.sh` and `bash f21-gauge_allocation.sh` from the
Tutorial directory using its `.venv` Python environment. The processing code
checked the `Cama15row/col` values against their global 0.25° grid-center
coordinates, matched those centers to the current regional axes, and verified
the current `outlon/outlat` and `uparea` values. `outlon/outlat` are NetCDF
variables with dimensions `(lat, lon)`, units `degrees_east` / `degrees_north`,
and fill value −9999. They describe unit-catchment outlets. `uparea` has
dimensions `(lat, lon)`, units m², and fill value −9999. `nextx/nexty` use
one-based downstream grid indices; the emitted table uses zero-based Python
row/column indices.

The source `Cama15row/col` candidates are zero-based global `glb_15min`
indices, north-first rows and west-first columns. The current map begins at
global row 148, column 732, so the three local cells are Lobith `(4, 12)`,
Speyer `(15, 21)` and Maxau `(16, 21)`. The source `Cama15lon/lat` values
match the cell centers; the plotted model locations instead use the actual
unit-catchment outlet variables.

The matching records in `GRDC_allocated.csv` identify GRDC stations 6435060
(Lobith), 6335170 (Speyer) and 6335200 (Maxau). Their `GRDC_alloc.txt`
`ix1/iy1` values, converted from one-based to zero-based, agree with all three
selected current-map cells. Following `nextxy` from Maxau visits Speyer and
then Lobith before the river-mouth endpoint.

The CSV `ProvArea` field has no declared unit. The Step 4 dataset metadata
records area units as unknown. `Cama15area` also has no declared unit, but each
value matches current map `uparea` in km² after the map's declared m² unit is
converted. Area ratios and percent errors are therefore explicitly marked
conditional on `ProvArea` being km²; this interpretation is supported by the
GRDC source conventions and values but is not an explicit source declaration.
Gauge-to-outlet distances use a spherical great-circle calculation with mean
Earth radius 6371.0088 km.

For impact locations, the script reads all 22 report/timing rows. It assigns
coordinates to cells by containment in the map's outer-edge bounds
(3–13°E, 45–53°N): `col=floor((lon-west)/0.25)` and
`row=floor((north-lat)/0.25)`, consistent with the eastward longitude and
north-first latitude arrays. It does not search for or snap to the nearest
outlet. Cell centers, outlet coordinates, map `uparea` converted from m² to
km², straight-line point-to-outlet distance, model `basin` label and cell
river width are recorded. `nextxy` destination cell center is included in the
notes when valid. The `basin` value is treated as a routing label, not as a
natural-basin name.

The scientific review then compared the regional 1-minute `catmxy` assignment
at each coordinate with outlet positions, `uparea`, `rivwth` and `nextxy`.
External gauge basin information was used where available. This is evidence
from the map product, not independent verification of named-river geometry.
The CSV retains the geographic containing-cell fields and adds distinct
`river_model_*` candidates plus `river_allocation_status` and
`river_allocation_reason`. Reviewed status counts are 2 `confirmed`, 14
`plausible`, 1 `unresolved`, 4 `not_represented`, and 1 coordinate-missing
record. For example, Kordel's river candidate is (11,14), with 819.9 km²
uparea versus the official 819 km² basin; the geographic cell (12,14) is a
large downstream routing cell. The Erft Bliesheim candidate has 630.3 km²,
close to the Erftverband's 604.17 km² station catchment. Ahr sites at Bad
Neuenahr and Bad Bodendorf map to a mixed confluence/mainstem cell rather than
a distinct Ahr cell; Prümzurlay likewise has no separate local candidate.
Details and rationale are recorded per report row.

## Outputs and checks

- `metadata/21_gauge_allocation.csv` — three station records and Step 22 cell
  indices.
- `metadata/21_impact_location_allocation.csv` — 22 report-linked rows, 21
  spatially assigned coordinates and one coordinate-missing report.
- `figure/f21-gauge_allocation.png` — full-map context plus two impact-region
  views; containing-cell outlets and reviewed river-assessment candidates have
  distinct symbols.
- `AI_survey_report/21_gauge_allocation.md` — results and scientific limits.

Focused checks passed: the three source gauge cells are in-bounds and have
valid outlets/upstream areas; the ECMWF candidate areas match the current map's
uparea conversions; the GRDC allocation cells match; and the downstream chain
is Maxau → Speyer → Lobith. The impact CSV preserves all 22 report IDs, assigns
the 21 available coordinate records by cell containment, and marks the
coordinate-missing Eupen record without inference. All candidate cells were
checked against current map dimensions and valid outlet/uparea/channel-width
values. The updated Figure was
rendered and visually inspected for network position, marker distinction,
connectors, label legibility and regional context. No model output was read,
and impact-flow extraction, Step 22 re-extraction or performance evaluation
was not run. The Figure visibly distinguishes geographic cell outlets (dark
squares) from river-assessment candidates (magenta diamonds).

## Handoff

For local-river timing comparisons, use the separate `river_model_row_0based`
and `river_model_col_0based` where the status is `confirmed` or `plausible`,
and preserve the containing-cell indices as geographic context. Do not treat
`unresolved` or `not_represented` as local-tributary discharge. The three
gauge-only rows in `21_gauge_allocation.csv` remain the Step 22 handoff. Keep
discharge units, time zone and conditional `ProvArea` units visible in later
comparisons.

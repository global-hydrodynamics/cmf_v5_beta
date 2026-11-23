# Step 21 — Gauge and Flood Impact Location Allocation

## Finding

The ECMWF `Cama15row/col` candidates resolve to valid cells in the current
40 × 32 `Rhine_15min` map after converting the zero-based global `glb_15min`
indices to the regional map. All three cells agree with the corresponding
station entries in the current map's `GRDC_alloc.txt` allocation output. The
current `nextxy.nc` network traces downstream through **Maxau → Speyer →
Lobith**.

| Station | Observed lon/lat | Current map outlet lon/lat | Distance | Reported area (source value) | Map uparea | Conditional area error* |
|---|---|---|---:|---:|---:|---:|
| Lobith (153) | 6.10833, 51.84444 | 5.98375, 51.86292 | 8.8 km | 160,800 | 159,285.6 km² | −0.94% |
| Speyer (63) | 8.44876, 49.32379 | 8.41208, 49.24958 | 8.7 km | 53,131 | 52,103.7 km² | −1.93% |
| Maxau (28) | 8.30561, 49.03896 | 8.36875, 49.16875 | 15.1 km | 50,196 | 50,808.3 km² | +1.22% |

*`ProvArea` has no unit declaration in the source. The percentages are shown
conditionally using km², consistent with the GRDC allocation conventions and
the supplied Cama15 values matching the current map's `uparea` after m²-to-km²
conversion. They are not an independently confirmed unit comparison. Raw
source values and the conditional basis are retained in
[`metadata/21_gauge_allocation.csv`](../metadata/21_gauge_allocation.csv).

## Gauge allocation

The three discharge-gauge allocations are unchanged and remain the handoff for
Step 22. The gauge details and their unit caveat are retained in
[`metadata/21_gauge_allocation.csv`](../metadata/21_gauge_allocation.csv).

## Reported impact locations

The Step 01 timing/location ledger contains 22 report records: 14 locality
impact records and eight detailed hydrologic/context records. Seven detailed
records have their own coordinates; the Eupen reservoir-outlet record has no
verified coordinates. The 14 locality records use the existing approximate
town coordinates, while coordinate-bearing detailed reports retain their own
site coordinates. Records are linked to Step 01 by both `report_id` and
`location_id`.

Of 22 records, **21 were assigned to the geographic model cell containing the
recorded coordinate**, and one Eupen report remains unallocated because no
coordinates are present. No location was outside the map. The 21 coordinates
fall in 11 distinct 0.25-degree cells. Each assigned cell has a valid mapped
channel outlet, but that does not establish that it is the reported impact
reach. The detailed assignments and source coordinates are in
[`metadata/21_impact_location_allocation.csv`](../metadata/21_impact_location_allocation.csv).

River correspondence is therefore recorded separately from cell assignment:

- 7 records have a nearby outlet and a *plausible but unverified* local-network
  correspondence.
- 9 records are marked uncertain because the cell outlet separation and coarse
  grid do not establish the named reach.
- 5 Ahr / Erft-Swist records are flagged because their containing cells have
  very large mapped upstream areas (about 140,000–145,000 km² for the mapped
  Bad Neuenahr/Sinzig/Blessem cells). These may represent a major routing
  channel rather than the named local tributary.
- 1 record (Eupen reservoir outlet) lacks coordinates and was not assigned.

The map's 0.25-degree grid is too coarse to guarantee local Ahr, Erft, Vesdre,
Kyll or Geul reach identity. The `model_basin_id` is a model routing label, not
a direct natural-watershed classification. Outlet positions are model
unit-catchment outlets, not the impact locations themselves. The point
coordinates for towns are approximate locality representatives; they are not
surveyed flood boundaries. Use these allocations as spatial extraction
candidates, not as evidence that a particular modeled reach experienced the
reported impact. Later discharge or inundation peak comparisons must retain
these location and river-match limitations.

## Figure and interpretation

![Figure 21 — Gauge and flood impact location allocation](../figure/f21-gauge_allocation.png)

*Figure 21. Orange circles and blue squares show the three discharge gauges
and their allocated outlets. Colored circles show reported impact localities;
triangles show separately georeferenced Step 01 report sites; dark squares
show outlets of the containing impact-location cells. Dotted connectors are
straight-line coordinate-to-outlet distances, not river paths. The two local
views separate the western Meuse/Vesdre groups from the Ahr/Erft/Kyll/Prüm
cluster. Detailed-site names remain traceable in the CSV to keep the dense
local labels readable.*

The checked candidates are suitable as the Step 22 spatial handoff: each has a
current-map index, valid outlet coordinates and close correspondence to the
available GRDC map allocation. The outlet-to-gauge distances of 8.7–15.1 km
remain material spatial offsets; Step 22 should retain these offsets in its
interpretation rather than describing the outlet as the gauge location.

The model upstream areas closely match the supplied reported-area values under
the conditional km² interpretation. Since the source does not explicitly
declare units, the area ratios are supporting evidence rather than a fully
resolved unit validation. The discharge values' units and time-zone semantics
also remain open from Step 4. No model-flow extraction or flow-performance
comparison was performed here.

## Gauge allocation decision

Retain the existing ECMWF candidate cells for all three stations. In
`metadata/21_gauge_allocation.csv`, `model_row_0based` and
`model_col_0based` are the indices to use for the current map's `[lat, lon]`
arrays and the Step 14 `outflw(time, lat, lon)` output. The source's raw global
indices are recorded separately. The current GRDC output independently agrees
with the same local cells.

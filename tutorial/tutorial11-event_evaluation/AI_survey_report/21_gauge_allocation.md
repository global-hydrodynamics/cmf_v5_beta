# Step 21 — Gauge and Flood Impact Location Allocation

## Catchment-based scientific review — 2026-11-24

The restored Rhine map was inspected and the high-resolution allocation was
executed on this workstation. All **22 report records** remain: **21 have valid
catmxy assignments, 11 change model cell**, and the coordinate-missing Eupen
outlet report remains unassigned. The 14 locality records and eight detailed
reports retain their IDs and individual rows. Old geographic columns and notes
are retained; the three-gauge CSV is byte-identical to its pre-review version.

The 600 × 480 one-minute grid covers 3–13°E, 45–53°N. A location selects its
containing one-minute pixel; the pixel's two int16 values identify the
one-based x/y of its **unit-catchment model cell**. They do not identify the
15-minute rectangle containing the location. No nearest-channel snapping or
coordinate substitution was used.

| Locality | Old (row,col), area km² | catmxy (row,col), area km² | Interpretation |
|---|---|---|---|
| Schuld | (10,15), 680.265 | (10,15), 680.265 | Unchanged candidate; downstream goes directly to (9,17). |
| Altenahr | (9,15), 630.277 | (9,17), 140,560.780 | Old cell belongs to the same model path as upper Erft sites. New assignment shares the large-channel cell with lower-Ahr reports; independent local Ahr routing remains unresolved. |
| Bad Neuenahr-Ahrweiler | (9,16), 140,777.669 | (9,17), 140,560.780 | Changes to an upstream cell on the same large-area path, not a separately resolved small tributary. |
| Blessem | (8,15), 144,251.306 | (8,14), 1,450.238 | Moves from the large-area path to the Erft-side candidate draining upper Erft sites. Plausible, not independently confirmed. |

### River connection evidence

All 21 assigned point paths terminate at stored nextxy=(-9,-9), have no cycle,
and have no decrease in mapped upstream area. This establishes selected map
connectivity consistency, not independent river-name or flood-wave validation.
The retained JSON contains full paths and outlet coordinates.

- **Ahr:** Schuld/Müsch (10,15; 680 km²) → (9,17; 140,561 km²) →
  (9,16; 140,778 km²). Altenahr, Bad Neuenahr, Sinzig, Pegel Altenahr and
  Bad Bodendorf all map to (9,17). Their upstream/downstream local ordering
  cannot be resolved inside one model cell. The increase in area does not
  establish correct Ahr reach representation. The lower-Ahr channel is not
  independently resolved by these assignments; named-reach status remains
  `unresolved`, rather than asserting the physical tributary is absent globally.
- **Erft:** Bad Münstereifel, Euskirchen and detailed Bliesheim map to
  (9,15; 630 km²) → Blessem (8,14; 1,450 km²) →
  (7,14; 147,646 km²). This supports a tributary-side Blessem candidate and
  explains why the old (8,15) large-channel assignment was misleading.
- **Kyll:** Kordel changes from (12,14; large receiving channel) to
  (11,14; 819.941 km²), then drains to (12,14; 25,093 km²).
- **Prüm:** Prümzurlay changes to (11,13; 580.627 km²), then
  (12,13; 4,222 km²) → (13,14; 23,811 km²) → (12,14).
  The Kyll/Prüm candidates are separate tributary branches before their shared
  receiving path. No intervening named-river identity is inferred from area.
- **Vesdre:** Verviers (9,12; 351 km²) → Pepinster (9,11; 699 km²)
  → (9,10; 20,644 km²), consistent with the retained point order.

There are **16 plausible** and **6 unresolved** records (five lower-Ahr reports
and the coordinate-missing Eupen report); none are promoted to confirmed.
Plausible means map-consistent candidate with coordinate/river uncertainty,
not an independently established river identity. Town-center coordinates and
one-minute resolution can select a nearby hillslope unit catchment, which
remains a limitation even when indices and topology are consistent.

### Catchment Figure

![Ahr–Erft catchments and old/new outlets](../figure/f21-catchment_allocation.png)

Discrete pastel regions and fine boundaries show one-minute unit-catchment
assignments, not 15-minute rectangles. Dotted geographic grid lines are only
context. Gray pixels are unassigned land; other NoData/background is white.
Blue outlet-to-outlet links and arrows use standard nextxy. Orange
open squares/dotted connectors show old geographic outlets; teal diamonds/solid
connectors show catmxy outlets. Coincident symbols indicate unchanged outlets.
Blessem moves to a separate western outlet; the lower-Ahr reports converge on
one large-area outlet. Straight point connectors are assignment guides, not
mapped river courses. The original regional Figure remains below.

### Step 23 handoff and remaining questions

Prefer the assigned `catmxy_row_0based`/`catmxy_col_0based` candidates for future
impact-location extraction. Retain each report separately even when model cells
coincide; duplicated model series must not be interpreted as independent local
river signals. Carry `river_allocation_status/reason`, coordinate confidence,
and old/new differences into that work. Keep Eupen unassigned. The lower-Ahr
river representation and approximate town-coordinate meaning remain unresolved;
matching a reported flood wave requires later evidence. No Step 23 extraction,
peak-time comparison, simulation, map modification or Gallery publication was
performed. Existing observation-unit/timezone and forcing-time caveats remain.

## Retained geographic and gauge review

The following findings describe the earlier geographic assignment, preserved
for comparison; they are not the new catmxy results.

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

# p21 — Gauge Allocation

## Workflow Summary

**Inputs**

- The selected gauge inventory and provider station table.
- `metadata/01_impact_locations.csv` and
  `metadata/01_reported_flood_timing.csv` for reported impacts and detailed
  report locations.
- The current event-specific CaMa-Flood map used by the simulation.
- Existing allocation products, where available.

**Tasks**

- Verify source row/column conventions and map grid coordinates.
- Resolve each candidate to a current-map cell and use its unit-catchment
  outlet coordinates, upstream area and downstream connection.
- Compare the observation and outlet locations, areas and network order.
- Assign each georeferenced impact report to its containing map cell; assess
  named-river correspondence separately, without snapping to a nearby outlet.
- For tributary assessments, inspect the regional 1-minute `catmxy` assignment,
  coarse-map outlet, `uparea`, `rivwth` and `nextxy`; keep a river assessment
  candidate separate from the geographic containing cell.
- Save separate machine-readable gauge and impact-location handoffs and a map.

**Outputs**

- `metadata/21_gauge_allocation.csv`
- `metadata/21_impact_location_allocation.csv`
- `figure/f21-gauge_allocation.png`
- Step 21 Survey and Work Reports

## Human Instructions

Adapt the station source, selected-station inventory and current map paths for
the event. Run the allocation check and then render its Figure:

```sh
bash s21-gauge_allocation.sh
bash f21-gauge_allocation.sh
```

The processing script verifies the supplied gauge candidates against the
current map and relevant existing allocation outputs. For impact reports, it
uses the recorded geographic coordinate to identify the containing model cell;
it does not replace that cell with the nearest outlet. It records the outlet,
upstream area and outlet distance. A separate `river_model_*` candidate is
written only where the reviewed regional `catmxy` association, outlet
position, upstream area, channel width, topology and external river/gauge
evidence support a candidate. `river_allocation_status` is `confirmed`,
`plausible`, `unresolved`, or `not_represented`. The 1-minute `catmxy`
association is regional map evidence, not independent ground truth for the
named river. Reports without coordinates remain in the CSV without an
inferred location. All row/column fields are zero-based Python array indices,
with row following the map's north-first latitude array.

Where a river-assessment cell is supported, retain it in separate
`river_model_row_0based` / `river_model_col_0based` and `river_model_*` outlet
fields, with a `river_allocation_status` (`confirmed`, `plausible`,
`unresolved`, or `not_represented`) and a reason. `catmxy` association is
model-map evidence rather than independent proof of river identity. Use a
containing-cell series only as regional context when no local channel is
represented; never label it local tributary flow.

## Example AI Agent Prompt

```text
Complete the gauge and reported-impact location allocation for this flood-event tutorial.
Inspect the repository and Tutorial instructions, the current simulation map,
the selected gauge inventory and the original station metadata. Treat the
current map used by the experiment as authoritative; do not assume an older
map's allocation remains valid.

For each selected gauge, establish the source row/column convention and map
grid alignment before indexing. Inspect the current map's outlet longitude and
latitude, upstream drainage area and nextxy network. Compare the supplied
candidate and any available existing allocation product with the current-map
cell. Measure station-to-outlet distance, check drainage-area correspondence
with explicit units, and verify relevant downstream station ordering by
following nextxy. Use unit-catchment outlet coordinates for model locations,
not grid centers. Do not optimize allocations using model-observation flow
agreement or replace a candidate by simple nearest-cell search.

Create a reusable processing shell/Python pair and a CSV containing the
observation coordinates, original candidate fields, current map's zero-based
row/column, outlet coordinates, map upstream area, distance, area comparison,
allocation comparison and evidence-based decision. If an area unit is not
declared, preserve the source value and leave any derived comparison clearly
conditional or unavailable. Generate a Figure with the current map's river
network, observation gauges, selected outlets and connectors; add local views
if the full-map view cannot show their separation. Also read every Step 01
impact/timing report, retaining `report_id` and `location_id`, and allocate
each georeferenced coordinate to its containing current-map cell. Keep the
geographic cell assignment distinct from the map outlet and from whether that
outlet represents the named river. Do not snap small-tributary locations to a
nearby mainstem. For priority tributaries, inspect regional 1-minute `catmxy`
assignments and the candidate coarse cell's outlet, upstream area, river width
and `nextxy` continuity alongside independent source-backed gauge or river
evidence. `catmxy` is not ground truth. Add separate `river_model_*` fields
only for supported candidate cells and record `river_allocation_status` and a
reason. Keep unsupported locations as `not_represented` or `unresolved`.
Retain records with missing or out-of-map coordinates and explain their status.
Write these results to a separate
`metadata/21_impact_location_allocation.csv`; do not mix them into the
gauge-only `metadata/21_gauge_allocation.csv`, which remains the Step 22 gauge
handoff. Update the Figure to distinguish gauges, impact localities, detailed
sites and model outlets, and use local views where labels would otherwise
overlap. Create a researcher-facing Survey Report and technical Work Report,
and update the Tutorial process and development log. Do not modify model/map/
source-observation data, extract model flows, calculate performance metrics,
or publish a Gallery item. Human review is recommended but is not a script
execution gate.
```

## Expected Handoff and Review

The gauge CSV is the machine-readable handoff for later discharge extraction.
The impact CSV preserves report-linked geographic cells and model outlets for
later impact-location extraction. A reviewer can compare source coordinates,
grid indices, outlet location, map topology and Figure. Human review is
recommended, but does not gate processing. Do not treat a spatial assignment
as a validated river match or discharge comparison; tributary representation,
time conventions and discharge units may remain unresolved.

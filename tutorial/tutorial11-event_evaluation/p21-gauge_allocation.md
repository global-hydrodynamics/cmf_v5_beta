# p21 — Gauge Allocation

## Workflow Summary

**Inputs**

- The selected gauge inventory and provider station table.
- The current event-specific CaMa-Flood map used by the simulation.
- Existing allocation products, where available.

**Tasks**

- Verify source row/column conventions and map grid coordinates.
- Resolve each candidate to a current-map cell and use its unit-catchment
  outlet coordinates, upstream area and downstream connection.
- Compare the observation and outlet locations, areas and network order.
- Save a machine-readable station-to-model-cell handoff and a map.

**Outputs**

- `metadata/21_gauge_allocation.csv`
- `figure/f21-gauge_allocation.png`
- Step 21 Survey and Work Reports

## Human Instructions

Adapt the station source, selected-station inventory and current map paths for
the event. Run the allocation check and then render its Figure:

```sh
bash s21-gauge_allocation.sh
bash f21-gauge_allocation.sh
```

The processing script verifies the supplied candidate against the current map
and relevant existing allocation outputs. It must not substitute a nearest
grid cell without evaluating outlet position, upstream area and network
connectivity. Report area-unit uncertainty explicitly; do not present a
conditional unit assumption as source metadata. The output row/column values
are zero-based Python array indices, with row following the map's latitude
array order. Keep the source index convention and current local-map indices
separate.

## Example AI Agent Prompt

```text
Complete the gauge-allocation preparation for this flood-event tutorial.
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
if the full-map view cannot show their separation. Create a researcher-facing
Survey Report and technical Work Report, and update the Tutorial process and
development log. Do not modify model/map/source-observation data, extract model
flows, calculate performance metrics, or publish a Gallery item. Human review
is recommended but is not a script execution gate.
```

## Expected Handoff and Review

The CSV is the machine-readable handoff for a later flow-extraction step. A
reviewer can compare the source and selected indices, outlet location, area
units, map topology and Figure. Human review is recommended, but does not gate
processing. Do not treat a checked spatial mapping as a validated discharge
comparison; time conventions and discharge units may still be unresolved.

# Step 21 — Gauge Allocation Survey

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

## Figure and interpretation

![Figure 21 — Gauge and model outlet allocation](../figure/f21-gauge_allocation.png)

*Figure 21. Orange circles are provider gauge coordinates; blue squares are
the current CaMa-Flood unit-catchment outlets. The dotted connectors show
straight-line separation, and the insets expose local river context. Neither a
grid center nor the ECMWF candidate coordinate is substituted for the map's
outlet coordinate.*

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

## Allocation decision

Retain the existing ECMWF candidate cells for all three stations. In
`metadata/21_gauge_allocation.csv`, `model_row_0based` and
`model_col_0based` are the indices to use for the current map's `[lat, lon]`
arrays and the Step 14 `outflw(time, lat, lon)` output. The source's raw global
indices are recorded separately. The current GRDC output independently agrees
with the same local cells.

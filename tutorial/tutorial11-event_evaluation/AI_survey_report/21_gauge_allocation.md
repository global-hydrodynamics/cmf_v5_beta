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

## Scientific review of impact-location river allocations

The original geographic assignments are retained: **21 of 22 report records**
have coordinates inside the map and remain attached to their containing
0.25° cell; the Eupen reservoir-outlet record has no verified coordinate.
These `model_row_0based` / `model_col_0based` fields answer where the reported
coordinate falls. They do not identify the river represented by that cell's
outlet.

The review used the regional one-minute `catmxy` assignments to inspect the
fine-grid catchment associated with each point, then checked the corresponding
15-minute outlet coordinates, upstream area, channel width and `nextxy`
continuity. `catmxy` is model-map association evidence, not independent river
truth; area agreement and topology were considered with documented river and
gauge locations. The CSV now separates candidate `river_model_*` fields and
`river_allocation_status` from the preserved geographic cell.

| River system / site | Geographic cell evidence | River assessment | Step 23 implication |
|---|---|---|---|
| Ahr at Schuld / Müsch | Both points lie in (10,15), whose outlet has 680.3 km² upstream area. | **Plausible, coarse downstream Ahr-path context**, not a point match at Schuld/Müsch. The outlet is about 16.5 km downstream of the Müsch gauge and the reported gauge basin is 353 km². | Use only as provisional Ahr-system timing context. |
| Ahr at Altenahr | Coordinate-containing cell (9,15) has a 630.3 km² outlet about 37 km from the gauge point; its local `catmxy` point falls in the large downstream routing cell. | Separate candidate (10,15), outlet near Altenahr, 680.3 km² versus the official 747 km² gauge catchment, with `nextxy` toward the Sinzig confluence: **plausible**, not confirmed. | Geographic-cell series is not an isolated Ahr series; candidate is the better but still coarse river cell. |
| Bad Neuenahr / Bad Bodendorf | Containing cells route through the high-uparea Rhine/confluence cells (~140,000 km²). The local `catmxy` assignments also point to that mixed downstream cell. | **Not represented** as a distinct Ahr channel at these locations. | Do not interpret the containing-cell Rhine hydrograph as local Ahr discharge. |
| Sinzig | The Ahr reaches the Rhine near the local confluence; the containing cell has ~140,561 km² upstream area. | **Unresolved / mixed confluence**; it cannot isolate the Ahr contribution. | Regional context only. |
| Erft: Bad Münstereifel, Euskirchen, Bliesheim | Fine-grid assignments identify (9,15); its outlet has 630.3 km². | **Plausible** Erft basin candidate; Bliesheim's official catchment is 604.17 km², while the coarse outlet is several kilometres away. | Candidate is useful for basin timing, not exact site conditions. |
| Erft at Blessem | Geographic cell (8,15) routes on a ~144,251 km² main routing channel. | `catmxy` and topology identify (8,14), ~1,450 km², downstream of (9,15): **plausible** Erft candidate, but coarse. | The original geographic cell is unsuitable as local Erft discharge. |
| Kyll at Kordel | Geographic cell (12,14) lies on the large downstream routing cell (~25,093 km²). | Candidate (11,14) has 819.9 km², matching the official 819 km² Kordel catchment; outlet ~1.5 km away and `nextxy` proceeds downstream: **confirmed at basin/cell scale**, not a sub-grid reach guarantee. | Use candidate (11,14) for Kyll timing. |
| Prüm at Prümzurlay | Local point assignment reaches a ~4,221.6 km² cell near the Prüm–Sauer confluence; official Prümzurlay basin is 574 km². | **Not represented** as a separate Prüm channel candidate in the available map evidence. | Do not use the confluence cell as a Prüm-only hydrograph. |
| Vesdre, Geul, Gete, Dyle | Fine-grid assignment and outlet network generally provide local-basin-scale cells. | **Plausible**, not confirmed, because outlets and 0.25° support do not resolve exact affected reaches; the Halen reach is not independently confirmed. | Interpret as basin context; retain location uncertainty. |

These official source measurements support the limited catchment comparisons:
[RLP flood report](https://lfu.rlp.de/fileadmin/lfu/Service/Publikationen/Bestellkatalog/Hochwasser_im_Juli2021_barrierefrei.pdf),
[Erftverband Bliesheim gauge record](https://www.erftverband.de/mapserver/arcshp/flussgebiet/klima_abfluss/howis/html/pegel/Pegel_Bliesheim_zr.html).
No claim is made that upstream-area similarity alone proves river identity.

Across the 22 records, the reviewed statuses are **2 confirmed**, **14
plausible**, **1 unresolved**, **4 not represented**, and **1 not assessed
because coordinates are missing**. These counts are report records, not unique
sites or independent model reaches. The full evidence and separate candidate
cells are in
[`metadata/21_impact_location_allocation.csv`](../metadata/21_impact_location_allocation.csv).
The 15-minute grid can merge minor tributaries with neighbouring networks or
skip locality-scale reaches in `nextxy`; do not snap those locations to the
Rhine mainstem and call them local tributary flow.

## Figure and interpretation

![Figure 21 — Gauge and flood impact location allocation](../figure/f21-gauge_allocation.png)

*Figure 21. Orange circles and blue squares show the three discharge gauges
and their allocated outlets. Colored circles show reported impact localities;
triangles show separate Step 01 report sites; dark squares show outlets of
geographic containing cells; magenta diamonds mark reviewed river-assessment
candidate outlets. Dotted connectors represent straight-line point-to-cell
outlet distances, not river paths. The two local views separate western
Meuse/Vesdre sites from the Ahr/Erft/Kyll/Prüm cluster.*

The checked gauge candidates remain the Step 22 spatial handoff: each has a
current-map index, valid outlet coordinates and agreement with the available
GRDC map allocation. Outlet-to-gauge distances of 8.7–15.1 km remain material
spatial offsets. For impact sites, Step 23 should use the river-assessment
candidate when it is separately recorded and clearly distinguish that
candidate from the containing-cell assignment; it should not treat
`not_represented` or `unresolved` records as local channel comparisons.

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

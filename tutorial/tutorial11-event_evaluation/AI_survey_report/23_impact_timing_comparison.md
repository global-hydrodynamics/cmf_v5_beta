# Step 23 — Flood Impact Timing Comparison

## Rerun with final impact allocations — 2026-11-24

Step23 has been re-executed with final Step21 `river_model_*` cells. All 22
report rows are retained; 21 coordinate-bearing reports share **10 model
cells**, with **1,680 hourly samples** (10 × 168). Eupen has no coordinate or
series. The model search period remains `[2021-07-12 00:00, 2021-07-19 00:00)`
UTC. Fig23a displays July13–16; Fig23b displays July14–15 (end-exclusive
16 July 00:00 UTC). All model maxima lie inside the
search window, not on its boundaries. No simulation or allocation rerun was
performed. Inputs and output fingerprints are recorded in
`metadata/23_handoff_status.json`; the earlier stale-output notice is resolved.

The selected-cell basis remains explicit: direct catmxy or a reviewed one-step
upstream tributary proxy. Lower-Ahr reports now use the 680.265 km² upstream
Ahr cell (10,15); they are no longer plotted as mixed Rhine/confluence series.
Prümzurlay now uses its direct 580.627 km² catchment (11,13), not the previous
downstream confluence cell. These choices preserve the limitations documented
in Step21; proxies omit downstream tributary area and do not resolve the exact
local reach. Repeated reports at one cell share one model hydrograph.

## Figures

![Fig. 23a — Final-allocation hydrographs](../figure/f23a-impact_hydrographs.png)

Hourly model outflow is plotted once per final cell. Red dashed lines mark
search-window maxima; orange markers denote recorded UTC discharge peaks, and
purple dotted markers denote UTC water-level peaks as reference only. The
shared Ahr panel explicitly identifies its upstream proxies.

![Fig. 23b — Report-linked timing summary](../figure/f23b-impact_timing_summary.png)

Each report retains its own row. Basin-color squares match Fig1; red model
diamonds, orange discharge circles and purple reference-only water-level
triangles preserve their meanings. Bold labels identify plottable UTC peaks,
and compact codes identify missing/uncertain/proxy support. Date-only or
timezone-unknown records are not assigned an inferred UTC observation time.

## Fig. 23b display and scientific reading

Fig. 23b defaults to **14 July 00:00 to 16 July 00:00 UTC**, with six-hour
ticks. This is a display window only: the saved model maximum still comes from
July12–18. Halen's maximum at **16 July 04:00 UTC** remains visible as a right
arrow outside the axis, with its actual timestamp printed in the Notes column.
The arrow is an out-of-view indicator, not a peak at the display boundary.
No source-supported UTC observation is hidden by the selected display window.

Small squares immediately left of labels reuse Fig1 colors directly from
`event_figure_settings.json → panel_step1.plot_group_colors`. The detailed
`Meuse basin / Geul` group uses Fig1's Meuse category, whose existing legend
identifies Meuse basin / Geul. No color is inferred from geographic proximity;
unmapped categories would be neutral gray. All current groups map to that
existing palette. Basin squares are separate from peak marker colors.

All 22 rows and their original basin/group order remain. Short display labels
remove repeated basin/source metadata without changing CSV fields. Five rows
with a plottable UTC peak use bold labels and filled red model diamonds; rows
without a plottable UTC peak use gray labels and hollow diamonds. Orange circles
remain discharge peaks; purple triangles are water-level references only.
Very small within-row vertical offsets separate close markers without moving
their time positions. Subtle horizontal lines separate basin groups.

Repeated annotations are replaced by codes: **M** no reported peak time,
**U** unconfirmed source timezone, **P** upstream tributary proxy, **N** no
model cell, and **C** context only. Unknown-zone observations stay off the UTC
axis. The common key explains these codes once.

The event-specific note is supplied by display settings: the 2021 Rhine event
involved multiple tributary flash floods, so the row sequence across independent
catchments is **not** evidence of a single downstream-propagating flood wave.
The plotting method does not impose that interpretation on other events.

## Provisional timing results

| Ahr report | Source peak UTC | Model maximum UTC | Model minus source |
|---|---|---|---:|
| Müsch | 14 July 20:00 | 15 July 02:00 | +6 h |
| Altenahr | 15 July 00:00 | 15 July 02:00 | +2 h |
| Bad Bodendorf | 15 July 02:30 | 15 July 02:00 | −0.5 h |

All three use the **same model cell**, peak 2,227.19 m³/s, and remain
`provisional_river_match`. They are not three independent validations. Altenahr
and Bad Bodendorf use the adopted upstream proxy; the latter's −0.5 h value
compares a source timestamp with an hourly model sample and is not evidence of
half-hour model timing accuracy. Source peak times/values are themselves
estimates retained from Step01. No additional timing research was performed.

Other findings remain qualified:

- **Prümzurlay:** final cell maximum is 15 July 02:00 UTC, 1,832.41 m³/s.
  Its 10:30 UTC source peak is a water-level peak, so no discharge-peak lag is
  calculated. The previous 4,437 m³/s receiving-channel result is superseded.
- **Kordel/Kyll:** maximum 15 July 03:00 UTC, 622.64 m³/s; 08:30 UTC source
  water-level peak remains reference only, with no discharge lag.
- **Bliesheim/Erft:** maximum 15 July 02:00 UTC, 2,435.85 m³/s. The source
  10:40 clock label lacks a confirmed timezone and is not placed on the UTC axis.
- **Valkenburg/Geul:** maximum 15 July 02:00 UTC, 797.85 m³/s. The 05:30
  source label remains unconverted because its timezone is unknown.
- Fourteen locality-impact reports have no supported UTC peak time. Eupen has
  no model cell. These omissions are not evidence of no flooding.

Comparison statuses are 3 provisional discharge-peak comparisons, 2 water-level
reference records, 2 timezone-unknown records, 14 timing-unavailable reports,
and 1 no-model-cell record. Time differences are calculated only for eligible
UTC discharge peaks, following the existing Step23 rule.

## Limits and handoff

The source model file has 744 hourly `outflw(time,lat,lon)` records, m³/s and
`time: mean`. Its timezone-omitted CF reference is interpreted as UTC as in
Step22; no new timezone conversion or temporal aggregation was introduced.
Original source labels, time types, confidence and allocation basis remain in
the comparison CSV. Model input, final Step21 allocation and Step01 timing
hashes are unchanged by the rerun.

These are exploratory comparisons. Upstream-proxy support, coarse channel
representation, approximate locations, source timing uncertainty, hourly mean
semantics, cold start and existing forcing-time attribution questions still
limit interpretation. The rerun does not resolve KG-0039 or establish model
skill. Use the regenerated CSVs/Figures together with their current fingerprint
metadata; re-extract again if allocation/timing/model inputs change.

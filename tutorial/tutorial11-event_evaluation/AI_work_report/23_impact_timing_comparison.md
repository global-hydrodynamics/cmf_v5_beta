# Step 23 — Final-Allocation Rerun Work Report

## Execution and scope

On 2026-11-24, reran the existing Step23 workflow at starting revision
`ef487584` after the maintainer requested updated impact allocations. Used
`metadata/21_impact_location_allocation.csv` final river_model cells; did not
rerun Step21 or the model. No input data, event times, allocation choice,
peak-search rule, interpolation or aggregation was changed.

```sh
bash run_script/s23-impact_timing_comparison.sh
MPLCONFIGDIR=/tmp/cmf-mpl-cache bash plot_script/f23-impact_timing_comparison.sh
```

Inputs: Step01 timing ledger, final Step21 impact CSV, and
`experiment/Rhine2021/o_outflwRhine2021Jul.nc`. Before/after SHA-256 equality
was checked for all three. The model is float32 outflw(time,lat,lon),
744 × 32 × 40, m³/s; search interval July12 inclusive to July19 exclusive
contains 168 consecutive hourly labels. Time is interpreted as UTC under the
retained CF convention. Step23 now propagates direct/proxy basis and appends
the missing-downstream-area caveat to proxy rows; plot notes identify proxies.
These are presentation/provenance changes, not changes to peak calculations.

## Outputs and focused validation

- Timeseries CSV: 1,680 rows, 10 distinct final model cells × 168 hours.
- Comparison CSV: 22 report rows with all report/location IDs and source UTC
  timing fields retained; Eupen has no cell/series.
- Fig23a and Fig23b regenerated and visually inspected; proxy, water-level,
  unknown-timezone and missing-time distinctions remain visible.
- 23_handoff_status.json now marks outputs current for recorded input hashes;
  includes search bounds, method/status counts and output hashes.
- All saved timeseries values round-trip exactly to the original float32
  model values at the selected cells/times. Every saved peak timestamp/value
  agrees with an independent maximum from the extracted samples; all maxima
  lie inside the search window. Each selected cell equals the final Step21
  selector result.
- No lag is populated for water-level peaks or unknown/unavailable times.
  The three provisional Ahr offsets are +6 h (Müsch), +2 h (Altenahr) and
  −0.5 h (Bad Bodendorf), all at the same model cell. Source labels and
  model-cell support limit interpretation; the proxy is not the exact reach.

Step21 summary/prose now points to fingerprint-based Step23 currency rather
than a fixed stale message. Old research/development records remain historical;
current reports supersede the earlier 12-cell/2,016-sample results.

## Remaining limitations

No independent river/timing revalidation, model run, broader performance score
or solution of forcing-time/cold-start questions. Kordel/Prüm peak observations
are water-level references, not discharge-peak scores. The half-hour Ahr offset
does not imply sub-hourly model accuracy. Figures and CSVs are reusable only
with the recorded allocation/timing/model fingerprints. Research validator
retains the 22 pre-existing unrelated errors, with no new errors from this task.

## Fig23b-only visualization revision — 2026-11-24

Applied the maintainer's focused visualization request after the Step23 rerun.
Changed only the summary plotting function, its directly necessary CLI/Shell
settings and related documentation/metadata. The hydrograph function's AST is
unchanged. Fig1 uses `plot_script/f01-reported_flood_impacts.sh` → existing f06b renderer →
`metadata/event_figure_settings.json`, section panel_step1; the summary now reads
that exact plot_group_colors palette. Meuse basin / Geul explicitly aliases its
Fig1 Meuse category based on the existing Fig1 legend; no categories are
unresolved in the real data. A neutral unknown-category check also passed.

Executed `MPLCONFIGDIR=/tmp/cmf-mpl-cache bash plot_script/f23-impact_timing_comparison.sh
--summary-only`. No s23 or model run. New display settings are in
metadata/23_timing_figure_settings.json, and rendered row/color/layout evidence
in metadata/23_timing_figure_review.json. Updated the Fig23b output fingerprint
and render-input hashes in 23_handoff_status.json; its analysis-input provenance
is unchanged.

Verification: all 22 report rows retain their prior basin/group order, all color
indicators match Fig1 values, and five plottable UTC peak rows are emphasized.
Halen's 16 July04:00 maximum is the only outside-view model marker; it has an
arrow outside the data axes plus the actual timestamp. All source-supported UTC
observations remain visible. The fixed 11.65-inch canvas and its physical plot
area, text columns, legends and footnotes pass rendered bounding-box checks;
labels do not intrude into the time axis. Both default and an alternate display
window render; an added unmapped category uses neutral gray rather than an
inferred basin color. All source peak records remain unmodified.

Protected SHA256 checks pass for both Step23 CSVs, Step01/21 inputs, Fig1 settings,
Fig1 PNG and Fig23a PNG. No peak values, search interval, grouping/order, timezone
conversion or analysis method changed. The final PNG was opened and visually
reviewed for colors, ticks, groups, marker separation, codes and margins.
The event-specific flash-flood interpretation is in settings, not hardcoded in
the reusable summary method. No Gallery or other figure refactoring.

### 2026-11-24 — Explicit hollow-diamond legend

Maintainer clarification: preserve observation-availability encoding, without
introducing a timing-agreement threshold. Added a hollow-diamond legend entry
("no usable UTC peak observation") and a filled-diamond entry for available UTC
peak observations. The footnote explicitly states that fill does not indicate
model-observation agreement. Regenerated only Fig23b with `--summary-only`;
reviewed the saved PNG and passed the existing canvas/label bounds checks.
Analysis CSVs, Fig1 and Fig23a remain unchanged; refreshed the output hash.

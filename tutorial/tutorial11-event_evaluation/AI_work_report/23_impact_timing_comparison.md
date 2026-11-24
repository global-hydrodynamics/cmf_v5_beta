# Step 23 — Impact Timing Comparison Work Report

## Inputs and cell selection

- Step 01 timing ledger: `metadata/01_reported_flood_timing.csv`
- Step 21 review: `metadata/21_impact_location_allocation.csv`
- Model output: `experiment/Rhine2021/o_outflwRhine2021Jul.nc`
- Model variable: `outflw(time, lat, lon)`, `m3/s`, `time: mean`
- Model time: `seconds since 2021-07-01 00:00`; inherited Step 22 CF interpretation uses UTC.

The extraction preserves `report_id`/`location_id`. It chooses Step 21's
`river_model_row_0based` and `river_model_col_0based` for `confirmed` or
`plausible` assessments. For `unresolved` and `not_represented`, it extracts
the geographic containing cell only as context and flags it accordingly. The
Eupen report without a coordinate has no model cell. Distinct selected cells
are deduplicated before extraction; every report remains a separate comparison
row.

## Execution and outputs

Ran from `tutorial/tutorial11-event_evaluation/`:

```sh
bash s21-gauge_allocation.sh
bash f21-gauge_allocation.sh
bash s23-impact_timing_comparison.sh
bash f23-impact_timing_comparison.sh
```

The first two commands reran the requested Step 21 allocation with separate
river-candidate columns and regenerated Fig. 21. The latter commands used the
actual Step 14 model NetCDF and saved Step 01 timing ledger. The extraction
window is `[2021-07-12T00:00:00Z, 2021-07-19T00:00:00Z)` (168 hourly samples
per cell). The Figure window is July 13 through July 16 UTC.

Outputs:

- `metadata/21_impact_location_allocation.csv` — original geographic fields
  retained; separate river-candidate row/column, outlet, area, width, status
  and reason appended; `ai_notes` remains the final column.
- `metadata/23_impact_model_timeseries.csv` — 2,016 rows from 12 selected
  cells, with cell basis and river status.
- `metadata/23_impact_timing_comparison.csv` — 22 report-linked rows including
  original and UTC timing, model maxima, lag status, and caveats.
- `figure/f21-gauge_allocation.png` — containing-cell outlets (dark squares)
  and river-assessment candidates (magenta diamonds) are visually distinct.
- `figure/f23a-impact_hydrographs.png` and
  `figure/f23b-impact_timing_summary.png`.
- `p23-impact_timing_comparison.md`, process document, Survey Report, this Work
  Report and the Tutorial development log.

## Results and focused checks

No model rerun or observation search was performed. The model search maxima
for the 12 selected cells were finite and occurred away from both search
boundaries. The only calculated discharge-peak time offsets are the provisional
Ahr results: Müsch +6 hours and Altenahr +2 hours relative to their Step 01
UTC times. The Kyll and Prüm records are water-level peaks; Bliesheim,
Valkenburg and Eupen have unconverted source timing; unrepresented Ahr/Prüm
cells are context only. No lag or performance metric was calculated for those
records.

Both Figures were regenerated and visually inspected. Figure 23a shows one
hydrograph per unique selected cell, the model search maximum, UTC peak
markers, and the river-assessment status. Figure 23b retains one row per report
and distinguishes timing types; date-only and timezone-unknown data are not
placed on the UTC axis. Representative field and row checks confirmed the
Step 21 identifiers were retained, model sample count is 12 × 168, and the
comparison table retains all 22 report IDs.

## Handoff and limitations

The extracted CSV and comparison CSV are the Step 23 handoff for later review.
Most reported impacts have no source-supported local peak time. The two
calculated Ahr offsets remain provisional because the model cells have only
`plausible` river correspondence and the source discharge peaks are estimates.
Do not treat the close times as validation. Observation time-zone ambiguity,
water-level versus discharge timing, coarse channel representation and cell
support must be resolved or retained before any formal timing score.

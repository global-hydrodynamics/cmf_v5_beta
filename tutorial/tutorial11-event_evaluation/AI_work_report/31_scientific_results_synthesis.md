# Step 31 — Scientific Results Synthesis

## Execution and scope

Date: 2026-11-24. Task: DT-0182; validation: VR-0226.
Approved working branch: `feature/package-builder`.

Implemented the reusable [Step31 Prompt](../p31-scientific_results_synthesis.md)
and executed it once as a documentation-focused L0–L1 workflow. No scientific
software, experiment settings, observations, model outputs or existing figures
were changed. No acquisition, model run, downscaling, figure generation, input
version/SHA reconciliation or new scientific analysis was performed.
The pre-existing directory reorganization, modified records and deleted synthesis
files were preserved; the new primary report replaces the previously absent
primary synthesis, as requested.

## Source evidence and independence

The scientific sources were the current README research objectives and all16
individual Survey Reports:

- [01](../AI_survey_report/01_flood_event_overview.md) and
  [02](../AI_survey_report/02_analysis_domain_design.md): event and domain.
- [03a](../AI_survey_report/03a_satellite_availability.md),
  [03b](../AI_survey_report/03b_gfm_download.md),
  [03c](../AI_survey_report/03c_gfm_classification.md),
  [03d](../AI_survey_report/03d_focus_area_extraction.md) and
  [04](../AI_survey_report/04_discharge_observations.md): observations.
- [11](../AI_survey_report/11_regional_map_preparation.md),
  [12](../AI_survey_report/12_era5land_runoff_preparation.md),
  [13](../AI_survey_report/13_runoff_input_matrix.md),
  [14](../AI_survey_report/14_simulation_setup.md) and
  [15](../AI_survey_report/15_simulation_output_visualization.md): experiment.
- [21](../AI_survey_report/21_gauge_allocation.md),
  [22](../AI_survey_report/22_hydrograph_comparison.md),
  [23](../AI_survey_report/23_impact_timing_comparison.md) and
  [24](../AI_survey_report/24_inundation_downscaling.md): comparisons.

Inspected retained Step14,15,24 JSON and the three-gauge Step21 allocation CSV
for experiment settings, ranges, time support, counts and upstream areas.
Consulted the individual Step24 Work Report for source verification and the
Prüm timing discrepancy. Public references were carried from these individual
reports; no new literature research or live URL validation is claimed.

The previous `00_scientific_results_en.md` existed at task start (70,656 bytes).
Its bytes were preserved exactly; before/after preservation checksum agrees.
The primary `.md` was absent, so no previous primary-file copy was necessary.
Neither the preserved synthesis nor the other two integrated syntheses was read
as a writing source. No old/new content comparison was performed. A known
historical process-file link inside the preserved English report remains
unchanged to respect exact preservation.

**Independence limitation:** this chat includes prior report-writing context.
Fresh sourcing from individual reports does not make the experiment blinded or
eliminate prior contextual exposure. The researcher should account for this
when comparing Step31 output with the preserved synthesis. No claim of a fresh
independent agent/session is made.

## Synthesis decisions and outputs

Created [new English Markdown](../AI_survey_report/00_scientific_results.md)
and its [Word edition](../AI_survey_report/00_scientific_results.docx).
The Markdown contains approximately5,945 whitespace-delimited words, nine
scientific chapters, an overview, references,14 original figures and7 tables.

Scientific themes: contrasting tributary and main-stem responses; real acquisition
and valid-pixel support; spatial runoff mapping; river identity and upstream
proxies; hydrograph/time support; acquisition-selected inundation; the separate
roles of routing and terrain resolution. Related Steps are combined into a
scientific argument, rather than reproduced as16 activity summaries. Operational
file-size/download details are omitted unless relevant to interpretation.
Results, interpretations, hypotheses and proposed experiments are separated.
No observational agreement or skill score was invented.

Included the existing figures f01, f02, f03a, f03c, f03d, f04, f15a, f15b,
f21a, f21b, f22, f23a, f23b and f24. Their original identifiers and image bytes
are retained. Captions explain scientific meaning, validity support and
important restrictions. Seven tables cover passes, gauges, experiment settings,
main-stem peaks, Ahr offsets, satellite/model definitions and integrated findings.
The README now distinguishes the new Step31 products from the preserved comparison
report. Step24 remains the final analysis; Step31 adds writing only.

## Scientific consistency review

Checked the main numeric statements against the individual reports and selected
metadata:45 Items/6 passes/27 products;37 unique assets;35,225 valid-support cells;
75.9% maximum fraction; the distinct182,974 and160,301 flood-pixel populations;
140,228 retained pixels/87.5%;3×1,460 station values;40×32 and111×91 grids;
1,245 mapped cells/16,963 contributions;744 steps/no spin-up; discharge ranges;
16 direct plus5 proxy assignments/one unassigned;528 and88 comparison labels;
10×168 extracted samples; Ahr offsets; nearest06UTC selection/~9min20s; and
42,960 valid/240 missing/37,429 dry/5,531 positive depth cells.

Interpretation preserves mean outflow versus point depth, valid-class conditional
Flood Fraction, native assignment versus geographic containment, shared model
series versus independent evidence, and river-water depth versus overbank flooding.
Values are rounded for reading while discrete counts and settings are retained.

Known unresolved questions are carried forward, not resolved by synthesis:
station units/timezone/averaging bounds; ERA5-Land00UTC/first-value and boundary
attribution; reconstructed Ahr peaks; Prümzurlay10:30UTC in the retained LfU-derived
ledger versus05:30UTC in Mohr Section3.2.2; proxy reach support; cold-start and
regional-edge sensitivity; and satellite/model water definitions and common
valid support. Source-derived full20m classification counts remain inherited
provenance; the absent full raster was not restored or rechecked. Knowledge-gap
review found no additional material scientific gap beyond these retained issues.

## Word conversion and checks

Used the bundled document runtime, python-docx and a small task-local converter
outside the repository. The new Markdown was the only scientific content source.
A4 layout, black hierarchical headings, embedded original images, caption styles,
editable tables and source hyperlinks are retained. Local links remain relative
to the report directory; keep the repository context when following them.
No report-generation framework or s31/f31 entry point was added.

PASS: all274 nonempty ordered text/cell blocks correspond exactly to Markdown
with formatting removed;14 embedded images equal the original figure bytes;
7 actual editable Word tables; previous synthesis preservation.
Rendered using the bundled LibreOffice/PDF toolchain and inspected all21 page
PNGs, including all figures, tables, captions and references: no conversion
clipping, overlap or detached captions found. Large multi-panel figures retain
native embedded resolution and may need zooming for their smallest labels.
The Word file is approximately14.1MB; temporary converter, PDF and page PNGs
remain outside the repository. Microsoft Word itself was not launched.

PASS: focused local Markdown references and figure paths, scoped diff and
whitespace review. The repository research validator still reports15 pre-existing
errors (one missing historical validation reference and14 unrelated historical
links), with no new errors. Scientific execution and regression tests are not
applicable to this writing task and were not run. Changes remain uncommitted
for maintainer review; no push or old/new comparison was performed.

# Step 24 — Flood Inundation Downscaling, Visualization, and Assessment

### How to Use This Workflow

**Rhine 2021:** Use the current selection, maps and options below; provide
the entire Markdown file as an attachment or copy its full content. Honor the
recorded documentation-completion scope and reuse current A–C products.

**Another event:** Review the selected pass/scene times, representative-time
rule, model experiment/time support, domain, compatible coarse/auxiliary maps,
output resolution and downscaling options in Parts A–D and their handoffs.
Rhine's orbit, dates, 06 UTC selection and map resolutions are current-case
configuration, not constants for the method. Verify the implementation and
required inputs; editing the Prompt alone does not adapt them. Supply the
entire updated file once scientific choices and prerequisites are established.
Rhine's recorded completion/no-regeneration note applies to its retained
products, not to an unexecuted new event; the general scope exclusions remain.

Parts A–D and the completion/scope guidance must be read together. The inline
execution instructions are not a standalone extract.

## Workflow Summary

- **Inputs:** Selected satellite acquisition and exact scene timestamps;
  model output/configuration and time convention; matching coarse/high-resolution
  maps; analysis domain; event, observation, allocation and timing evidence.
- **Tasks:** A: satellite–model time matching; B: existing terrain-based
  downscaling; C: diagnostic visualization; D: scientific interpretation and limits.
- **Outputs:** One simulated-depth NetCDF under ignored `out/`,
  `metadata/24_downscaling_verification.json`, `figure/f24-inundation_1min.png`,
  scientific Survey Report and technical Work Report.
- **Agent role:** Execute the requested feasible workflow, distinguish verified
  facts from hypotheses, and retain provenance/uncertainties for researcher review.
- **Validation:** Preliminary L0–L1. Check time/grid/units/masks and inspect the
  diagnostic figure; verify scientific claims and links without claiming skill.

## Reusable Agent Workflow Prompt

Use the current event's documented acquisition, experiment, map and domain.
Keep event-specific findings in metadata and the Survey Report. Preserve source
observations/model/maps and previous Steps. If A–C outputs already exist and
are current, inspect them and complete D without rerunning those workflows.

### Part A — Satellite–model time matching

Read exact source-scene acquisition times and group only the selected pass.
State the representative-time rule, verify model time convention and point/mean
semantics, then select the nearest available CF timestep with no interpolation.
Record the observation interval/representative time, actual model time/index
and signed/absolute difference. Current Tutorial selection is one S1A orbit 038784
pass on 15 July 2021, approximately 05:49–05:52 UTC; verify exact times and the
06 UTC selection against `metadata/24_downscaling_verification.json`.

### Part B — Inundation downscaling

Reuse the maintained `tools/downscale_flddph` method with matching map inputs.
Confirm flddph meaning/units, original simulation resolution, output resolution,
geometry, required terrain/connectivity layers and calculation options. Do not
substitute interpolation or a different algorithm. Current implementation uses
15 arcmin flddph and 1 arcmin Rhine maps; retain method/map/time provenance and
correct missing masks. Record permanent-water and regional-buffer limitations.
`run_script/s24-downscale_inundation.sh` is the processing entry point.

### Part C — Visualization

Use `plot_script/f24-inundation_1min.sh` to render the saved output without recomputing it.
Keep Fig 24's variable definition and established workflow. Distinguish dry,
missing and positive-depth cells; show time, extent, scale, units and preliminary
status. Positive depth must not automatically be labelled overbank flood extent.
Inspect the saved figure; do not publish to the Gallery without authorization.

### Part D — Scientific assessment

The Survey Report is an essential deliverable. Explain objective/method,
spatial results, event characteristics, four categories of limitations (model
resolution/hydrodynamics, forcing, downscaling, observation comparability),
scientific interpretation, future opportunities and conclusions. Link existing
figures/metadata and verified sources. Distinguish demonstrated findings,
plausible explanations and unresolved questions. Do not infer underestimation
from narrow river-aligned patterns alone: separate insufficient modeled water,
unresolved spatial detail and different simulated/observed physical quantities.

Verify observation support, water classes, denominator and timing before any
comparison claim. Distinguish hydrodynamic resolution from terrain/downscaling
refinement; neither is a guaranteed solution. Finer DEMs/maps, forcing/geometry
improvements and rigorous matching are future research opportunities, not new
implementation requirements. Keep execution and checks in the Work Report.

## Recorded Rhine 2021 completion and scope

The time-selected 1min product execution and Fig 24 are recorded; check local
product availability in the [preparation record](AI_work_report/00_synthesis_preparation.md).
Prompt, Survey/Work Reports and
workflow overview consistently cover A–D; technical facts/links are checked;
interpretation remains within the evidence. No separate subsequent assessment
Step is required. No other acquisition, GFM comparison, accuracy metric, new
algorithm, finer-resolution downscaling or model rerun is authorized here.
For this documentation completion, do not regenerate existing outputs unless a
specific factual inconsistency requires correction.

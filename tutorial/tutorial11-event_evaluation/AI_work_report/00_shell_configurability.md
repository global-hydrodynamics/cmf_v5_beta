# Tutorial11 — Shell configuration review and collaboration rule

Date: 2026-11-24. Task: DT-0175; validation: VR-0218.
Status: implemented in the worktree for maintainer review; no commit/push.
This is an AI-authored implementation account, not a scientific assessment.

## Scope and configuration ownership

Reviewed all **22 top-level Shell entry points** against the current worktree,
root/Tutorial AGENTS, tutorial development guidance, figure-making guidance,
and the cama-development, cama-visualization and large-model-refactoring Skills.
The 21 active entry points needed at least settings organization, explanatory
comments or actual forwarding improvements. None was wholly unchanged/compliant;
f15 already exposed most display controls. The remaining entry,
`f01-gfm_3sec_validation.sh`, is the previously retired explanatory failure
notice: it receives no artificial configuration section or restored old workflow.
No unrelated tutorial or shared Gallery implementation is changed.

Each active Shell now identifies `User settings` and the end of that section.
Inline comments explain units, supported choices, exclusive date boundaries,
automatic behavior and structured-file ownership. Implementation/path anchors
are separate. Existing intentional PYTHON/PYTHON_CMD, RUNDIR and thread environment
interfaces are preserved; no new installation or environment selection framework.

| Shell reviewed | Exposed or clarified settings; authoritative structured sources |
| --- | --- |
| f01-reported_flood_impacts.sh | Map/cache/output, settings section, OSM switch; existing display JSON, extents/locality CSV paths own detailed settings. |
| f02-analysis_domain.sh | Map/cache/output and OSM switch; existing settings JSON and extents/locality/station CSV paths remain authoritative. |
| s03a-satellite_availability.sh | Python, Atlantis/catalogue roots and domain JSON; acquisition dates and bbox remain in domain JSON. |
| f03a-satellite_footprints.sh | Domain/catalogue/map/cache/output paths, OSM switch, canvas dimensions and DPI. |
| s03b-download_gfm.sh | Domain/selection handoffs, Atlantis/reuse roots, workers and offline mode. |
| s03c-classify_gfm_extent.sh | Domain/selection and native manifest paths, output root and overwrite flag; class semantics unchanged. |
| f03c-flood_fraction_1min.sh | Source/domain/focus/locality/map/cache/output paths, canvas/DPI, colormap, limits in percent, PowerNorm gamma and OSM switch; retained --figure-only. |
| s03d-extract_gfm_focus_areas.sh | Source raster, structured focus definition/provenance, output root. |
| f03d-gfm_focus_areas_20m.sh | Crop manifest, output/cache, width/height (0 automatic), columns and DPI; categorical meanings/colors retained. |
| s04-prepare_discharge.sh | Source station directory and metadata output directory; existing Python fallback retained. |
| f04-observed_discharge.sh | Station/series paths, exclusive start/inclusive end in source time labels, y-limits, canvas/DPI/output; no assumed UTC or invented units. |
| s14-run_simulation.sh | Existing period/map/runoff/physics/output/thread/run-directory settings explained; executable/Python/Restart input accessible; Step13 JSON still owns matrix/diminfo paths. |
| f15-maximum_discharge.sh | Existing data/color/normalization/panel/OSM/DPI controls clarified; regional/AOI canvas heights forwarded with existing aspect ratios. |
| s21-gauge_allocation.sh | Map and output paths annotated; actual spatial allocation logic remains Python. |
| f21-gauge_allocation.sh | Allocation/map/output paths, catchment extent with explicit ordering, overview width/height and DPI. |
| s22-extract_hydrograph.sh | Model/observation/allocation/dataset paths, period and output paths annotated. |
| f22-hydrograph_comparison.sh | Saved series/summary/output, optional display period (blank inherits summary), y-limits, model/observation colors and canvas/DPI. |
| s23-impact_timing_comparison.sh | Model/timing/allocation paths, exclusive search end and output paths annotated. |
| f23-impact_timing_comparison.sh | Saved inputs/outputs, Fig23a width/row height/DPI; existing Fig23b settings JSON owns its timing/colors/layout/DPI. |
| s24-downscale_inundation.sh | Model/map/downscaler/domain/selection/output/metadata paths; the supported single S1A pass and maintained method are not turned into unsupported options. |
| f24-inundation_1min.sh | Existing downscaling metadata/output, color limits [m], colormap, canvas/DPI. |
| f01-gfm_3sec_validation.sh | Retired notice only; intentionally exempt. |

Added only necessary optional CLI adapters in Tutorial Python. Defaults for legacy
direct Python calls remain compatible; these fallbacks are not an alternative
routine configuration interface. Shell arguments override them. Structured
station/scene lists and geographic contracts are not copied into Shell.
`metadata/23_timing_figure_settings.json` gains three flat display-layout keys;
its default dimensions/DPI reproduce the previous plot. No scientific handoff,
recorded input fingerprint or published Figure is refreshed by this interface task.

Custom plotting periods now generate corresponding captions rather than leaving
hardcoded July/full-period text. Fig24 reads existing observation/model times
from its verification metadata; it does not select a new observation or rerun
downscaling. Source-time labels in Fig04 remain unconverted. The scientific
aggregation, native class semantics, masks, allocation, runoff and downscaling
algorithms have not been revised.

A configuration invocation exposed the macOS Bash 3.2 `set -u` empty-array issue.
Optional arguments now use a documented guarded expansion; the previously
existing f03c empty-array failure is also corrected. This is execution plumbing,
not a change to scientific selection.

## Permanent Human–AI convention

The normative authority is [Tutorial AGENTS section 10](../AGENTS.md#10-human-configurable-ai-executable-workflow):
**Human-Configurable, AI-Executable Workflow**. It extends and links the existing
root Shell rules and visualization configuration-ownership guidance. The process
document links it rather than defining another copy. It explicitly applies to
future new/modified active Tutorial11 entry points, requires genuine wiring and
single configuration ownership, and preserves independently executable workflows.

Rationale: routine scientific/display choices belong to the researcher and must
remain accessible after an AI-assisted implementation. Code generation alone
does not provide human control or a reproducible experimental interface.

**Shared adoption proposal (not implemented):** add a short normative reference
in `tutorial/agent_tutorial_development.md`, adopting the existing root settings
and visualization ownership rules for future new/modified tutorial wrappers.
The principle suits all tutorials; retroactive cleanup or changes to other
Tutorials need a separate scope. No competing shared standard is introduced here.

## Verification performed

Checks used the existing Miniforge dy Python 3.11.11 with required libraries;
no package install, environment rebuild or shared-environment change. All generated
validation files are in a disposable `/tmp/cmf-t11-config.*` tree. Default comparison
baselines were copied from the pre-task worktree, preserving earlier edits.

- **PASS:** `bash -n` for all 22 Shells; AST parsing for all 20 Python files in
  `script/`; changed Python entry points also import and parse `--help` (11).
- **PASS:** all 21 active wrappers invoked from `/tmp` using disposable copies
  with only their Python executable setting replaced by a capture stub. All
  20 Python CLI wrappers forward flags accepted by their actual implementations.
  Settings-section/comment/use inspection complements this argument capture.
  This checks interfaces, not scientific processing or every nondefault combination.
- **PASS:** s14 metadata reading and generated Namelist checked with a fake model
  executable. Default parameter text equals the pre-task Namelist after removing
  comments and normalizing temporary root paths. No real model was executed.
- **PASS:** 8 default images rendered before/after and compared as decoded RGBA:
  Fig04, Fig21 regional and catchment detail, Fig22, Fig23a/b, Fig24 and Fig03c.
  All have exact pixel equality. Fig24 uses a synthetic depth NetCDF because its
  derived production NetCDF is absent. Fig03c uses retained fraction data in
  render-only/no-OSM mode. Other comparisons use retained CSV/metadata/map inputs.
- **PASS:** nondefault Fig04 period (July10–20), y-maximum and dimensions/DPI;
  Fig24 colormap, upper color limit and dimensions/DPI render successfully.
  The Fig24 custom canvas is exactly 700 × 600 pixels. Saved Fig23b and custom
  Fig04 outputs were visually inspected for labels/layout; no browser GUI claim.
- **PASS:** existing `tests/test_gfm_workflow.py`, 13 tests in 0.564 s. Synthetic
  masks, classification, native grids, valid-support fractions, reuse/resume and
  protected-path checks. Initial restricted execution blocked the localhost
  fixture server; rerun with local-server permission passed all tests.
- **PASS:** `git diff --check`, relevant local links/JSON/CSV and no task-generated
  datasets/PNG/binaries in the repository. Remote branch refs fetched without
  checkout/merge; origin remains equal to HEAD. Open Tutorial11 issue and open PR
  searches returned none. Pre-existing worktree and execution-mode edits kept.

Research-record validator: **15 pre-existing unrelated errors remain**, unchanged
from the preceding task; new DT-0175/VR-0218 records introduce none. These include
legacy broken links and the earlier unknown VR-0206 reference. This is not a
repository-wide validation pass.

Representative commands (run from repository root):

```bash
bash -n tutorial/tutorial11-event_evaluation/f04-observed_discharge.sh
PYTHONDONTWRITEBYTECODE=1 GDAL_PAM_ENABLED=NO PROJ_NETWORK=OFF \
  MPLCONFIGDIR=/tmp/cmf-t11-mpl \
  /Users/yamadai/miniforge3/envs/dy/bin/python -B \
  tutorial/tutorial11-event_evaluation/tests/test_gfm_workflow.py
```

Temporary evidence: `interface_verification.json` records captured CLI flags and
the default Namelist check; `figure_verification.json` records the eight exact
image comparisons and custom renders. These are task-local verification records,
not another permanent configuration registry or reusable testing framework.

## Limits and remaining work

No event/model simulation, new acquisition, full peak processing, environment
repair, broad regression or input-version/SHA reconciliation was performed.
The default appearance comparisons establish rendering compatibility on the
specified inputs/environment, not scientific equivalence of all possible runs.

Fig01/02 shared renderers are unchanged and checked through their forwarded
configuration. Fig03a lacks local catalogue inputs; Fig03d would need uncached
OSM requests. Fig15 would repeat peak-product processing. Those real-data figure
runs were not performed. Missing Step24 depth data was replaced only in temporary
rendering fixtures, never in the Tutorial products or scientific findings.

Detailed metadata/settings retain their pre-existing schemas and responsibilities.
Changing a processing input requires executing its relevant Step and refreshing
handoffs under the existing AGENTS responsibility rule; editing a Shell setting
does not assert a new scientific result. Existing output guards/overwrite behavior
remain in force. Shared-guideline adoption remains a maintainer decision.

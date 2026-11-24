# Tutorial11 Synthesis Preparation — Work Report

## Authorization and boundary — 2026-11-24

The maintainer accepts the bounded follow-up to the structure/documentation audit:
locate missing data/environments, correct Step12–14 contracts and retired-code
references, define handoff maintenance responsibility, and prepare three
syntheses. **Input-version and SHA reconciliation is explicitly unnecessary and
excluded.** No original or derived scientific data, stored fingerprint, model
setting, allocation or Figure is changed. No acquisition, environment setup, model/real-data analysis execution, or
synthesis of new scientific findings is performed. Focused synthetic tests
verify the corrected code references without reprocessing observations. Work stays on existing `feature/package-builder`.

The initial worktree had execution-mode-only changes to f21, s21, s23 and s24.
These pre-existing changes are preserved. No commit or push is part of this
follow-up request; changes remain for maintainer review.

## Data and environment location findings

The [availability inventory](../metadata/event_artifact_availability.csv) records
paths, state, downstream need and recovery options. Checks covered the current
repository and documented external `~/work/Atlantis/` workspace; this is not a
search of every disk or backup. Only filesystem presence/file counts and
symlink destinations were inspected, without reading raster values or comparing
input fingerprints.

- Original station files, processed1min GFM fraction,15focus crops, regional
  map, and existing model outputs are present. The runoff directory contains31
  converted daily NetCDFs and31original daily NetCDFs; presence/count is not a
  new validation of values or period semantics.
- The external workspace retains STAC/acquisition metadata and run logs, but
  its raw COG directory is empty. Tutorial-local `Atlantis/` and its Step3b
  manifest/summary are absent. These two catalogue/manifest layouts must not
  be conflated.
- Full20m classification, Step15 derived peak NetCDF and Step24 derived depth
  NetCDF were not found at their documented paths. Existing Figures and compact
  metadata remain, so these syntheses need no reprocessing.
- Repository `.venv/bin/python` is absent. External `source -> old/source` is
  broken and no `old/` exists in that workspace. A targeted search also located `~/miniforge3/envs/dy/bin/python`
  (Python3.11.11), with NumPy, netCDF4, rasterio, Matplotlib and requests.
  This existing environment ran the13 focused synthetic GFM contracts; no
  installation, symlink repair or environment reconstruction was needed.
  Backups and other disks were not exhaustively searched.

## Recovery decisions

| Requested future work | Minimal requirement | Work performed now |
| --- | --- | --- |
| Read the synthesis reports | Existing reports/CSV/JSON/Figures | Completed; no dataset recovery needed |
| Rerender existing1min GFM fraction | Existing dy environment, saved fraction and context; `f03c --figure-only` | None |
| Recreate Step15 peak dataset | Restore backup, else run f15 from retained model/map files | None; no model rerun needed merely for derived data |
| Recreate Step24 depth dataset | Restore backup, else run s24 then f24 with a suitable environment | None; do not imply historical result identity |
| Recreate full20m classification / crops | Restore source class raster, or restore/reacquire native COGs and rebuild Step3b/3c handoff | None; retained crops do not reconstruct the whole raster |
| Reuse retired3sec workflow | Read its historical Git revision as history | Not reinstated; not required by current tutorial |

## Changes made

1. Aligned p14 to the actual31-day July1–August1-exclusive run and
   `experiment/Rhine2021/`; corrected its Shell header comment only. Scientific
   Shell settings are unchanged. Corrected p12's final matrix handoff to
   `ERA5land_Rhine2021Jul` and p13's old acquisition period.
2. Corrected the event Survey's attribution of six-hour interval semantics to
   provider correspondence, and the Step14 Survey's pthflw dimension exception.
3. Replaced the broken historical f01 3sec Shell call with an explicit retired
   message and status2; it generates no files. Kept the historical Git source
   as history, without restoring competing3sec processing code.
4. Kept13 focused GFM test methods: replaced obsolete3sec aggregation/owner/grid
   expectations with current class-denominator, categorical-state and1min-edge
   contracts; adjacent native-grid checks now call the maintained native reader.
   No production scientific algorithm or test-skip gate was added. Tests do not
   assert equivalence between the historical3sec and current1min products.
5. Added handoff ownership to Tutorial AGENTS, linked the syntheses from the
   process document and separated the scientific and collaboration explanations.
6. Authored [Scientific Results](../AI_survey_report/00_scientific_results.md),
   [Evaluation Workflow](../AI_survey_report/00_flood_event_evaluation_workflow.md)
   and [Human–AI Research](../AI_survey_report/00_human_ai_collaborative_research.md).
   Numbers are attributed to retained records, not recomputed.

## Verification scope

Checks for this task are static contracts, relative links, AST/Shell syntax,
CSV/JSON structure, source-level test targets and preservation of scientific
settings. The retired Shell's message/status can be checked without running any
workflow. The adapted13 GFM unit tests were actually executed in the existing dy
environment and passed in0.582s. They cover synthetic classification/aggregation,
source parsing, reuse/resume and grid contracts, not real-event skill. The
command used `python -B tests/test_gfm_workflow.py` from this Tutorial root,
`PYTHONDONTWRITEBYTECODE=1`, `GDAL_PAM_ENABLED=NO`, `PROJ_NETWORK=OFF` and a new
`MPLCONFIGDIR` under `/tmp`; no shared environment was changed. Figure,
real-data analysis and model workflows were not rerun.

Stored input/output fingerprints and handoff execution flags remain unchanged.
Current file equivalence to recorded historical inputs is not asserted and is
not a prerequisite imposed on these retrospective reports. Step24 retains
A–D, including scientific interpretation; **Step25 is canceled**.

## Final checks and knowledge-gap review

- All22 Tutorial Shells pass `bash -n`; all22 Python files parse with `ast.parse`.
- Changed active Markdown links and new report links resolve. Chronological
  historical links outside this bounded cleanup are retained as history.
- Period/matrix/output-path contracts,13 availability rows and13 maintained test
  methods are consistent. The retired entry actually returns2 with guidance.
- `git diff --check` passes; no scientific raster, model output, Figure or
  stored fingerprint/execution flag is modified. Four pre-existing mode edits
  remain. The s14 change is a header comment, not a scientific setting.
- Research-record validation has15 existing unrelated issues after repairing
  seven historical3sec artifact links (previous audit count22). New task/event/
  validation references are structurally valid; no full-registry repair claimed.
- Knowledge-gap review completed: existing observation units/timezone, KG-0019,
  KG-0039 and boundary/observation-support limits remain. No new scientific
  resolution or unsupported Human approval is inferred. Data availability and
  the explicit exclusion of input-version checks are documented limitations.


## 2026-11-24 — Comprehensive Japanese case-study reconstruction (DT-0179)

Maintainer requests a complete restructuring of the existing scientific-results
synthesis as an outcome/figure-led case study accompanying an ECMWF Event-based
Benchmark prototype development report. No separate main deliverable report,
new analysis, acquisition, simulation, data verification or SHA comparison.
Applied large-model-refactoring at bounded prototype-documentation scope.

Read all16 executed-Step Survey Reports and corresponding Work Reports, the
process/general-workflow/collaboration syntheses, and relevant saved metadata.
Scientific explanation follows Survey Reports; actual execution/reuse follows
Work Reports. Retained the current31-day standard-nextxy experiment and final
Step21/23 assignments rather than historical20-day or superseded allocations.
Existing Fig03d/23b/24 images were opened for caption/meaning inspection; none
was regenerated. Other captions follow their existing Step explanations.

Rewrote `AI_survey_report/00_scientific_results.md` in Japanese as six chapters:
introduction; event/design; observations; experiment; comparison/assessment;
outcomes. It contains all14 unique existing embedded Survey figures,17 numbered
tables, all8 source Survey tables' content, and all16 completed Step sections.
Each Step links its Survey and Work Report. No images copied, new scientific
conclusions invented, or unrecorded Human–AI roles/productivity metrics inferred.
Known Prümzurlay source-time discrepancy is retained with its Work Report link.
Local environment/status/hash concerns are excluded from the scientific narrative.

Documentation checks:14/14 figure-reference coverage, captions,17 sequential table
captions, all8 source-table coverage and exact preservation of the15-row crop
table; six chapters and16 Step/pair references; all70 relative paths/anchors;
CSV structure and diff/scope checks. Read-through separates observed/modelled
quantities, conditional fractions, non-independent proxy comparisons and formal
skill from exploratory results. No source/data/metadata/PNG/test changes.
Existing research validator errors remain15 and are unrelated to this task.
No new scientific/architectural gap: existing timing/units, coarse-reach, forcing,
cold-start/boundary and inundation-comparability questions remain explicit.

The report can be reviewed without reacquiring or regenerating products. Step24
remains final; no new numbered assessment Step. Changes are uncommitted; no
commit/push or external report submission was requested. Validation: VR-0222.


## 2026-11-24 — Maintainer-reviewed case-study finishing (DT-0179)

Maintainer approved the six-chapter coverage and requested four bounded edits:
Executive Summary, fewer duplicated defensive caveats, readable result precision,
and stronger scientific synthesis. Applied large-model-refactoring for existing
prototype documentation only. Added a quantitative overview of16 Steps,6 passes,
3 discharge stations and the31-day/744-step experiment. Rounded display results
and coordinates while preserving integer inventories and reproducible settings.
Chapter6 now treats five themes: flood space/time, satellite availability, model
resolution, hydrograph/timing and inundation. Each separates retained findings,
explicit hypotheses and proposed future tests. Important units/time-support,
proxy-cell, observation-mask and inundation-definition limits remain in context.

Validation (VR-0223): six numbered chapters and16 Step headings unchanged;
14 image references,17 table numbers and all70 link destinations preserved
against the start-of-follow-up text. All relative paths/anchors resolve, source
Survey-table coverage retained and the15-row crop table remains exact. Five
scientific themes have explicit result/hypothesis/future-test labels; requested
precision examples are rounded. Read-through and diff checks pass. No new
analysis, input verification, image generation or scientific product changes.
Knowledge-gap review: no new gap; existing scientific questions are expressed
as future tests, without claiming their resolution. Research validator retains
15 unrelated errors. Existing working-tree edits preserved; no commit/push.


## 2026-11-24 — English case-study report and external-facing references (DT-0180)

Maintainer requested final editorial changes and an English Markdown edition,
retaining the Japanese report and all scientific products. Applied the existing
large-model-refactoring documentation-only scope. Created
`AI_survey_report/00_scientific_results_en.md` with the requested title, six
chapters,16 Step sections,14 original image references,17 translated tables,
quantitative Executive Summary and the five-theme scientific synthesis.
Removed editing-session statements, numbering instructions, the Bonn provenance
detour and superseded-experiment narration. Used Flood Event Evaluation Tutorial
in prose. Kept scientific time/mask/units/proxy/forcing uncertainties and the
separation of results, hypotheses and proposed tests.

Traced event/timing provenance through Step01 Survey/Work, impact/timing CSVs and
Step23/24 reports. Added nine reference entries and direct citations at Fig1,
Table1 and Step23. Checked publisher/official records for bibliographic details;
no missing author/date/publication facts were invented. Thewissen2022 thesis
identity/title/year were confirmed through the TU Delft catalogue, whose reuse
notice requires attention before redistributing the thesis itself. Source facts
in the report were retained; no new flood analysis was conducted.

Link maintenance was confined to this English edition. Two synthesis documents
are Git-tracked and available at HEAD but absent from the current local tree:
`00_human_ai_collaborative_research.md` and
`00_flood_event_evaluation_workflow.md`. Used their immutable GitHub HEAD links
rather than recreating or modifying missing files. All other original local
reference destinations are retained. The old Waterschap PDF and TU Delft file
URLs returned404; the English references use the reachable NIPV institutional
listing and TU Delft bibliographic record. The old URLs remain in original
provenance ledgers, which were not edited. NIPV is a discovery route, not a new
verification of the Geul timing passage. LFU web-tool429 and GEER size limits
were distinguished from actual reachability: direct HEAD checks returned200.

Validation VR-0224: six chapters16 Step sections;14 unchanged image paths with
English captions;17 tables; complete numeric equality for classification,
15-crop,station,index,outlet/area inventories (Tables5/6/7/9/11/12); manual review
of all remaining time/settings/result tables; all82 local/internal link
occurrences resolve; all13 unique retained external URLs return HTTP200 to HEAD.
HTTP reachability does not establish full content or future access permissions.
English prose/terminology and internal-history exclusions checked. Five themes
retain explicit findings/hypotheses/future tests. Original Japanese text, PNGs,
metadata, model/data/source and existing uncommitted edits are preserved.
No Word/PDF conversion, scientific execution, input/output revalidation or SHA
comparison. Research validator retains15 unrelated pre-existing errors.
Knowledge-gap review: no new scientific gap; existing uncertainties remain.
Human review before external provision: scientific interpretation and unresolved
units/time/forcing/source discrepancies; reference access and original-source
reuse terms; supplied-data sharing scope and repository/metadata accessibility.
No commit/push requested; changes remain uncommitted for review.

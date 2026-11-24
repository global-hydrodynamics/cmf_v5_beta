# Flood Event Evaluation Workflow — General Method and Rhine Example

## Purpose and evidence boundary

Tutorial11 demonstrates an event-evaluation process with reusable research
contracts and a Rhine-specific implementation. This synthesis derives from the
[process document](../00_event_evaluation_process.md), Step Prompts and retained
Survey/Work Reports; it does not execute the workflow. Input-version/SHA
reconciliation is excluded by maintainer direction. Distinguish a documented
execution, an artifact present today, and a complete scientific evaluation.
The [availability inventory](../metadata/event_artifact_availability.csv) is a
location check, not a data-validity or equivalence certificate.

## Scientific dependency chain

| Stage | Required handoff | Rhine example and limits |
| --- | --- | --- |
| Establish event evidence (01) | Sourced localities, river systems, original and qualified timing | 14 localities and 22 timing/impact records; unknown timing remains blank |
| Design domains (02) | Separate model, observation and viewing extents; boundary rationale | Model3–13E/45–53N, satellite4–8E/49–52N; hydrologic completeness not independently established |
| Prepare observations (03a–d,04) | Pass identity, masks/classes, station identity, units/time semantics | One GFM pass and three supplied gauges; observations do not cover every impact reach |
| Prepare experiment (11–14) | Regional map, forcing Registry, grid-specific Input Matrix, initialization and run settings | 15arcmin map, 111×91 runoff grid, dedicated matrix, 744-hour cold start |
| Inspect modeled fields (15) | Saved derived fields with time/variable definitions | Local maximum-absolute signed discharge is not a simultaneous state |
| Establish correspondence (21,22,24A) | Geographic/direct/final allocation; time and variable support | Catchment/proxy review, nominal-time gauge overlay, one satellite-time selection |
| Compare and interpret (23,24B–D) | Qualified comparisons and explicit scientific limitations | Provisional timing comparisons and 1min simulated-depth assessment; no formal inundation score |

Steps05 and06–10 are future/reserved. Steps18–20 are unassigned, not missing
executed analyses. The conceptual matching/evaluation requirements in16–17 are
partly exercised by21–24, but formal matching and quantitative skill remain
unfinished. **Step24 ends the current sample; Step25 is canceled.** Numbering
must not be interpreted as proof that24 separate analyses were completed.

## Reusable processing contracts

1. **Observation identity before merging.** Group satellite products by actual
   acquisition/platform/orbit, not nearby clock times. Keep source footprints,
   product tiles and usable pixels distinct. Preserve missing observations as
   missing, never dry. Record crop selection and overlap limitations.
2. **Actual grid before matrix reuse.** A runoff matrix depends on origin,
   spacing, dimensions/order and map assignment. The global ERA5-Land pair is
   not interchangeable with the regional111×91 subset. Keep physical runoff
   units and accumulated/interval quantities explicit.
3. **Experiment before comparison.** Record dates, initialization, network,
   forcing and timestep/output semantics. A successful cold-start run proves
   execution only. Model input `nextxy` and fine-grid `catmxy` have different roles.
4. **Correspondence before scoring.** A containing grid cell need not represent
   the relevant tributary. Preserve direct assignment and any reviewed proxy
   separately. Do not invent missing units/timezones, substitute water-level
   peaks for discharge peaks, or count shared model series as independent tests.
5. **Physical quantity before raster comparison.** Terrain-downscaled depth,
   permanent river water and valid-support satellite Flood Fraction differ.
   Define time/spatial support, water classes and denominator before metrics.

The generic contribution is this sequence of decisions and handoffs. Shells,
pass IDs, periods, named Ahr proxies and several implementation paths remain
Rhine-specific; copying them unchanged is not a general event runner. Another
event needs its own evidence, configuration and spatial checks. No new framework
or universal proxy-selection algorithm is claimed.

## Processing, figures and data ownership

Processing should save explicit datasets and metadata; figures consume those
products. A figure-only revision does not imply re-extraction or a new model
run. Step3c's existing Figure entry also aggregates when run normally; its
`--figure-only` mode consumes the retained fraction. Step15's Figure entry
calculates its derived peak dataset. These current responsibilities should be
followed rather than assumed to be plotting-only commands.

Git stores Prompts, scripts, compact handoffs, reports, selected observations
and Figures. Native acquisitions, model/runtime outputs, environments and large
intermediates remain external/ignored. A Git checkout alone is therefore not
an end-to-end executable data package. Do not duplicate complete processing
algorithms or reinstall shared environments simply because a local product is
missing.

## Handoff and revision responsibilities

The executing agent maintains the affected Step's machine-readable handoff and
Work Report, labels newly executed versus retained results, and records input
availability. Step21 changes require explicit Step23 pending/re-executed status;
a Fig23b-only edit does not refresh extracted hydrographs. The current s23
program does not automatically update `23_handoff_status.json`; its update is
an explicit agent bookkeeping responsibility. No freshness guarantee is implied
by the JSON status alone. For this preparation task, no input-version check or
fingerprint update was performed, as directed by the maintainer.

Scientific decisions and scope remain with the researcher; recommended review
is distinct from an execution gate. Detailed collaboration rules belong in
[Tutorial AGENTS](../AGENTS.md) and the [collaboration synthesis](00_human_ai_collaborative_research.md),
not in duplicate scientific instructions here.

## Practical continuation and reproducibility limits

For these syntheses, existing reports, metadata and Figures are sufficient;
no retrieval, environment reconstruction, model run or derived-data regeneration
is needed. For future execution only:

- Use the located existing Miniforge `dy` environment with explicit script
  settings; the default `.venv` and external Atlantis target are absent. No
  installation is needed for the verified synthetic tests. Full acquisition
  environment compatibility has not been tested.
- Restore Step15/24 derived files if available. Otherwise regenerate only the
  requested derived product from retained model/map data; a new simulation is
  not required merely because a derived file is missing.
- Restore the full20m classification if full Step3c/3d reprocessing is requested.
  If unavailable, restore native COGs or reacquire the selected pass, then run
  the documented classification chain. Existing crops cannot reconstruct the
  complete source raster.

The [preparation Work Report](../AI_work_report/00_synthesis_preparation.md)
states the checked locations, remaining dependencies and checks actually run.
No broader reproducibility, hydrologic skill or portability claim is made.

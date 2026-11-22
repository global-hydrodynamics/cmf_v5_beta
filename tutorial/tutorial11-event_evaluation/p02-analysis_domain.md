# p02 — Analysis Domain Agent Workflow

## Purpose

Step 2 connects Step 1's reported rivers and impact localities to a specific
CaMa-Flood map. On the first run, the agent investigates routed basin
structure, chooses and records evidence-based proposed simulation and
satellite-analysis domains, prepares Figure 2, and presents the results for
researcher review. The researcher may request revisions; the agent updates the
same settings and regenerates the Figure as needed.

## Human instructions

After reviewing the Step 1 evidence, give the AI agent the paths to:

- `01_flood_event_overview.md`;
- `metadata/01_impact_locations.csv`;
- the reviewed Step 1 Figure 1;
- the CaMa-Flood map data and map name/version;
- any evaluation river, gauge or observation site that should be considered.

Run the workflow in that event's own directory. Researchers do not need to
supply Basin IDs or initial bounding boxes: the agent should inspect the
selected map and choose initial evidence-based candidates without waiting
for approval at each choice. Keep Tutorial 11's Rhine 2021 sample unchanged.

## Example AI agent prompt

Copy the prompt below, fill in the event and input paths, and give it to the
agent.

```text
Design Step 2 spatial domains for this CaMa-Flood event evaluation.

Event: [EVENT NAME, REGION, YEAR]
Research objective: [RESEARCH OBJECTIVE]
CaMa-Flood map: [MAP NAME/VERSION OR PATH]
Step 1 overview: [PATH TO 01_flood_event_overview.md]
Step 1 impact inventory: [PATH TO metadata/01_impact_locations.csv]
Step 1 Figure 1: [PATH TO REVIEWED FIGURE]
Additional target rivers or observation sites: [OPTIONAL]

Work only in this event's directory. Tutorial 11's Rhine 2021 materials are a
worked example: do not edit them or copy their Basin IDs, domains, viewing
extent, gauges or event settings. Inspect the supplied event evidence and the
actual selected CaMa-Flood map. Distinguish verified facts, interpretations,
candidate choices, human-approved decisions and unresolved questions.

Complete this workflow on the first Prompt run; do not stop after presenting
initial ideas. Save first-run candidate values with `status: "proposed"`. This
status records review state only and is not a program execution gate. Later
review iterations update the same files; do not create versioned filenames.

Complete this workflow:

1. Review the Step 1 overview, impact CSV and Figure 1. Summarize target
   rivers, reported localities, relevant event timing and observation
   priorities. Note approximate coordinates and uncertainty; markers are not
   inundation boundaries.
2. Analyze the selected map and metadata. Use available `basin`, `uparea` and
   `nextxy` data to associate target rivers, impact locations and gauges with
   plausible model cells, identify routing groups and upstream contributing
   networks, follow connectivity, and check the needed downstream outlet and
   neighboring groups. Derive Basin IDs from this map; never carry IDs over
   from Tutorial 11 or another map. Model routing groups may combine or divide
   natural watersheds. If the evidence cannot establish the connection or full
   contributing area, state the limitation and ask the researcher rather than
   guessing.
3. Propose three distinct extents, with bounds in W/S/E/N order, units,
   rationale, status and uncertainty:
   - **Simulation domain:** include the required full upstream contributing
     area/routed network and downstream outlet, with justified boundary
     margin. Do not define it only around damage locations or minimize its
     size as an objective.
   - **Satellite analysis domain:** one or more candidate areas informed by
     impacts, target reaches and research purpose. It may be smaller or
     separate from the simulation domain. Treat it as a candidate until later
     observation-footprint and usable-pixel checks.
   - **Map viewing extent:** a wider Figure viewport to show geographic
     context. It does not define either analysis domain.
   Do not treat a rectangle as a watershed mask or equate a model routing
   group with a natural basin without supporting evidence.
4. Prepare and run a candidate Figure 2. Reuse the Tutorial 11
   `f02-analysis_domain.sh` structure and a suitable Visualization Gallery
   renderer; do not build a new plotting framework or put event-specific
   values into shared code. Keep points and display settings in event-local
   metadata. Show the selected river network, relevant model groups, Step 1
   impacts, confirmed observation sites where available, and distinctly styled
   `Candidate`/`Proposed` simulation and satellite boxes. Choose a viewport
   that explains the geography rather than copying Rhine bounds. Inspect the
   saved Figure and correct readability or placement problems.
5. Present the map, map-connectivity evidence, proposed bounds, rationale and
   open questions to the researcher after saving the initial candidates and
   Figure 2. Ask for decisions where the scientific target or evidence is
   ambiguous. Revise target rivers, domains, viewport, settings or annotations
   in response to feedback, update the same files and rerun Figure 2 as needed.
   Continue review as useful; the iteration count is not fixed. Clearly
   distinguish viewport-only changes from changes to analysis domains. Record
   `proposed` or `approved` as informative review metadata where appropriate;
   neither status is a Shell/Python execution gate.
6. On the first run, create or update `02_analysis_domain_design.md` with
   map/version, examined routing evidence, recommended ranges, rationale,
   limitations and unresolved items. Save the initial spatial/temporal handoff
   in `metadata/02_domain_selection.json` with proposed values marked
   `proposed`; retain null/undecided values where evidence is insufficient.
   Store event-specific Figure settings in metadata. Ensure
   `f02-analysis_domain.sh` reproduces Figure 2 from those settings. After
   researcher feedback, revise the same report/settings and regenerate the
   Figure. Do not create `_v2`, `_final` or similar files.
7. Hand the current design and uncertainties to Step 3. Complete `proposed`
   values may be used when their required inputs are present; researcher review
   can revise them but is not an execution precondition. Later scene
   availability, valid-observation support, forcing or model-boundary evidence
   may require reconsideration.

Do not run CaMa-Flood or acquire satellite data in this workflow. Do not
publish to the Visualization Gallery unless separately authorized. Report the
map and version, network evidence, candidate/approved bounds, researcher
review status, generated files, commands/checks and remaining uncertainty.
Do not claim hydrologic validation from a successful figure render.
```

## Expected outputs and human review

| Output | Role |
| --- | --- |
| `02_analysis_domain_design.md` | Domain rationale, evidence and caveats |
| `metadata/02_domain_selection.json` | Spatial/temporal handoff and decision status |
| Figure settings under `metadata/` | Reproducible event-specific display configuration |
| `f02-analysis_domain.sh` | Reproducible Figure 2 entry point |
| `figure/f02-analysis_domain_design.png` | Candidate or reviewed simulation/observation domain map |

The agent completes the initial map investigation, candidate selection,
Figure and proposed settings before presenting them. Researcher review is the
recommended scientific workflow, not a software gate: downstream scripts may
consume valid `proposed` settings, and no script must require `approved`. The
researcher can request changes, which the agent applies to the same files.
Step 2 does not guarantee satellite coverage or final model boundary
conditions.

Tutorial 11 already has a provisional Rhine 2021 Step 2 example. This Prompt is
for future events and must not be run there to recreate or change its existing
domain design or Figure.

# Step 2 — Human–AI Analysis Domain Design Instructions

## Purpose

Step 2 connects the reported rivers and impact localities from Step 1 to a
specific CaMa-Flood map. Human and AI use that map to propose a simulation
window containing the required upstream watershed and outlet, and separate
satellite-analysis areas suited to the evaluation question. Figure 2 makes the
spatial relationships reviewable. Candidate settings are iteratively adjusted
with the researcher, then recorded for reproducible handoff to later steps.

The Rhine 2021 Step 2 materials in Tutorial 11 are a worked example. Do not
reuse their basin IDs, extents, map viewing window, station set or event
settings for another flood without independently checking that event and its
selected map.

## Human instructions

After reviewing and accepting the Step 1 evidence, ask an AI agent to plan Step
2 in a separate event-specific directory. Provide or point the agent to:

- `01_flood_event_overview.md`;
- `metadata/01_impact_locations.csv`;
- the reviewed Step 1 Figure 1;
- the CaMa-Flood map data and its map name/version;
- any required evaluation river, gauge or other observation site not already
  identified in Step 1.

Researchers do not need to preselect basin IDs or give the agent a bounding box.
The agent should inspect the selected map and present an initial, evidence-based
proposal for review. Keep the new event's settings and outputs separate from
Tutorial 11.

## Example AI agent prompt

Copy the prompt below for another event and fill in the bracketed fields. Run it
from that event's own working directory.

```text
I am designing the spatial domains for a CaMa-Flood evaluation of this event.

Event: [EVENT NAME, REGION, YEAR]
Research objective: [RESEARCH OBJECTIVE]
CaMa-Flood map: [MAP NAME/VERSION OR PATH TO THE MAP DATA]
Step 1 overview: [PATH TO 01_flood_event_overview.md]
Step 1 impact inventory: [PATH TO metadata/01_impact_locations.csv]
Step 1 Figure 1: [PATH TO THE REVIEWED FIGURE]
Additional target rivers or observation sites, if any: [OPTIONAL]

Work only in this event's directory. Treat Tutorial 11's Rhine 2021 files as
examples; do not edit them or copy their event-specific basin IDs, station set,
domain bounds or map settings. Inspect the event evidence and actual selected
CaMa-Flood map before proposing any spatial settings. Distinguish verified map
facts, event evidence, interpretation, candidate choices and unresolved items.

Task 1 — Review the Step 1 evidence
Read the event overview, impact inventory and Figure 1. Summarize the target
rivers, reported impact localities, event timing relevant to evaluation, and
observation priorities. Note approximate locality coordinates and uncertainty;
do not treat markers as inundation boundaries. Identify any Step 1 gaps that
affect spatial planning.

Task 2 — Analyze the selected CaMa-Flood map
Inspect the map's available `basin`, `uparea` and `nextxy` data and relevant
metadata. For target rivers, impact locations and supplied gauges:
- associate the geographic locations with plausible model cells, noting the
  map resolution and coordinate uncertainty;
- inspect model Basin IDs and upstream contributing area;
- follow `nextxy` connections to understand upstream and downstream routing;
- identify the contributing upstream network and necessary downstream outlet;
- check neighboring Basin IDs or routing groups when they affect the target.

Derive Basin IDs from this map; never copy IDs from Tutorial 11 or another
event. A model routing group may combine or divide natural watersheds. Do not
name a model group as a natural basin unless map and external watershed
evidence support that interpretation. If the available data cannot establish
the connection or full contributing area, state the limitation and request a
researcher decision rather than guessing.

Task 3 — Propose three distinct spatial extents
Propose candidates and explain the evidence, status and remaining uncertainty
for each:

1. **Simulation domain:** a model window that contains the full upstream
   contributing area and routed network required for the target river, plus
   its necessary downstream outlet and boundary margin. Do not define it only
   around damaged places or minimize its size as an end in itself. A large
   full-watershed domain is appropriate when required by the evaluation.
2. **Satellite analysis domain:** one or more candidate areas based on reported
   impacts, target reaches and the research objective. It may be smaller than,
   or spatially separate from, the simulation window. Treat it as a candidate:
   do not claim satellite observations or valid pixels are available until
   acquisition metadata and usable coverage are checked in a later step.
3. **Map viewing extent:** a wider display window chosen to show the geographic
   context and why the candidate boxes are located there. This is only the
   Figure viewport; it does not set either analysis domain.

Do not silently treat a rectangular extent as a watershed mask. Record bounds
in W/S/E/N order with units and explain any margin or included neighboring
routing group.

Task 4 — Create a candidate Figure 2
Inspect `f02-analysis_domain.sh`, the Tutorial 11 Figure 2 implementation and
the Visualization Gallery for a suitable existing method. Adapt the existing
map renderer and shell workflow; do not build a new plotting framework or add
Rhine settings to shared code. Put this event's point data and display settings
in its own files. The figure should normally show:
- OSM background and the selected CaMa-Flood river network;
- relevant model basin/routing groups and Step 1 impact locations;
- available gauges or other confirmed observation sites;
- separately styled, clearly labelled candidate simulation and satellite
  analysis boxes.

Choose and justify a viewing extent that shows the geographic relationships;
do not begin by copying a fixed Tutorial 11 extent. Use legends or annotations
to distinguish map extent from candidate domains. Label unapproved boxes
`Candidate` or `Proposed`. Generate and inspect the saved Figure 2.

Task 5 — Iterate with the researcher
Present the map, candidate bounds, basin/network evidence and open questions to
the researcher. Revise the river selection, domains, viewing extent or figure
settings in response. Distinguish a change to an analysis-domain value from a
change that only alters the map viewport. Repeat as needed; do not set a fixed
number of review rounds or mark scientific domain choices final before the
researcher approves them.

Task 6 — Save the approved design reproducibly
After researcher approval, update the event's `02_analysis_domain_design.md`
with the selection rationale, evidence, limitations and remaining questions.
Record the spatial and temporal handoff for later steps in
`metadata/domain_selection.json`, distinguishing approved choices from
candidates and undecided values. Save event-specific map display settings in
metadata files such as `metadata/event_figure_settings.json` and
`metadata/event_map_extents.csv`. Provide `f02-analysis_domain.sh` so the final
Figure 2 can be regenerated from those tracked settings; keep it focused on
configuration and workflow orchestration. Preserve only the final reviewed
Figure unless intermediate outputs have a specific documentation purpose.

Step 2 does not acquire satellite data or run CaMa-Flood. Later steps may
reconsider the domains if actual scene footprints, valid-observation masks,
forcing coverage or model boundary requirements provide new evidence.

At completion, summarize the map/version examined, basins and network paths
verified, proposed and approved bounds, review decisions, files created,
commands and checks run, and unresolved questions. Do not claim scientific
validation based only on successful figure generation.
```

## Expected outputs and human review

| Output | Role |
| --- | --- |
| `02_analysis_domain_design.md` | Domain rationale, evidence and scientific caveats |
| `metadata/domain_selection.json` | Spatial and temporal handoff to later steps |
| `metadata/event_figure_settings.json` and related metadata | Event-specific map display settings |
| `f02-analysis_domain.sh` | Reproducible Figure 2 entry point |
| `figure/f02-analysis_domain_design.png` | Reviewed simulation/observation domain map |

The researcher reviews whether the simulation window includes the necessary
upstream area and outlet; whether natural watersheds and model routing groups
are distinguished correctly; whether satellite-analysis candidates fit the
research question; whether the three extents are clearly distinguished; and
whether rationale, uncertainty and handoff settings are recorded. Step 2
selects a documented spatial design for later work, not a guarantee of complete
satellite coverage or final model boundary conditions.

Tutorial 11 already contains a provisional Rhine 2021 Step 2 example. This
procedure is for future events and must not be executed in Tutorial 11 to
recreate its existing design.

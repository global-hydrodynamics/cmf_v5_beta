# p02 — Analysis Domain Design

## Workflow Summary

### Inputs
- Step 1 Survey Report, `metadata/01_impact_locations.csv`, and Figure 1
- Selected CaMa-Flood map/version, network layers, and available gauge data

### Tasks
- Trace target reaches and upstream networks from `basin`, `uparea`, and `nextxy`.
- Propose distinct simulation, satellite-analysis, and map-viewing extents; create Figure 2.

### Outputs
- `AI_survey_report/02_analysis_domain_design.md`
- `AI_work_report/02_domain_design.md`
- `metadata/02_domain_selection.json` and figure settings
- `figure/f02-analysis_domain_design.png` and `plot_script/f02-analysis_domain.sh`

## Human Instructions

Give the agent the event directory, Step 1 outputs, selected CaMa-Flood map/version, and any additional target reaches or gauges. You do not need to provide Basin IDs or initial bboxes. Keep other events separate from Tutorial 11's Rhine-specific sample.

## Example AI Agent Prompt

```text
Design Step 2 spatial and temporal domains for this event evaluation.

Event and objective: [EVENT / RESEARCH PURPOSE]
Event directory: [PATH]
CaMa-Flood map/version: [MAP NAME, VERSION, PATH]
Additional target reaches/gauges: [OPTIONAL]

Read the Step 1 Survey Report, impact CSV and Figure 1. Use the actual selected
map; do not transfer Rhine 2021 IDs or extents. Separate verified facts,
interpretation, proposed settings and open questions.

1. Relate reported rivers, localities and gauges to the map. Inspect available
   `basin`, `uparea` and `nextxy` information to identify routing groups,
   upstream contributing networks, downstream outlets and neighboring groups.
   Derive Basin IDs from this map. A model routing group need not equal a
   natural watershed. If connectivity or the full contributing area cannot be
   established, document that limitation instead of guessing.
2. Propose three distinct extents, in west/south/east/north order:
   - Simulation domain: contains the target river's required upstream
     contributing area, routed network and downstream outlet, with justified
     boundary margin. Do not define it around damage points alone or minimize
     its size as an objective.
   - Satellite analysis domain: one or more candidate observation areas based
     on impacts, reaches and research purpose. Later acquisition/valid-support
     evidence may change them.
   - Map viewing extent: the Figure viewport only; it does not define either
     analysis domain.
3. Create and run `plot_script/f02-analysis_domain.sh`; use a suitable existing map
   renderer. Show river network, relevant routing groups, Figure 1 impacts,
   confirmed observation sites and distinctly labelled proposed domain boxes.
   Use a viewport broad enough to explain the geographic setting and inspect
   the saved figure.
4. Save findings, map evidence, candidate ranges, reasons and unresolved
   questions in `AI_survey_report/02_analysis_domain_design.md`; record actual
   actions and checks in `AI_work_report/02_domain_design.md`. Store the
   machine-readable handoff in `metadata/02_domain_selection.json` with
   `proposed` or `undecided` states as appropriate, and save display settings
   under `metadata/`. Ensure the same f02 Shell regenerates Figure 2.
5. Hand off the domain and timing settings to Step 3. Do not run CaMa-Flood or
   acquire satellite data.

Complete initial investigation and candidate outputs before presenting them;
Human review is recommended, not an execution gate. Feedback updates the same
files. Status fields never block scripts when required values are present.
Do not claim hydrologic validation from a rendered map or publish to the Gallery
without separate authorization.
```

## Researcher review

Review whether the model domain contains the needed upstream/outlet network, whether routing groups are being interpreted correctly, whether observation bounds match the evaluation purpose, and whether the Figure communicates the difference between analysis domains and viewport. A candidate design may pass to Step 3 without Human response.

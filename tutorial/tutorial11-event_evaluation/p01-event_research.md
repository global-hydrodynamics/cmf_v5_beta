# p01 — Event Research Agent Workflow

## Purpose

Step 1 establishes an evidence-based understanding of a flood event: its
reported timing and development, major rivers, affected places and candidate
observations. It creates a geographic impact inventory and Figure 1 to support
Step 2. Step 1 does not select CaMa-Flood Basin IDs or finalize analysis
domains.

## Human instructions

Provide the AI agent with:

1. The flood event name, region and year (or known event dates).
2. The research objective, such as evaluating simulated flood extent, river
discharge, or both.

Run this workflow in a new event-specific directory, separate from Tutorial
11. Tutorial 11's Rhine 2021 files are a worked example; do not edit or replace
them. Reuse their structure and suitable Visualization Gallery methods.

## Example AI agent prompt

Copy and complete the fields below, then give the prompt to the agent.

```text
Prepare Step 1 of a CaMa-Flood flood-event evaluation.

Flood event: [EVENT NAME, REGION, YEAR]
Research objective: [RESEARCH OBJECTIVE]

Work only in the current event-specific directory. Treat Tutorial 11's Rhine
2021 materials as examples; do not edit them or transfer their event-specific
facts, coordinates, rivers, styles or settings. Reuse an appropriate existing
Visualization Gallery method and the current visualization conventions. Do not
build an unnecessary plotting framework.

Complete the following workflow:

1. Research the event using traceable scientific papers, public authority
   reports, and reliable news or situation reports. Confirm each source exists
   and supports the claim. Summarize event dates and documented development,
   major rivers/watersheds, affected places and reported impacts, hydrologic
   characteristics, and candidate observations with known limits. Cite
   sources close to claims. Separate sourced facts, interpretation and
   uncertainty; do not invent or overstate evidence.
2. Create `01_flood_event_overview.md` with the researched event summary,
   citations and unresolved information.
3. Create `metadata/01_impact_locations.csv`, using Tutorial 11's CSV as a
   schema example. Include locality, river/system, country/region, concise
   source-reported impact, coordinates, source/citation and coordinate
   confidence where available. Distinguish approximate town/locality centres
   from surveyed damage locations and observed inundation boundaries. Do not
   infer precise locations or impact severity from a marker.
4. Prepare `f01-reported_flood_impacts.sh` using an existing suitable map
   renderer. Keep event points and display settings in event-local metadata,
   not shared plotting code. The script must regenerate
   `figure/f01-reported_flood_impacts.png` from the saved CSV/settings.
   Include OSM attribution where applicable.
5. Run the Figure script and inspect the saved image for geographic placement,
   labels, extent, legibility and consistency with cited evidence. Fix issues
   within scope and rerun as needed. If a required dependency or data source is
   unavailable, report the limitation instead of claiming a successful visual
   review.
6. Present the overview, source basis, CSV, Figure and remaining uncertainties
   to the researcher. Ask for specific scientific or location decisions where
   evidence is insufficient. Revise the research outputs or Figure when the
   researcher gives feedback; repeat review as needed, with no fixed iteration
   count. Do not treat silence as scientific approval.
7. After the researcher accepts the Step 1 result, preserve the reviewed
   overview, CSV, Figure, event-local settings and reproducible Figure Shell.
   Hand off major rivers, impacted areas, documented timing, candidate
   satellite-search period/observations and unresolved questions to Step 2.

Do not choose or finalize CaMa-Flood Basin IDs, simulation domains or satellite
analysis domains in Step 1. Do not present candidate observations as acquired
or validated. Literature research itself need not be reproducible by Shell;
the impact map must be reproducible from its saved inputs and settings. Do not
publish to the Visualization Gallery unless separately authorized.

At completion, report sources checked, files created, commands/checks run,
researcher review status and remaining uncertainty. Do not claim scientific
validation from successful plotting alone.
```

## Expected outputs and human review

| Output | Role |
| --- | --- |
| `01_flood_event_overview.md` | Event background, evidence and references |
| `metadata/01_impact_locations.csv` | Geographic inventory of reported impacts |
| `f01-reported_flood_impacts.sh` | Reproducible Figure 1 entry point |
| `figure/f01-reported_flood_impacts.png` | Map of reported-impact localities |

The agent performs the research, prepares and runs the mapping workflow, and
presents the evidence for review. The researcher checks source accuracy,
impact selection, coordinate confidence and the Figure, then decides whether
the result is accepted and Step 2 may begin. Tutorial 11 already contains a
Step 1 sample for the July 2021 western European floods; this Prompt is for
future events and must not be run to recreate it.

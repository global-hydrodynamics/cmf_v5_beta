# p01 — Event Research

## Workflow Summary

### Inputs
- Flood event name, region and year or known dates
- Research purpose (for example, evaluating flood extent or discharge)

### Tasks
- Review traceable sources, summarize the event and reported impacts, and prepare Figure 1.
- Save a georeferenced impact inventory and provide an evidence-based handoff to Step 2.

### Outputs
- `AI_survey_report/01_flood_event_overview.md`
- `AI_work_report/01_event_research.md`
- `metadata/01_impact_locations.csv`
- `metadata/01_reported_flood_timing.csv` (separate time/location evidence ledger)
- `figure/f01-reported_flood_impacts.png` and `plot_script/f01-reported_flood_impacts.sh`

## Human Instructions

Give the AI agent the event identity and research objective. Run this workflow in a new event-specific directory, not in the Tutorial 11 Rhine example. Human review is recommended; the first complete result must be usable by Step 2 without waiting for a review.

## Example AI Agent Prompt

```text
Prepare Step 1 event research for a CaMa-Flood flood-event evaluation.

Event: [EVENT NAME, REGION, YEAR / KNOWN DATES]
Research objective: [RESEARCH OBJECTIVE]
Event directory: [PATH]

Work only in the event directory. Treat Tutorial 11's Rhine 2021 materials as
examples; do not copy their geographic facts, observations, coordinates, or
settings. Confirm that cited sources exist and support the statements. Separate
source-reported facts, interpretations, and uncertainty.

1. Review scientific papers, public authority reports, and reliable
   contemporaneous reports. Summarize timing and development, major rivers and
   watersheds, affected localities and reported impacts, hydrologic features,
   and candidate observations. Cite sources close to claims and do not invent
   details or make the locality list appear exhaustive without evidence.
2. Create `metadata/01_impact_locations.csv` from confirmed reported locations.
   Record names, river/system, country, concise reported impact, coordinates,
   coordinate source/confidence, event date if known, and citation/URL. Distinguish
   approximate town centres from surveyed damage locations and flood boundaries.
3. Create `metadata/01_reported_flood_timing.csv` with one record per
   source-supported timing/location combination. Distinguish water-level peak,
   discharge peak, inundation maximum, onset, impact report, and response time.
   Preserve original time text and timezone; populate UTC only when the source
   time basis is established. Leave unknown times blank. Keep coordinate
   confidence separate from timing confidence. Do not assign a nearby gauge
   peak to a town without evidence. Keep `ai_notes` as the last CSV column.
4. Create and run `plot_script/f01-reported_flood_impacts.sh` using a suitable existing
   Visualization method. Produce `figure/f01-reported_flood_impacts.png` with
   OSM where available, river context, labelled localities, and attribution.
   If timing is added to a legend, label it as reported gauge/river context and
   avoid implying that it is the exact impact or peak time for every locality.
   Inspect the saved figure; report failures instead of claiming visual review.
5. Create `AI_survey_report/01_flood_event_overview.md` for the researcher and
   `AI_work_report/01_event_research.md` for reproducibility and handoff. The
   Survey Report explains findings, sources, the figure, uncertainty and next
   research decisions. The Work Report records actual inputs, commands,
   generated files, checks and unresolved technical work. Do not present this
   retrospective example-report task as a new literature search.
5. Hand off major rivers, affected areas, timing, candidate observation periods,
   and unresolved questions to Step 2. Do not select CaMa-Flood Basin IDs or
   finalize simulation/satellite domains in Step 1.

Complete the first run without waiting for a Human response. Use `proposed` for
unreviewed recommendations where supported; it is descriptive metadata, not an
execution gate. If the researcher gives feedback, update the same files and
rerun affected work; do not create `_v2` or `_final` files. Do not publish to
the Visualization Gallery without separate authorization.
```

## Completion and review

The agent should report findings, sources, the impact inventory and Figure, plus uncertainty. Researcher review is recommended but not required for Step 2 to consume complete outputs. Literature research itself need not be reproducible by Shell; the map must be reproducible from the saved CSV/settings and `f01` entry point. For Tutorial 11, use the retained Rhine sample and its reconstructed Survey/Work Reports; do not rerun this Prompt there.

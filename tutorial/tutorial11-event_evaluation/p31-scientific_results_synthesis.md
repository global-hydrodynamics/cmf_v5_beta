# Step 31 — Scientific Results Synthesis

### How to Use This Workflow

**Rhine 2021:** Use the current research objectives, individual Step reports
and preservation settings below. Supply the entire Markdown file as an
attachment or copy its full content; preserve previous synthesis before any
new writing and respect its exclusion from the source material.

**Another event:** Review the event directory/objectives, available completed
Steps, scientific metadata/figures and report destinations referenced below.
Verify source availability, scientific uncertainties, previous-report preservation
and document-conversion dependencies; do not import Rhine findings or assume
that earlier completion applies to the new event. Give the entire updated file
to the agent. Reuse only the writing workflow, with no new scientific processing
and no claim of blinded independence when earlier context has been exposed.

The numbered Agent Workflow Prompt is part of the full document, including
its Workflow Summary and scope; do not supply a partial extract.

## Workflow Summary

- **Inputs:** Current research objectives and workflow in `README.md`; individual
  completed Steps 01–24 Survey Reports; existing scientific figures and relevant
  metadata/summary tables; individual Work Reports when execution, provenance or
  a scientific uncertainty needs clarification.
- **Tasks:** Select consequential findings; connect related Steps in research
  order; distinguish results, interpretation, hypotheses and future work; check
  important quantities and figure references; write a substantial English
  scientific synthesis and convert that Markdown to an editable Word report.
- **Outputs:** `AI_survey_report/00_scientific_results.md`,
  `AI_survey_report/00_scientific_results.docx`, and
  `AI_work_report/31_scientific_results_synthesis.md`.
- **Scope and checks:** Documentation-focused L0–L1 under the repository's
  `cama-development` and `large-model-refactoring` Skills. No new acquisition,
  simulation, scientific calculation, figure regeneration or input-version/SHA
  reconciliation. Step31 is synthesis, not an additional flood analysis.

## Reusable Agent Workflow Prompt

### 1. Establish the evidence and preserve earlier synthesis

Read the applicable AGENTS files, current process specification and relevant
Skills. Use the current event and actual directory structure; do not hard-code
Rhine findings or this first execution's conclusions into these instructions.

Inspect the existence of `AI_survey_report/00_scientific_results.md` and
`AI_survey_report/00_scientific_results_en.md` before writing. Preserve an
existing `_en.md` without any modification. If only the primary `.md` contains
an earlier synthesis, preserve an exact copy as `_en.md` first. If both contain
previous reports, preserve both and identify their roles before replacing the
primary output; do not overwrite the comparison copy or assume equivalence.
Use the established preservation mechanism or an untracked exact backup when
needed, and record its location. Verify preservation at completion.

After preservation, exclude previous integrated scientific reports and the
workflow/Human–AI synthesis reports from the writing sources. Do not copy their
prose, structure or conclusions. Do not conduct an old/new comparison. If prior
conversation context already exposed an earlier synthesis, disclose that limit
in the Work Report: fresh file sourcing is not a blinded independence test.

### 2. Read and select scientific evidence

Read the research objectives and all available individual Survey Reports from
completed Steps01–24. Determine which results answer the research questions and
which are proposals, superseded findings or operational evidence. Consult
relevant metadata and individual Work Reports only as needed to clarify major
numbers, execution state, provenance or uncertainty. Do not rerun analyses to
fill gaps. Record material source discrepancies without silently resolving them.

Select important event evidence, observation coverage and definitions, experiment
conditions, modeled behavior, comparisons, and cross-Step findings. Retain
spatial and temporal support, masks, physical units, initial conditions and
other methodological details affecting interpretation. Exclude routine file
management, installation, download commands, implementation and debugging.

### 3. Plan a coherent scientific argument

Follow the research progression rather than concatenating individual reports.
Combine related Steps and explain how earlier evidence enables or constrains
later interpretation. For example, event context and region; observations;
experiment; simulated dynamics; discharge/timing; inundation; integrated
interpretation; conclusions and future research can form a useful sequence.
Adapt the sections to the evidence; do not impose a fixed number or reuse an
older integrated report's outline.

The report must be self-contained for flood-model researchers. Explain what was
investigated, what was achieved and learned, and why it matters. Give scientific
results priority over operational history. Use enough detail and existing
figures to convey the findings without an arbitrary length limit.

### 4. Write and substantiate the report

Write clear academic English in `AI_survey_report/00_scientific_results.md`.
Use “Flood Event Evaluation Tutorial” in scientific prose. Explain the overall
Human–AI research context once; do not invent roles, productivity effects or
review approvals. Separate exploratory comparisons from formal skill evaluation.

For each important conclusion, distinguish source-supported results from
interpretations, testable hypotheses and future work. Connect findings across
Steps, including observation availability, spatial representation and temporal
support. State substantive uncertainty where needed without repetitive defensive
phrasing. Do not invent numbers, bibliographic details or completed evaluations.

Use existing figures generously where they serve the argument. Embed the original
files with valid relative paths, captions and a discussion of their scientific
meaning. Keep original image resolution; do not duplicate or regenerate images.
Retain useful scientific tables in editable form. Use readable significant
figures while preserving essential counts and experiment settings. Link to
supporting individual Survey Reports/metadata and verified source publications;
technical execution evidence belongs in the Work Report.

### 5. Convert the new Markdown to Word

The newly written Markdown is the sole content source for
`AI_survey_report/00_scientific_results.docx`. Use an available small conversion
workflow and the applicable document-authoring Skill. No `s31` or `f31` script
is needed and no document framework should be added to the repository.

Keep the title, heading hierarchy, scientific prose, tables, captions and
references equivalent. Embed images at original resolution and use readable
academic typography. Preserve source links where practicable. Keep temporary
conversion/render files outside the report directory. Render and visually
inspect the document when tools are available, following the Skill's review
requirements; report any unavailable checks explicitly.

### 6. Verify, record and hand off

Check major numbers against their actual source reports or metadata, local
links and figures, results/hypothesis distinctions, and correspondence of the
Word text/tables/embedded images with Markdown. Check the changed-file scope:
scientific software, configurations, original observations/model outputs and
figures must remain unchanged. No numerical regression suite is needed.

Write `AI_work_report/31_scientific_results_synthesis.md`: source reports,
selected themes/figures, synthesis decisions, consistency checks, discrepancies,
Markdown/Word outputs, preservation outcome, conversion and visual-QA results.
Update the existing chronological development log and required repository
records without rewriting history. Follow current branch/commit policy.

Stop after this synthesis and its checks. Leave comparison with the earlier
report to the researcher. Do not revise unrelated Steps or generate the other
two synthesis reports. Report outputs, figure count, scientific themes, actual
checks and remaining limitations concisely.

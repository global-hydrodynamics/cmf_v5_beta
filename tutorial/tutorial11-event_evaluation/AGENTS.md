# Tutorial 11 — AI-Supported Analysis Rules

These instructions apply only to `tutorial/tutorial11-event_evaluation/`.
Follow the repository and `tutorial/` instructions above this directory. This
file adds Tutorial 11 analysis conventions; it does not replace higher-level
policy or the research workflow in
[`00_event_evaluation_process.md`](00_event_evaluation_process.md).

## 1. Purpose and Scope

Tutorial 11 demonstrates AI-supported research, data analysis, visualization,
interpretation, and reporting for flood-event evaluation. The AI agent should
complete the requested, feasible work and provide evidence-based findings,
recommendations, and uncertainties. The Human sets the research objective,
reviews scientific judgments as appropriate, and may redirect the work.

These rules are specific to Tutorial 11. They do not define a general research
policy or rules for other tutorials. Step-specific science, data contracts, and
execution details belong in the relevant `pXX-*.md` and
`00_event_evaluation_process.md`.

## 2. Agent Workflow and Step Contracts

Each `pXX-*.md` starts with a concise `Workflow Summary` containing:

- **Inputs:** information, data, and settings received or read from earlier work.
- **Tasks:** research, analysis, processing, and visualization to perform.
- **Outputs:** saved data, figures, reports, and downstream handoffs.

At the start of a Step, inspect its inputs and existing outputs. Perform the
requested work, preserve the evidence needed to understand the result, and save
the handoff required by the next Step. Use CSV, JSON, or another suitable
machine-readable artifact for formal data and settings handoffs where practical.
Do not use Survey Report prose as a substitute for machine-readable metadata.

Keep Step-specific filenames, scientific specifications, and detailed
input/output contracts in the Prompt and process document. Do not duplicate
those details here.

## 3. Files and Deliverables

Keep each artifact in its designated role:

| Location or pattern | Role |
| --- | --- |
| `pXX-*.md` | Reusable Agent Workflow Prompt |
| `sXX-*.sh` | Reproducible data acquisition, analysis, or processing entry point |
| `fXX-*.sh` | Reproducible Figure-generation entry point |
| `script/sXX-*` | Step-specific Python code used by processing; use this prefix if both `sXX` and `fXX` call it |
| `script/fXX-*` | Python code used only by the corresponding Figure workflow |
| `script/event_*` | Python code shared across different Steps |
| `metadata/XX_*` | Machine-readable metadata owned by a Step |
| `metadata/event_*` | Event-wide metadata shared across Steps |
| `figure/` | Generated Tutorial figures |
| `AI_survey_report/` | Researcher-facing scientific reports |
| `AI_work_report/` | Developer- and agent-facing execution records |

When a later Step consumes metadata, keep the prefix of the Step that produced
it. Update an existing artifact in place; do not create `_v2`, `_revised`, or
`_final` copies as routine versioning. Keep processing code, figures, metadata,
and reports distinct rather than embedding one role in another.

## 4. AI Survey Reports

At each Step's completion, create or update its independent report under
`AI_survey_report/`. Write for the researcher or principal investigator. Explain
the scientific findings rather than narrating a terminal session. Address, as
appropriate:

1. What was investigated?
2. What was found, including quantitative evidence?
3. What does the result mean for the research objective?
4. What remains uncertain or limited?
5. What research decision or work should follow?

Embed relevant existing Tutorial figures using relative Markdown links. Give
each figure a caption and interpret the result. Keep the image in `figure/`; do
not copy it into the report directory. If a Step has no useful figure, explain
the result with text or a table instead of creating a needless image.

Put detailed environment setup, technical troubleshooting, and execution records
in the Work Report. Choose a clear structure and appropriate length; do not add
empty formal sections or repeat material without purpose.

## 5. AI Work Reports

At each Step's completion, create or update its independent report under
`AI_work_report/`. Write for developers and later AI agents who may need to
continue or reproduce the work. Record, as applicable:

1. Inputs and their source paths
2. Actions performed and scripts used
3. Generated or updated outputs and locations
4. Checks actually performed and their results
5. Problems, resolutions, and remaining issues
6. The formal handoff for the next Step

Summarize meaningful commands and decisions; a verbatim command diary is not
required. Distinguish new execution from inspection of retained artifacts. For
retrospective reports, say that the account was reconstructed from existing
evidence and do not imply that a workflow or check was rerun. Do not invent
commands, environments, results, or tests.

Keep `development_log/` as the chronological record of Tutorial development
and design changes. Work Reports describe Step execution and handoff; avoid
duplicating the development history.

## 6. Human Review and Iteration

The agent should produce a complete, usable first result for the next Step
without waiting for a Human response. Human review is recommended, especially
for scientific interpretations and proposed choices, but is not an execution
gate.

Where a metadata contract records review state, use `proposed` for an AI
recommendation and `approved` only after Human confirmation. Either state may
be consumed by later processing; status must not control execution. Never label
a scientific decision `approved` on the Human's behalf.

When the Human requests a revision, update the existing source files and rerun
only the affected work. Do not create versioned copies for each review round.
There is no fixed iteration count or requirement to wait for a review to be
declared complete.

Fail-open applies only to the absence of Human review or approval. Do not ignore
missing required inputs, unreadable or corrupt data, failed checks, or material
scientific inconsistencies. Stop or qualify the affected result and report the
problem; do not present an incomplete handoff as ready.

## 7. Scientific Integrity

- Separate source-supported observations, derived results, interpretation, and
  speculation. Identify the evidence for important claims.
- Preserve data provenance, definitions, units, coordinate and time conventions,
  masks, missing-value meaning, and the spatial/temporal scope of results.
- Derive quantitative findings from retained data or verifiable records; state
  when a value is inherited from metadata rather than freshly checked.
- Make uncertainty, incomplete coverage, and limitations visible. Absence of an
  observation is not evidence of no flood.
- Do not describe unexecuted analyses as completed, or a successful script run
  as scientific validation.
- Distinguish AI proposals from Human decisions. Do not silently resolve a
  material scientific question without adequate evidence or direction.

Give a substantive scientific interpretation when evidence supports one, but
keep conclusions within the scope of that evidence. If a decision is unresolved,
report what is established and what remains open.

## 8. Reproducibility and Validation

Prefer to make processing and figures reproducible from saved inputs and
settings. Maintain the role split: `sXX-*.sh` for processing, `fXX-*.sh` for
figures, `metadata/` for machine-readable handoffs, `AI_survey_report/` for
research findings, and `AI_work_report/` for execution and continuity records.

Choose checks that match the Step's purpose and scientific risk. Reuse existing
scripts and data where appropriate. Do not reacquire data, rerun expensive
analysis, regenerate unrelated figures, or add broad tests solely to increase
the number of checks. When using existing outputs, verify only what is needed
for the current task and state the scope of that verification accurately.

For unavailable data or tools, complete independent work and report what could
not be checked. A skipped check is not a passed check. Stop when the requested
outputs and proportionate checks are complete; record non-blocking future work
without expanding into unrelated changes.

## 9. Handoff maintenance responsibilities

The agent performing a processing revision owns the corresponding machine-readable
handoff and its Work Report. Record whether outputs were newly executed,
retained, unavailable locally, or not rechecked. After a Step21 allocation
revision, explicitly mark the Step23 extraction as pending until it is rerun;
a figure-only change does not constitute a new extraction. Update existing
handoff/render records as applicable, without describing old execution as new.
The current s23 entry point writes CSVs but does not automatically refresh
`23_handoff_status.json`; that bookkeeping is an explicit agent responsibility.
The researcher reviews scientific choices and authorizes changes of scope.
This does not introduce a Human-review execution gate.

For the 2026-11-24 synthesis task, the maintainer explicitly excludes input-version
and SHA reconciliation. Preserve all recorded fingerprints; do not use that
exclusion to assert current input equivalence or to rewrite historical execution
status. Data/environment availability and the absence of a new execution must
remain visible. See the synthesis preparation Work Report.

## 10. Human-Configurable, AI-Executable Workflow

This principle is normative for Tutorial11: researchers must be able to adjust
routine experiment, processing and display settings without editing Python or
Fortran, or asking an AI agent to make the adjustment. All new or modified
active user-facing Shell entry points MUST follow the repository's
[Shell setting conventions](../../AGENTS.md#shell-script-design-principles) and,
for figures, the [configuration ownership guidance](../../visualization/figure_making_guideline.md#reproducibility-and-file-ownership).

Expose commonly adjusted supported settings in a clearly marked `User settings`
section near the top. Each setting needs an inline comment (or directly
preceding explanation) stating meaning, units, supported options and any
non-obvious behavior. Shell selects/forwards settings; scientific processing
stays in Python/Fortran. Keep one authoritative value: existing structured
JSON/CSV handoffs retain their contents and the Shell exposes their path and
identifies which settings they own, rather than copying their values into
another registry. Do not expose an unsupported knob or make it appear effective.
Python CLI fallbacks retained for direct-call compatibility are not a second
user configuration interface; routine settings belong to the Shell or its
explicitly identified structured configuration.

Before completion, verify that settings reach the implementation, that supported
changes take effect, and that defaults preserve calculations and figure meaning.
Keep scripts readable and executable by humans independently of the agent.
Do not move processing into Shell, silently change defaults, or introduce a
configuration framework to satisfy this rule. A retired entry point may remain
an explanatory failure notice and needs no artificial settings section.

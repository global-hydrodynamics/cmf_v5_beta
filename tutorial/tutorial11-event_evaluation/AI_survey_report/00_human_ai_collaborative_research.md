# Human–AI Collaborative Research Workflow — Tutorial11 Case Study

## Purpose and evidence

This is a qualitative account of the Tutorial11 research workflow as documented
through 2026-11-24. Evidence consists of the [Step Work Reports](../AI_work_report/),
[development history](../development_log/development_log.md), retained Prompts,
metadata and linked [repository research records](../../../research/README.md).
Some early Work Reports explicitly reconstruct earlier activity; they are not
contemporaneous logs of a repeated execution. This synthesis does not infer
unrecorded conversations or independently verify external scientific sources.
The current task excludes input-version/SHA reconciliation and all new analyses.

The case demonstrates a useful division of responsibility and several concrete
revision loops. It does not measure productivity gains or prove that AI improves
research accuracy relative to another method.

## Roles, authority and contracts

| Role/artifact | Responsibility in the documented workflow | Boundary |
| --- | --- | --- |
| Researcher/maintainer | Objective, event constraints, important scientific choices and scope | AI recommendations are not Human approval |
| AI agent | Inspect evidence; implement authorized processing; create handoffs, Figures and reports | Successful execution is not scientific validation |
| Step Prompt | State inputs, tasks, deliverables and verification scope | A reusable instruction is not an execution record |
| Metadata | Carry identities, settings, allocations, states and data paths | `proposed` describes review state, not scientific truth |
| Survey Report | Explain findings, interpretation, uncertainty and implications | Must not inflate operational checks into model skill |
| Work Report | Identify actual inputs/actions/outputs/checks and handoff | Distinguish new execution from retained evidence |
| Development/research records | Preserve decisions, changes, failures and evidence | Do not manufacture missing metrics or private discussion history |

[Tutorial rules](../AGENTS.md) make Human review recommended rather than a
program gate. That permits a complete initial result and independent progress,
but does not waive missing/corrupt inputs, unresolved material science, or
repository authorization boundaries. The researcher can accept, revise or
redirect scientific choices; the agent must preserve the distinction between
proposal, authorized procedure and established scientific finding.

## Documented collaboration and revision episodes

| Episode | Researcher direction and agent response | Preserved lesson |
| --- | --- | --- |
| Native GFM workflow and later organization | Acquire one morning pass, keep raw classes and validity; later organize acquisition/classification/crops as Step3 | Keep observation identity, masks and processing state in explicit handoffs; the old3sec branch is not the current1min workflow |
| Domain and experiment revision | Distinguish outer cell edges from centers; extend forcing/run through July31 | Period, grid and run-directory changes must propagate to Prompt, metadata and downstream records |
| Tributary allocation review | Replace containing-cell assumptions with direct catmxy and reviewed one-step Ahr proxies | Human intervention can resolve the procedure while exact reach support remains scientifically uncertain |
| Timing re-extraction | Rerun Step23 after final allocations; preserve report IDs and shared-series caveats | A changed allocation invalidates dependent extraction; a finished plot is not a freshness check |
| Figure23b interpretation | Clarify that filled/hollow diamonds show observation availability, not timing agreement | Visual encoding can imply a scientific claim; explicit feedback corrects the interpretation without changing analysis |
| Final assessment scope | Put interpretation in Step24 and cancel a separate Step25 | Keep computation, visualization and scientific interpretation connected; do not invent another analysis to complete a report |

These episodes are supported by the [Step21](../AI_work_report/21_gauge_allocation.md),
[Step23](../AI_work_report/23_impact_timing_comparison.md) and
[Step24](../AI_work_report/24_inundation_downscaling.md) Work Reports and the
chronological log. They are case observations, not controlled comparisons of
Human-only, AI-only or collaborative research.

## What works well

The separation of Prompt, machine-readable handoff, scientific Survey and
technical Work Report makes it possible to ask different questions of the same
Step. The event ledger preserves missing timing instead of inventing UTC values.
Allocation metadata retains geographic, direct and final cells plus prior review
notes, so a scientific correction need not erase its history. Work Reports
state when analyses were not rerun. KG-0019 and KG-0039 preserve unresolved
questions rather than treating a maintainer's procedural choice as a scientific
resolution. Figure-only revisions are distinguishable from processing changes.

This design is effective when each artifact is updated consistently. It also
helps constrain AI autonomy: complete the authorized first result, explain
limitations, and carry forward unresolved questions without fabricating an
answer or creating an unnecessary new workflow stage.

## Weaknesses and bounded improvements

Old experiment details survived in Step12–14 Prompts after the31-day execution
was recorded. The current preparation corrects those contracts. A retired
3sec entry point and tests referenced removed code; the entry now explains
retirement, while focused tests target current classification/aggregation.
These are maintenance findings, not evidence that the retained scientific
conclusions are wrong.

A saved handoff status is not automatically current. The existing s23 program
writes the extraction/comparison CSVs but does not refresh its status JSON.
The executing agent therefore owns that bookkeeping and the Work Report;
a Step21 change requires explicit pending/re-executed downstream status.
The [rules](../AGENTS.md#9-handoff-maintenance-responsibilities) now state this
responsibility without a new review gate. Original fingerprints remain intact;
input-version review was excluded from this preparation by Human direction.

Local absence of environments and ignored data limits rerunning the example,
without erasing its recorded history. [Availability metadata](../metadata/event_artifact_availability.csv)
records checked paths and recovery options, not global absence or data validity.
The agent should state that distinction rather than quietly reinstalling,
reacquiring or regenerating results outside the task.

## Limits of this collaboration study

No matched baseline, systematic Human effort measurement, token/cost series,
review acceptance study or independent scientific outcome assessment was
performed. Command runtimes are not total researcher effort. Selective public
summaries and retrospective records cannot reconstruct every decision or
rejected alternative. Unknown quantities must remain unknown; the case cannot
support a percentage time saving, superiority claim or causal accuracy benefit.
A future formal collaboration study would need its own protocol and appropriate
participant/privacy review, not an invented reconstruction from this example.

## Conclusion

Tutorial11 provides an evidence-linked example of researcher-directed AI work:
explicit scientific questions, bounded execution, preserved handoffs, meaningful
Human corrections and qualified interpretation. Its demonstrated contribution
is the organization and inspectability of the research process. The remaining
risk is inconsistency between evolving contracts and retained execution evidence,
not a problem solved simply by adding more agents, gates or documents.
**Step24 is final; Step25 is canceled.** The three synthesis reports summarize
existing work and are not additional numbered scientific Steps.

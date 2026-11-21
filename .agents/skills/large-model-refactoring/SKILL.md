---
name: large-model-refactoring
description: Apply stage- and science-risk-based scope and validation decisions when ChatGPT plans scientific-model work or writes Codex handoffs, and when Codex directly implements or refactors large scientific models.
---

# Large Scientific Model Development

Use this Skill to choose a proportionate amount of investigation, implementation, and validation for a scientific-model task. It complements repository policy; it does not replace approval, safety, scientific review, or project-specific instructions.

## Read the applicable authority

Before planning or editing, follow the repository's current `AGENTS.md`, approved task or issue, and relevant scientific design and test documents. Read only the directly relevant material. Apply a domain-specific Skill as well when one governs the affected component; for example, `cama-visualization` controls visualization conventions while this Skill helps size the work and checks.

Do not copy repository policy into a prompt or this Skill. If a task conflicts with an authoritative rule or lacks an approval required by that rule, state the conflict and pause only the dependent work. In this repository, `AGENTS.md` is authoritative; `docs/ai_development_workflow.md` governs human/AI handoffs and evidence records; `docs/development_and_distribution_design.md` governs package and contribution design. Consult relevant research notes for prior decisions, not as a substitute for current policy.

## Select a development level

Choose the level from the task's actual purpose, not from code size or the number of files. Ordinary feature work and refactoring default to L1.

| Level | Stage | Proportionate default |
| --- | --- | --- |
| **L0** | Exploration or prototype | Minimal execution, a representative visual check, or another check that answers the immediate feasibility question. Keep prototype results distinct from validated production behavior. |
| **L1** | Feature development | Focused functional checks plus a representative real-data case when data is available and the change consumes it. Check only directly affected interfaces and outputs. |
| **L2** | Integration or stabilization | Relevant regression tests and cross-component consistency checks for the integrated scope. |
| **L3** | Release or distribution | Comprehensive validation of reproducibility, compatibility, supported environments, and release contents. |

A task may span levels, but do not silently promote a prototype or feature task to release assurance. Use the level needed for the requested deliverable and report what remains for a later milestone.

## Adjust for scientific risk

Estimate risk by asking whether the change can alter scientific interpretation or model behavior. Consider:

- governing equations, physical assumptions, thresholds, and classification rules;
- numerical methods, stability, conservation, precision, and operation order;
- units, time meaning, calendars, and aggregation;
- grid geometry, coordinate transforms, indexing, array order, and data formats;
- missing values, masks, and the meaning of observed versus unobserved data;
- parallel order, nondeterminism, and reproducibility;
- public interfaces, input compatibility, and restart or output compatibility.

Use targeted evidence for the risks actually touched. A color or layout change normally needs a focused visual review. A data-format conversion needs value/class, metadata, grid, and output checks. A change to equations or numerical schemes may need conservation, stability, and comparison against relevant trusted results even at L1. Do not add unrelated model-wide regression tests merely because scientific software is involved.

As a quick guide, classify the affected contract rather than assigning risk from the task label:

- **Low:** presentation, comments, or non-scientific workflow behavior; check the changed output or path.
- **Moderate:** data conversion, classification, coordinate handling, or file interfaces; check representative values, metadata, and boundary cases.
- **High:** equations, physical assumptions, numerical stability, conservation, or time semantics; identify domain-specific reference evidence and scientific acceptance criteria.

These are prompts for judgment, not fixed test quotas. A high-risk change can justify deeper checks at L1; a low-risk L2 integration task still needs only the relevant integration checks.

## Match effort to the task

Prefer the smallest check that demonstrates the requested behavior at its boundary. Reuse existing fixtures, validators, and representative inputs. Use synthetic data when it isolates a contract that is expensive or impossible to test with real data; do not treat synthetic success as real-data or scientific validation.

Keep implementation scoped to the assigned component and direct dependencies. Do not add generic frameworks, defensive layers, performance benchmarks, broad refactors, or cross-component repairs unless they are needed for acceptance or the task authorizes them. Never weaken a known scientific or safety check to make a task pass.

For unavailable data, runtimes, or tools, complete independent work, run feasible static or synthetic checks, and identify the missing evidence. Do not fabricate results or imply that a skipped test passed.

## Use in ChatGPT planning and handoffs

When asked to design work or write a Codex prompt:

1. State the task outcome and bounded components.
2. Select L0–L3 and briefly justify any increase above the L1 default.
3. Identify scientific risks actually touched and the evidence needed for them.
4. Specify a short list of acceptance checks and explicit exclusions that prevent likely scope creep.
5. Separate verified facts, maintainer decisions, proposals, and unresolved questions.

Leave routine implementation details to Codex. Do not prescribe a test suite, full audit, or exhaustive checklist by default. A prompt should request evidence proportional to risk and stage, not maximum possible assurance. When the researcher asks for an implementation prompt, give Codex the intended outcome, scope, known scientific contracts, acceptance evidence, and explicit exclusions; do not turn every possible edge case into mandatory work.

## Use by Codex during direct implementation

When assigned implementation directly, make the same level and risk decisions before changing files. Respect explicit scope and authorization. Inspect enough to understand the target and immediate dependencies; broaden investigation only when required to avoid a scientific, compatibility, data-loss, or security failure. Convert the acceptance evidence into focused checks, then execute those checks against the actual changed behavior rather than producing a broad audit.

Implement the requested behavior, run the selected checks, and stop when the stated acceptance conditions are met. Record non-blocking findings for a later task rather than fixing neighboring components. If a missing scientific decision blocks correctness, do not guess; continue independent work and raise the decision with its consequence.

## Stop conditions

A task is complete when its requested behavior is implemented, proportionate checks pass or their limits are reported, and required documentation or records are updated. Additional possible improvements do not extend the task automatically.

Classify discoveries as:

- **Blocking:** the requested change cannot be completed safely or correctly without resolving it.
- **Non-blocking:** relevant future work that does not invalidate the current result.

Resolve blocking issues before claiming completion. Report non-blocking work with a concise reason and defer it. Existing repository rules still govern approvals, data preservation, branch use, research records, and publishing.

## Examples

**Compact GFM classification export — L1, low-to-moderate scientific risk.** Check the observed source-code combinations, class precedence, CRS and pixel alignment, representative output values, and file integrity. A small synthetic fixture can cover precedence. Do not require a CaMa-Flood simulation, repeated full regeneration, or unrelated model regression suite.

**River-dynamics algorithm change — L1 or L2, high scientific risk.** Inspect the affected equations and numerical contracts; check conservation, stability, and relevant trusted results. Keep tests focused on the changed dynamics rather than running every unrelated subsystem automatically.

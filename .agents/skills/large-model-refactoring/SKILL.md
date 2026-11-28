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

Choose a level by the guarantee the task is meant to establish, not by code size or test count. Ordinary feature development defaults to L1. Levels define investigation/modification scope and completion evidence; they are independent choices, not automatic stages.

| Level | Purpose | Investigation and modification scope | Validation | Completion |
| --- | --- | --- | --- | --- |
| **L0** | Local fix / exploration | The specified local issue and immediate dependencies. | Static/minimal checks. Runtime validation is not required; explicitly designated L0 tasks follow the stricter root `AGENTS.md` rule. | Local change is complete and unverified behavior is stated for user validation. |
| **L1** | Functional completion | The target function and dependencies directly needed to make it work. | Exercise the target behavior. Use representative real data when available; inspect rendered output for GUI/visualization changes when possible. | The target function works; broader component effects are outside this level. |
| **L2** | Integration / stabilization | The target plus related components plausibly affected through interfaces or data contracts. | Focused integration and regression checks across that impact boundary. | Intended behavior and relevant neighboring contracts are stable within scope. |
| **L3** | Release / distribution | The distributed product, supported environments, and user-facing workflows. | Clean-environment setup, compatibility, package contents, reproducibility, and supported workflows as applicable. | The deliverable and documented supported workflows meet release acceptance. |

**L1 validates the target functionality. L2 validates the impact on related components. L3 validates the distributed product and supported user workflows.** L1 is the functional boundary: do not add general neighboring-feature audits or regression suites automatically. Discoveries outside the target that do not block its completion should be reported and deferred to a later L2 task.

Do not silently promote a prototype or feature task to release assurance. Choose the level needed for the requested deliverable and state what remains for a later milestone.

Large refactorings may group work by purpose: use L0 for bounded local edits, L1 to establish key functions, L2 at a component-integration milestone, and L3 when preparing a release. A task may start or stop at any level; do not repeat L1–L3 after every L0 edit or require every project to pass through all four levels.

## Adjust for scientific risk

Estimate risk by asking whether the change can alter scientific interpretation or model behavior. Consider:

- governing equations, physical assumptions, thresholds, and classification rules;
- numerical methods, stability, conservation, precision, and operation order;
- units, time meaning, calendars, and aggregation;
- grid geometry, coordinate transforms, indexing, array order, and data formats;
- missing values, masks, and the meaning of observed versus unobserved data;
- parallel order, nondeterminism, and reproducibility;
- public interfaces, input compatibility, and restart or output compatibility.

Use targeted evidence for the risks actually touched. A color or layout change normally needs a focused visual review. A data-format conversion needs value/class, metadata, grid, and output checks. A change to equations or numerical schemes may need conservation, stability, or comparison against trusted results even at L1, but keep those checks on the target behavior. Do not add unrelated model-wide regression tests merely because scientific software is involved.

As a quick guide, classify the affected contract rather than assigning risk from the task label:

- **Low:** presentation, comments, or non-scientific workflow behavior; check the changed output or path.
- **Moderate:** data conversion, classification, coordinate handling, or file interfaces; check representative values, metadata, and boundary cases.
- **High:** equations, physical assumptions, numerical stability, conservation, or time semantics; identify domain-specific reference evidence and scientific acceptance criteria.

Scientific risk and Development Level are independent axes: level sets the scope of the guarantee; risk sets the depth needed to support it. High risk can require deeper validation of an L1 target, but does not by itself expand the task to unrelated components. A directly relevant safety or correctness concern must still be resolved at any level. These are prompts for judgment, not fixed test quotas.

## Match effort to the task

Prefer the smallest check that demonstrates the requested level's guarantee. For L1, show that the target behavior works at its boundary; reuse a representative real input when available. Use synthetic data when it isolates a contract that is expensive or impossible to test with real data, and distinguish it from real-data or scientific evidence. L2 adds checks only for related components within the plausible impact boundary. L3 checks the actual distribution and supported workflows.

Keep implementation scoped to the assigned level: target and direct dependencies at L1, related affected components at L2, and the delivered product/user workflow at L3. Do not add generic frameworks, defensive layers, performance benchmarks, broad refactors, or cross-component repairs unless they are needed for acceptance or specifically authorized. Never weaken a known scientific or safety check to make a task pass.

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

When assigned implementation directly, make the same level and risk decisions before changing files. Respect explicit scope and authorization. Inspect enough to understand the target and its level-defined dependencies. At L1, broaden beyond those dependencies only when a blocking correctness, compatibility, data-loss, or security issue prevents the target from working safely; report non-blocking neighboring issues for later L2 work. At L2, inspect the plausible related-component impact boundary. At L3, validate the distributed product and supported user workflows. Execute focused checks for the selected guarantee, not a general audit.

For a task explicitly designated **L0**, follow the authoritative L0 policy in
the repository-root [`AGENTS.md`](../../../AGENTS.md#explicit-l0--local-fix--user-validation):
make the smallest local fix, do not run functional/regression/end-to-end tests,
and do not create tests or fixtures. Functional validation belongs to the
user. A directly detectable syntax or compilation error may be corrected; a
focused syntax check is permitted. If scientific calculations, data integrity,
or established numerical behavior may be affected, explain why L0 is
insufficient and stop before such a risky change.

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

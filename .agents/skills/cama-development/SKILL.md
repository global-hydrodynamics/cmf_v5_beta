---
name: cama-development
description: Route ChatGPT development planning and Codex direct implementation to the current CaMa-Flood repository rules, component guidance, and relevant Skills without duplicating policy.
---

# CaMa-Flood Development Rules Router

Use this Skill for CaMa-Flood v5 development planning, Codex handoffs, and
direct implementation. Its job is to find and apply the right project rules,
not to create a second policy.

For tasks explicitly designated L0, apply the repository-root
[`AGENTS.md` L0 rule](../../../AGENTS.md#explicit-l0--local-fix--user-validation)
and the `large-model-refactoring` Skill: keep the fix local, leave functional
validation to the user, and do not add tests or fixtures.

## Find current authority first

1. Read the repository-root `AGENTS.md`. It controls repository boundaries,
   approval, branch, safety, research-record, commit, and publication rules.
2. Check for `AGENTS.md` files from the repository root down through every
   target directory. Read the applicable instructions; do not assume the root
   file is the only one.
3. Use `docs/development_rules_index.md` to locate component guidance and
   distinguish policy, design specifications, usage guides, plans, and history.
4. Read the task's current design/data contract and the closest component
   README or implementation example. Plans and old research records provide
   context, not automatic proof of current behavior.
5. Consult the project's current GitHub instructions and source when preparing
   ChatGPT advice or handoffs. If a copied/local Skill conflicts with current
   repository rules, use the repository's current rules and identify the
   discrepancy; do not invent a resolution.

Read only enough material to establish task scope, authority, and relevant
contracts. For cross-component work, apply the instructions for each affected
component rather than expanding into a repository-wide audit.

## Route by task

| Work | Read and apply |
| --- | --- |
| Python development across components | `docs/python_design.md` and relevant `docs/python_style.md` sections, plus the owning component guidance below. For a dedicated formatting pass, use Style and the target file; consult Design only for a concrete semantic issue. |
| Model Fortran in `src_main/` | `src_main/AGENTS.md`, `FORTRAN_DESIGN.md`, and the relevant `FORTRAN_STYLE.md` sections. Preserve scientific and runtime contracts. |
| Map or runoff preprocessing | `map/AGENTS.md` or `inp/AGENTS.md`, shared preprocessing conventions, relevant metadata/NetCDF contracts and component README. |
| GOSH sample workflow | `gosh_test/AGENTS.md` and README. Treat its style notes as working recommendations; retain experiment settings and behavior. |
| Tutorial content or workflow | `tutorial/AGENTS.md`, tutorial development/authoring guidance, and the target tutorial's own design and data contract. |
| Tutorial or repository visualization | Also use `cama-visualization`; consult the Gallery and catalog for suitable scientific methods. A tutorial figure does not authorize Gallery publication. |
| Package builder or additional-data selection | `docs/development_and_distribution_design.md`, `package/AGENTS.md`, package README and catalog. Keep repository, external additional data, and generated package distinct. |
| Research record | `research/README.md` and the relevant record template/category; preserve evidence and privacy rules. |

When a task changes multiple areas, combine their applicable instructions. Avoid
applying unrelated component conventions by analogy.

## Combine Skills by responsibility

- **This Skill (`cama-development`)** finds and applies CaMa-Flood-specific
  repository and component rules.
- **`large-model-refactoring`** chooses the amount of investigation and
  validation from the development stage and scientific risk.
- **`cama-visualization`** governs visualization-specific implementation,
  visual/scientific review, and the separate Gallery-publication approval.

Use `large-model-refactoring` for scientific-model implementation or planning
when its stage/risk judgment is useful. Use `cama-visualization` for figures,
visualization projects, catalog/Gallery work, and tutorial figures covered by
its description. Do not invoke every Skill for every task.

## Work loop

### ChatGPT planning and handoffs

Identify the requested outcome, affected component(s), applicable rules,
scientific or compatibility contracts, and the checks needed for acceptance.
Separate verified facts, maintainer decisions, proposals, and open questions.
When useful, use `large-model-refactoring` to size the work and checks, and
`cama-visualization` for visualization tasks. Leave routine coding choices to
Codex; do not turn a bounded task into an exhaustive audit.

### Codex direct implementation

Confirm the current branch/worktree and applicable approval scope as required
by root `AGENTS.md`. Inspect the target and immediate dependencies, follow the
component guidance, make the requested bounded change, then compare the result
with the actual relevant requirements. Run proportionate checks and report
their results and limits. Preserve pre-existing changes. Do not commit, push,
publish, or expand scope unless the task and root policy authorize it.

### Stop

Finish when the requested outcome and proportionate acceptance checks are
complete. Report non-blocking findings for later work instead of fixing
neighboring components. Pause only when a required approval, scientific
decision, or missing input blocks safe completion.

## Short routing examples

1. **Fortran change:** root rules → `src_main/AGENTS.md` → design/style docs;
   add stage/risk decisions from `large-model-refactoring` when appropriate.
2. **Tutorial 11 figure:** root + tutorial guidance + `cama-visualization`;
   inspect related Gallery methods and catalog entries, keep event settings
   separate when appropriate, and do not infer Gallery approval.
3. **Package Builder task:** root + maintained package design + package local
   guide/catalog; do not edit the external additional-data store by default.

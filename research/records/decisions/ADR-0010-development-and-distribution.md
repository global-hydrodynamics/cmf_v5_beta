# ADR-0010: Separate development sources, additional data and generated distribution

- Status: accepted design principles; implementation under development
- Date: 2026-11-15
- Event ID: EV-0477
- Task: DT-0103
- Decision owner: Dai Yamazaki (maintainer)
- Working branch: main, bounded documentation assignment; no commit or push

## Context and evidence

The maintainer supplied `development_and_distribution_design.md` and explicitly requested its installation as a maintained design specification, alignment of current guides, concise external contribution guidance, and research evidence. This public summary records that instruction; it is not a reconstructed transcript. Earlier v4 packaging combined separately maintained source and data through maintainer-specific procedures. Earlier beta discussions emphasized a Git checkout plus optional additional data; the supplied specification now distinguishes the generated complete user product as a third component. Historical research rows and URLs are retained.

## Adopted decisions and rationale

1. Track explicitly approved small Mekong map/runoff inputs in the ordinary map and inp locations. The intended result is that developers can compile and exercise a minimal model test without the full additional data package, rather than depending on maintainer-only data preparation.
2. Separate the GitHub Repository, versioned Package Additional Data, and Distributed Package. The user package is generated from a selected committed revision and data version into a separate destination, without Git history or changes to the source checkout. It is not an independently edited source tree.
3. Do not create a separate GitHub-only input-data directory or duplicate the existing Mekong data. Existing directory/workflow contracts are preferred. The supplied tree is conceptual: actual current forcing names use hyphens and current v5 workflows use gosh_test.
4. Contributors test before PR submission; maintainers can test the unmerged branch independently. A merge into main is not a prerequisite for verification. Component checks and scientific review remain distinct, and official numerical references need independent approval.
5. Prefer trusted contributors, coherent feature-branch diffs, ordinary Git inspection, proportionate tests and review over a custom protection/coordination mechanism. Shared project/agent authorization remains governed by AGENTS; private external experiments do not require dashboard registration.

The specification is [the maintained design](../../../docs/development_and_distribution_design.md), not this history record. [CONTRIBUTING.md](../../../CONTRIBUTING.md) provides the practical workflow; [AGENTS.md](../../../AGENTS.md) owns current development policy.

## Consequences, scope and alternatives

Area: development infrastructure and documentation. Prior constraint: current README and packaging guides still describe v4 and can obscure the executable Mekong inputs already tracked in Git. The change makes the intended products and contribution path discoverable; it does not implement a new package/test environment.

Scientific method change: no. No Fortran, runtime scripts, data, CI, experiments or numerical references are changed. All three product definitions and the original supplied Sections 1–10 are retained, with explicit current-name/status additions. The original roadmap is not represented as completed functionality.

An extra GitHub-only dataset tree would duplicate inputs and is rejected by the maintainer's instruction. Reusing the old v4 packager as the v5 interface would not meet the separate-output, selected-revision requirements; it remains historical, with implementation deferred. Automatically registering or switching old project branches is outside this task.

## Review and remaining decisions

The brief knowledge-gap review identifies the related new acceptance decisions in [KG-0036](../knowledge_gaps/KG-0036.md): official model regression contract, additional-data contract, and generated-package selection/equivalence. These are open before their dependent implementation and do not block documentation. No undocumented scientific rationale is inferred. AI-authored discussion/decision summaries remain subject to maintainer review. Validation is in [VR-0149](../validation_runs/VR-0149.md).

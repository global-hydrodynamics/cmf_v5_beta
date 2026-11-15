# ADR-0011: Retire transitional CI while preserving manual validation

- Status: accepted by explicit maintainer task instruction
- Date: 2026-11-15
- Task: DT-0104; decision event: EV-0482
- Approved working branch: main

## Context and decision

The v4-to-v5 transition workflow built the model and regional tools and checked
selected map/CTL contracts. It was not a full model regression/package suite
or independent scientific validation. The maintainer explicitly instructed
removal of the active workflow configuration, preservation of actual tests
and reference inputs, and no replacement CI in this migration task.

Remove only .github/workflows/map-sample-validation.yml from active GitHub
Actions. Git preserves the old definition. Automated CI is temporarily
disabled pending design of a small, reproducible v5 regression suite. Existing
build, syntax, metadata, CTL and region checks remain available manually;
pre-merge review must report actual executed evidence rather than assume a
CI run occurred.

## Rationale, alternatives and scope

This is a deliberate, maintainer-approved CI reduction rather than an
implicit weakening of tests. Keeping the old transition configuration active
was rejected by the task instruction; replacing it now would exceed scope.
No test program, reference data, model calculation, package assembler or
repository-hosting setting is changed. The obsolete trigger reference to
map/src/map_data_tools/map_metadata.py is documented, not replaced by a new
workflow.

Current authority, active/legacy boundaries and manual commands are in
[the migration audit](../../../docs/migration_consistency_audit.md). Current
development policy remains [AGENTS.md](../../../AGENTS.md). This record
preserves why CI was removed rather than duplicating those instructions.

## Evidence and limits

The definition was present at 8d557898 and its removal is in 9f08956e,
an external commit observed during this task. The agent did not execute
commit or push. Validation and the no-data/no-science-change inventory are
recorded in [VR-0150](../validation_runs/VR-0150.md). Future CI/reference choices
remain separately scoped; [KG-0036](../knowledge_gaps/KG-0036.md) is unchanged.

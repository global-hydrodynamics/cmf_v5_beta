# ADR-0013: Reconcile parallel research-log IDs without losing either history

- Status: accepted bounded integration under maintainer request; summary pending review
- Date: 2026-11-16
- Event: EV-0532
- Working branch: feature/package-builder; no main edits, history rewrite, commit or push

## Context and decision

The maintainer reports parallel university-workstation development on main and
local package-builder development. Both independently allocated DT-0105,
VR-0151 and EV-0486..EV-0491 for different work. Main's Map Explorer records and
feature's runoff-climatology records must both survive.

Preserve main's already-published identifiers. Assign unused canonical IDs to
the feature's runoff records, updating their indexes, report filenames and all
current references consistently. Original IDs remain recoverable in the
unchanged original Git commits; this table is a branch/commit-scoped alias
mapping, not a claim that the main records describe runoff work.

| Original ID on feature/package-builder | Canonical ID after integration |
| --- | --- |
| DT-0105 | DT-0118 |
| VR-0151 | VR-0164 |
| EV-0486 | EV-0526 |
| EV-0487 | EV-0527 |
| EV-0488 | EV-0528 |
| EV-0489 | EV-0529 |
| EV-0490 | EV-0530 |
| EV-0491 | EV-0531 |

## Provenance and compatibility

Original feature commit: `d7f3aa4b2009dc45d7cbc873a6047c0ab48c6140`.
Integrated main commit: `801e2a56fc69e835016c21a23763391542220c2c`.
Main's VR-0151 is retained in full; runoff's report is retained in full under
VR-0164, with identifier references updated. No scientific conclusions, measured
results, original commit references, source data or validation narrative are
removed. Existing ADR-0012 and KG-0037 keep their identifiers.

Integration uses a no-commit merge into the existing feature branch. The merge
commit is deliberately left uncreated for review. Both parents remain intact;
no force-push, reset, stash, new branch or switch is used. Table-row preservation
checks verify every main row and each mapped feature row. Existing historical
link failures are separate from duplicate-ID/conflict resolution.

## Publication authorization — 2026-11-16

EV-0533 records the maintainer's subsequent explicit instruction to commit and
push the reviewed integration. This supersedes only the earlier no-publication
boundary: create the merge commit on feature/package-builder and push that
branch to origin, without updating main or rewriting either parent history.
The remote feature tip was rechecked before publication and matched the local
pre-merge HEAD d7f3aa4b. The integration parent remains main801e2a56.

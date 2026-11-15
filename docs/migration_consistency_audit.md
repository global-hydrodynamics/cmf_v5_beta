# Repository migration consistency audit

Date: 2026-11-15. Task: DT-0104. Approved working branch: main. Owner:
Dai Yamazaki (maintainer); Codex implements. This is a bounded migration
cleanup, not a model refactor, scientific change or package implementation.

## Baseline and authority

The current repository is global-hydrodynamics/cmf_v5_beta; main starts this
task at 8d557898. Fetch completed without changing the checkout. Open Issue/PR
search found no overlapping work. The pre-existing root README edit is kept.
The v4 repository is a separate maintenance/history source and is not modified.
Root src/gosh/adm relocation into legacy and util consolidation into tools
were published in 29b889c4. Current paths are src_main, config, gosh_test and
tools; ordinary map/inp locations remain unchanged.

## Findings and classifications

| Finding | Classification | Action |
| --- | --- | --- |
| Current guides call committed relocation untracked/uncommitted | Fix now | Update current status, design, policy, tools and GOSH guides; label inherited snapshots as history. |
| Source/build guides link missing root src/gosh/adm | Fix now | Link active v5 guides or relocated historical files according to the surrounding meaning; do not redirect historical algorithms to a different implementation. |
| Guide01 active Shell root walks one directory too far; four Python root assignments do likewise | Fix now | Correct only parent traversal; fix the same one-level error in the runnable developer reference Shell script. Its Python reference already resolves the repository correctly and is retained. |
| Current runoff reproduction examples name the old repository directory | Fix now | Use cmf_v5_beta in example paths; keep historical source/units evidence unchanged. |
| Legacy Makefiles, gosh_test/legacy and optional etc scripts retain old roots | Preserve/defer | Keep original source and recipe assumptions. Label support boundaries; no automatic switch to v5 model/configuration. |
| Extraction logs and data provenance name the old machine/repository | Preserve as history | Keep observations, CSVs, NetCDF sample metadata and research rows unchanged. |
| Old branch names, origin/master and genuine v4 Issues/PRs in project records | Preserve as history | Label inherited plans/status; do not re-register branches or rewrite chronology. |
| MPI master-node comments and PTY master variables | Preserve | These are technical roles, not Git refs. |
| p02 f01/f02 unconditionally extract from local annual output | Defer | Existing data dependency, not a renamed-path error. Separate extraction/drawing only in a separately approved workflow task. |
| Guide01/p02 downscaling compiles existing etc source | Preserve/defer | Source remains present; migration cleanup does not replace the method. |
| 16 tracked Python cache files; broad ignore rules | Defer | Existing generated-file policy issue, not an algorithm/path fix; keep outside this cleanup. |
| Missing historical commit references DT-0064/DT-0092 | Defer | Previously observed in both local repositories; not proven migration loss. Do not silently rewrite research references. |

Optional etc and map/src recipes are v4 reference workflows, not supported v5
entry points. Their local src directories and old configuration contracts are
not all migrated. Notices distinguish them from current guides. Some historical
package-specific paths cannot resolve in a Git-only checkout; they are not
promised as executable here. The old root archive_src.sh is labeled a v4
archiver; its packaging logic remains unchanged and is not run.

## Manual checks retained from the retired workflow

The removed file is .github/workflows/map-sample-validation.yml. Its historical
definition remains in Git. It triggered on selected source/map/config paths,
PRs and manual dispatch; used Ubuntu, GNU Fortran, NetCDF-Fortran and Python;
initialized a disposable config/Mkinclude; built the v5 model and regional map
tools; checked selected Python/Shell syntax; ran CTL, registry, optional-region
and committed-Mekong fixture/wrapper checks. It did not run a full model
regression with approved references, global simulations, package assembly or
independent scientific validation. Its filters also named an obsolete
map/src/map_data_tools/map_metadata.py path.

No active workflow configuration is retained or replaced. Automated CI is
temporarily disabled pending a small, reproducible v5 regression suite, by
explicit maintainer instruction. Existing tests, sources and data are retained.
The build configuration guide now describes local/manual validation, not an
active CI job.

From an independent checkout with a reviewed config/Mkinclude and required
GNU Fortran/NetCDF dependencies, the existing commands remain available:

```sh
make -C src_main all
make -C map/tools/code region
python3 -B map/tests/validate_map_variables.py
python3 -B map/tests/validate_mekong_sample.py
PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest map.tools.tests.test_generate_ctl -v
PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest map.tools.tests.test_region_cut_domain_optional_maps -v
PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest map.tools.tests.test_mekong_ctl_integration -v
```

The region test requires its executable and otherwise reports a skip. Builds
create ignored intermediates; use an independent checkout for review and do
not clean another developer's build. Python/Shell syntax checks can be run
without executing model experiments. These commands are existing checks, not
a new framework or a claim that all of them ran in this cleanup; the actual
results and limitations are in [VR-0150](../research/records/validation_runs/VR-0150.md).

## Validation scope and remaining work

Check corrected roots from another working directory, actual map/runoff/model
paths, syntax and unchanged scientific ASTs; run existing component checks
where dependencies permit. Compare file inventories against the initial state
to verify that only the obsolete workflow is deleted and no scientific source,
model data, reference output, legacy source or historical research is changed.
Current/new documentation links must resolve; historical package-only recipe
paths remain explicitly qualified rather than falsely supported.

Remaining beta work: define the minimal regression/reference contract, decide
supported optional features, fix output-sample reuse under separate scope,
verify fresh-clone model/tutorial/visualization execution, and design future
CI/package assembly. The acceptance decisions remain [KG-0036](../research/records/knowledge_gaps/KG-0036.md).
The brief knowledge-gap review adds no new scientific question; no scientific
or architectural choice is made to hide an ambiguous dependency.

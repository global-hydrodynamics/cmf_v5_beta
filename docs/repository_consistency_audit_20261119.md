# Repository consistency audit — 2026-11-19

Scope: source/tool/data/document/package consistency on feature/package-builder,
baseline88524b24. Read-only investigation of implementation and scientific data;
only this report and status/research evidence are added. No main merge performed.

## Outcome

Most maintained components pass, but current working-tree validation is not
fully green and the existing assembled package is not the latest beta source.
Fix active diagnostics/documentation and reconcile the user-edited registry
before declaring package readiness. Then generate a fresh clean/package version.

## Actionable findings

| Priority | Finding | Evidence and implication |
| --- | --- | --- |
| Before merge/package | Setup checks retired forcing paths and DAY filenames | [s01-setup_fortran.sh](../s01-setup_fortran.sh), lines379–380/403, checks test-mek_1deg/test-mek_1deg_nc. Current mek01 uses repo-mek_1deg_bin monthly Roff____200001/200002.one; mek02 uses repo-mek_1deg annual runoff2000/2001.nc. It also checks nextxy_noedge.nc while maintained mek02 chooses nextxy.nc. The diagnostic can incorrectly report missing inputs. |
| Before merge/package | Current build README points to deleted wrapper | [src_main/README.md](../src_main/README.md), lines29–39, tells readers to run gosh_test/compile_netcdf.sh and expects out/bin/MAIN_cmf_netcdf. Actual supported target is src_main/MAIN_cmf with configured NetCDF support. |
| Reconcile working tree | Uncommitted registry removes upbasin-2569002 definition | Existing Binary/CTL remain tracked. Map registry schema still validates, but Mekong sample test and CTL integration fail. With a temporary HEAD-registry control, all9 corresponding tests pass. Do not silently restore/edit maintainer CSV: decide whether to retain the literal row or add approved standard variant support and align tests. |
| Documentation | Input README advertises a deleted Japan Binary sample | [inp/README.md](../inp/README.md), lines54/72, links to absent test-jpn_6min_1hr/README.md. [Runoff inventory](runoff_data_inventory.md) also retains one link. Mark historical/removed status or correct the intended current product; do not invent replacement data. |
| Fresh packaging required | Existing clean/assembled trees predate recent fixes | Both provenance files retain sourcea39f4ea1. Existing assembled Tutorial02 and Guide01 still reference out/bin/MAIN_cmf_netcdf; latest source fixes are not in those copies. Keep protected outputs and generate a new matching unused VER after source readiness; no automatic rearchive occurred. |
| Current intro | Model workflow plan still says old matrix tag remains current | [docs/model_source_workflow_plan.md](model_source_workflow_plan.md), opening paragraph, says test-mek_1deg remains valid; current pair is repo-mek_1deg. Distinguish current header from preserved historical milestone text. |

## Executed checks

| Check | Result |
| --- | --- |
| Full Explorer pytest | 403 PASS,1Windows SKIP,3subtests PASS,94.02s |
| Package/GOSH/conversion/CTL/input-matrix/research-validator/colormap component pytest | 167 PASS,1FAIL,1SKIP,1memory test deselected,65subtests PASS,34.73s |
| Mekong sample validator on working CSV | 7PASS,1FAIL; missing upbasin registration |
| Temporary committed-CSV control: Mekong validator plus CTL wrapper integration | 9PASS; working CSV not changed |
| Map registry | PASS:86rows,72numeric missing values,14blank/unresolved values allowed by schema |
| Runoff registry | PASS:5rows |
| Tracked Python syntax | 192PASS |
| Tracked Shell syntax | 186PASS;1historical failure in etc/legacy_migrated/old_levee/x03-downscale.sh at line24 |
| Tracked data/docs/Fortran/C permission scan | No executable data/docs/Fortran/C source misuse found |
| Tracked symlinks | One internal link; no absolute/out-of-tree link found |
| Markdown path-only link scan | 64broken links total;3outside historical record trees, all pointing to removed Japan sample. Anchors/external URLs were not checked. |
| Research record validator |12pre-existing broken historical/moved-source links; no structural failures |
| Regenerated Mekong NetCDF versus Binary |37files/41variables exactly match raw arrays and params coordinates |
| Preservation snapshot |203tracked scientific file size/mtime_ns/inode snapshots unchanged; working registry SHA-256 unchanged during audit |

The component failure is generated base CTL count33/skip7 instead of34/skip6,
consistent with removing the upbasin row. Both failing tests reflect the same
registry-selection mismatch; they do not show numerical corruption. Retained
NetCDF changes are uncommitted user work, not modified by the audit.

The initial combined component collection hit an uninstalled cmf_colormap in
the Explorer environment. Rerun used its existing src directory through
PYTHONPATH, with no installation; the table reports that completed run.

## Limits and historical material

No model scientific simulation, Fortran compilation, full large-map conversion,
public redistribution, new real package build or browser visual QA. Existing
Explorer tests are automatic state/rendering tests, not new browser interaction.
The large320MiB process-budget test is intentionally deselected in this audit.
Root .venv is absent; the available Explorer Python lacks xarray. Guide01's
analysis/downscale adapter runtime was already blocked by that missing dependency;
its documented repository environment must be prepared before a full learner run.

Historical v4/legacy sources and numbered tutorial authoring transcripts remain
references. Their old names are not automatically current bugs. The one legacy
Shell syntax failure and12research broken links are reported without rewriting
history. The path-only link scanner excludes fenced code and does not check all
Markdown forms/anchors, so64is a scanner count, not a complete documentation proof.

Main remains older than the approved project branch (58commits behind at fetch).
The maintainer's main merge remains conditional on v5b01 readiness; successful
component tests alone do not authorize that merge or establish model validity.

Temporary detailed logs/scripts are under /private/tmp/cmf-audit-* and are not
version-controlled. Source findings are not repaired in this audit task.

# Distribution-source consistency audit — 2026-11-19

## Scope

Only distribution-intended sources, maintained execution scripts, configuration,
user documentation and dataset registration are in scope. Test execution/test
code, research administration and existing generated packages are excluded.
No model/compiler/setup execution or data generation is performed. This is a
static path/name/document consistency review, not scientific validation.

## Resolution — DT-0149

The four current-use inconsistencies identified by DT-0148 are corrected:

1. [s01-setup_fortran.sh](../s01-setup_fortran.sh) now checks the actual monthly
   repo-mek_1deg_bin files and annual repo-mek_1deg files. Its mek02 list uses
   nextxy.nc, matching the maintained runner; mek01 retains nextxy_noedge.bin.
   Only four path substitutions changed; compiler probes and setup policy remain.
2. [src_main/README.md](../src_main/README.md) uses the standard configured
   src_main/MAIN_cmf target for Binary/NetCDF workflows. Removed compiler-wrapper
   and separate out/bin target are no longer current instructions. Build commands
   establish repository/package root; NetCDF configuration remains explicit.
3. [inp/README.md](../inp/README.md) no longer lists the removed Japan Binary
   sample as current distribution data. The [inventory](runoff_data_inventory.md)
   preserves historical unit/provenance facts without linking a missing README.
4. [Model workflow plan](model_source_workflow_plan.md) current introduction uses
   repo-mek_1deg and its matching descriptor/matrix. Earlier milestone filenames
   remain historical evidence rather than current commands.

Static confirmation: changed setup input references exist; shell syntax is valid;
normalizing the four path substitutions restores the original setup script
exactly. Eighty local links across four changed documents resolve, fenced blocks
are balanced and current descriptions agree with existing file names. No tests,
model run, compiler invocation, setup execution or generated-package inspection.

Current Tutorial01/Tutorial02/Guide01 shared executable paths, source input names
and Binary visualization remain unchanged. The working map CSV and scientific
data are not edited/staged. Its upbasin registration choice is not auto-restored.
No additional current-use inconsistency was established within this static scope;
this does not certify arbitrary optional configurations or scientific validity.

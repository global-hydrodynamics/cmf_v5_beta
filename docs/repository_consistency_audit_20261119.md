# Distribution-source consistency audit — 2026-11-19

## Scope

Following the maintainer's scope correction, inspect only sources, maintained
execution scripts, configuration, user documentation and dataset registration
intended for the forthcoming beta distribution. Existing generated package/clean
trees are excluded. Test execution/results/test code and research/administrative
records are excluded from the audit verdict. No further test suite is run.

This is a static source/path/name consistency review, not a compilation, model
run, scientific validation or inspection of an assembled distribution. Preserve
uncommitted scientific data and maintainer metadata. No source repair here.

## Remaining current-use inconsistencies

1. **Fortran setup sample checks use retired input paths.**
   [s01-setup_fortran.sh](../s01-setup_fortran.sh), lines379–380 and403,
   still checks test-mek_1deg daily DAY filenames and test-mek_1deg_nc.
   Current mek01/Tutorial01 use inp/repo-mek_1deg_bin/runoff/ with monthly
   Roff____200001.one and Roff____200002.one. Current mek02 uses
   inp/repo-mek_1deg/runoff2000.nc and runoff2001.nc. The setup can therefore
   incorrectly label installed samples incomplete. Its mek02 map list also
   checks nextxy_noedge.nc while maintained mek02 selects nextxy.nc.

2. **Model build README points to a removed entry point.**
   [src_main/README.md](../src_main/README.md), lines29–39, describes the
   missing gosh_test/compile_netcdf.sh and out/bin/MAIN_cmf_netcdf. Align the
   active instructions with the configured src_main/MAIN_cmf target and the
   Tutorial01-built executable reused by Tutorial02/Guide01. Preserve genuinely
   historical build evidence separately from current commands.

3. **Input documentation lists a removed Japan Binary sample as current.**
   [inp/README.md](../inp/README.md), lines54/72/78, lists/links
   test-jpn_6min_1hr/, which is no longer present. Clarify removed/historical
   status or document the intended existing product; do not invent replacement
   data. [Runoff inventory](runoff_data_inventory.md) has another link to the
   absent sample README, which should be labeled as historical evidence.

4. **Current model-workflow introduction retains an obsolete matrix tag.**
   [model source plan](model_source_workflow_plan.md), opening paragraph,
   still says test-mek_1deg is the current mapping tag. Current maintained
   scripts and descriptors use repo-mek_1deg, with
   diminfo_repo-mek_1deg.txt/inpmat_repo-mek_1deg.bin. Update the current
   introduction; older milestone spellings can remain historical.

## Consistent current source relationships

- Tutorial01, Tutorial02 and Guide01 active runners use src_main/MAIN_cmf;
  Tutorial02/Guide01 assume the NetCDF-enabled Tutorial01 build.
- Maintained simulation scripts and tutorial inputs use the renamed
  repo-mek_1deg/repo-mek_1deg_bin products and matching matrix pair.
- Current converter entry paths are script_format_conv; experimental variants
  and positive numbered MPI files use their documented standard definitions.
- Explorer uses code/ implementation paths and the current subcol/subbsn sample
  NetCDF conventions. No new runtime/browser claim is made by this review.
- Visualization catalog contains28unique IDs;83script/image/documentation paths
  resolve. Map/runoff/output registry source/doc references have no missing
  maintained code path; one optional Global Binary location metadata path is
  absent locally and is not treated as a required installed source dependency.
- No maintained-source executable data/docs/Fortran/C permission misuse or unsafe
  tracked symlink was found. Old transcripts/legacy examples are not current
  runnable instructions and are not blanket-renamed.

The working map CSV currently omits the concrete upbasin-2569002.bin row.
That file is outside registered conversion selection. This is a maintainer
metadata choice to preserve, not a test-driven request to restore the row.
Scientific data and working CSV were not edited by the audit.

General beta assembly implementation remains source material, but its existing
generated artifacts and remake scheduling are outside this audit. No verdict
is made about them. Main integration is not performed here.

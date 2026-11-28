# Manual Design — Guide01 Workflow Example

**Audience:** tutorial authors and model users familiar with editing scripts, but new to this sensitivity workflow. The learner-facing workflow is deliberately incomplete at the start; completed reference files remain in `design/` for developers and are not part of a learner package.

## Learning sequence

| Stage | Learner operation | Starting material | Artifact to create | Completion evidence |
| --- | --- | --- | --- | --- |
| Prepare the map parameter | Inspect `s01-prepare_map.py` and change `RIVHGT_INCREMENT_M` from `0.0` to `3.0`. Run the script. | Editable map-preparation script and shared `rivhgt.nc`. | `map_modify/rivhgt_deep.nc`. | Reported dimensions, valid/missing counts, unchanged grid/mask, and configured increment. |
| Create an experiment configuration | Copy `run-experiment.sh`, assign a new `PROJ`, and change `RIVHGT` to the tutorial-local map. | Working Control GOSH configuration. | Learner-created `run-deep-channel.sh`. | Namelist uses the created map and writes to a different project directory from Control. |
| Run and inspect | Run Control and the learner-created Deep Channel configuration, then run the supplied analyses and downscaler. | Shared inputs, map variant, and two independent configurations. | Model outputs, analysis products, and figures. | Both runs complete; analysis products and figures appear under the tutorial-owned output paths. |

The only intended scientific experiment difference remains the approved `+3 m` change to valid river-depth cells. Learners are not asked to change the scientific setting or infer an expected response. Their transferable skills are editing a map-generation setting, preserving shared inputs, and constructing an isolated GOSH experiment by changing `PROJ` and an input-path setting.

The workflow uses the current NetCDF-first Mekong map (`params.nml`, map-root
NetCDF layers, `1min/location.csv` and high-resolution NetCDF tiles), paired
with `inpmat_repo-mek_1deg.nc` and `diminfo_repo-mek_1deg.nml`. Control and
Deep Channel use the same model settings and inputs except for `CRIVHGT`.
Guide01 includes a physical copy of `tools/downscale_flddph/` and its required
metadata readers; the copy is self-contained and does not update automatically.

## Package state

Include the editable learner scripts, the tutorial-local downscaler and its
sample, and approved example images under `sample_figure/`. The starting
package has no `map_modify/rivhgt_deep.nc`, no learner-created Deep Channel
runner, no model outputs or analysis tables, and no generated figures under
`figure/`. Completed map, runner, and analysis references remain in `design/`;
generated outputs and modified map data are ignored by Git.

The general beta Package Builder exists and retains developer references; no dedicated learner-profile tutorial assembler exists. A temporary learner snapshot can verify the intended file set, but a complete learner-follow-through has not been performed after this intentional incompleteness change; package reproducibility remains partial.

## Future Learning Checks

- Can the learner identify the `rivhgt` increment and produce a separate map file without modifying the shared map?
- Can the learner explain which `PROJ` and `RIVHGT` settings distinguish the copied experiment?
- Can the learner locate the two run directories and the generated comparison figures?


Executable prerequisite: as in Tutorial02, reuse NetCDF-enabled
`src_main/MAIN_cmf` already compiled during Tutorial01, without a separate
compile wrapper. Prepare the repository `.venv` and set `CMF_V50_ROOT` for the
runner and analysis paths. Keep the tutorial-local Python NetCDF downscaling
implementation and approved learner edits unchanged.

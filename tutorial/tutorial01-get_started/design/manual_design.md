# Manual Design — Tutorial01: Get Started

**Audience:** first-time CaMa-Flood users comfortable copying terminal commands, but unfamiliar with the v5 repository, Fortran builds, river maps, runoff forcing, and GOSH experiments.

The experiment contract is [`../tutorial_design.md`](../tutorial_design.md). Shared evidence and writing instructions are in [`../../agent_manual_authoring.md`](../../agent_manual_authoring.md).

## Learning outcomes

Tutorial01 checks introductory navigation and workflow skills only. Readers should be able to:

- Obtain Tutorial01 and its matching inputs from the v5 beta branch, or default main after the planned integration.
- Locate the repository root, configure `CMF_V50_ROOT`, and identify the main source, map, input, and tutorial directories.
- Run the setup scripts and follow their displayed choices without accidentally replacing an existing configuration; optionally activate the local Python environment with `cmfpy`.
- Build or update `MAIN_cmf` from `src_main/` with `make all`.
- Locate the map, runoff, and input-mapping files named by the GOSH settings.
- Find `PROJ`, input paths, and output paths in the GOSH script.
- Run Tutorial01 and locate its model output and log.

These outcomes do not require learners to explain physical map variables, model parameters, numerical methods, hydrodynamic processes, or the mathematical details of input mapping. The manual may give brief context for terms needed to follow the steps, but Learning Checks should not assess those topics.

Use the v5 repository `global-hydrodynamics/cmf_v5_beta`. Main is its
default/base branch; during v5b01 preparation, the instructions and matching
inputs reside on `feature/package-builder` until the maintainer's planned merge.
Acquisition examples must identify the revision being documented. The learner
snapshot starts without compiled `MAIN_cmf` or generated tutorial results; the
learner performs the build.

## Manual-wide conventions

- Begin by explaining that the v5 development checkout is the tutorial environment and that a successful run does not validate scientific accuracy.
- At the repository root, run `pwd` and `ls -lF`, then run `s00-configure_cama_root.sh`. Explain that it writes `CMF_V50_ROOT` to a shell startup file but does not change the current shell; the learner must run the printed activation command or open a new terminal, then verify the variable.
- Use `cd "${CMF_V50_ROOT}"` to return to the repository root at the start of each major command section. Enter relevant subdirectories with relative paths. Use `pwd` before listing a directory. Within one major section, do not repeat root-navigation commands before every related command.
- For directory inspection, show a concise **Expected output** block based on real output. Include representative file names and properties; if entries are omitted, mark the excerpt as abbreviated. Explain that owners, dates, and some sizes vary by checkout or platform.
- Use `ls -lF` for beginner directory listings, and `ls -lhF` when human-readable sizes help. Explain that `/` marks directories and `*` normally marks executable files; these suffixes are display markers, not filename characters. Use output captured from the exact command shown.
- Use the five-part instructional pattern—Purpose, Commands, Expected output, Explanation, Required action—where it helps the reader. Interactive setup sections combine the last three under **Output and required actions**. Do not force the pattern onto trivial steps.
- End every major instructional section with one or two short **Learning Check** checklist items. Derive them from the introductory learning outcomes; they must be directly answerable from that section and check basic navigation, file/settings lookup, or successful workflow completion. Do not assess scientific mechanisms, model physics, or numerical methods. Do not add checks to introductions or developer-only notes.
- Introduce data progressively: locate and list files, explain what they represent, then show the settings that select them.
- Keep command blocks short and literal. Avoid advanced shell pipelines when `cat`, `ls`, or opening the file in an editor teaches the intended concept more directly.
- Put terminal output in separate blocks from instructions. Identify representative environment-dependent details and do not invent prompts or output.

## Required demonstrations by section

| Section | Learner should understand | Inspect and demonstrate | Expected output required? | Learner action and successful completion | Learning Check |
| --- | --- | --- | --- | --- | --- |
| 0. Obtain CaMa-Flood | Obtain the repository revision that matches the manual's file paths and inputs. | Give the current beta clone/ZIP instructions and, if applicable, explain when default main becomes the matching revision. | No terminal output required. | Obtain the matching tutorial/data revision and locate its root. | Can identify the v5 repository and the revision documented by this manual. |
| 1. Find and configure the repository root | The checkout root is stored in `CMF_V50_ROOT` for later shell sessions. `ls -lF` marks directories and executable scripts. | Run `pwd` and `ls -lF`; run `s00-configure_cama_root.sh`; follow its printed activation instruction; print `CMF_V50_ROOT`. | Yes: actual root listing and the variable value. | Confirm the variable matches the checkout; explain that sourcing or restarting the shell is required. | Can identify the checkout root from `CMF_V50_ROOT` and interpret `/` and `*` markers. |
| 2. Prepare the environment | `s01` checks the Fortran build; `s02` prepares optional Python; `s03` registers the `cmfpy` activation alias. | Run setup from the root; show representative checks and prompts, then describe reloading the selected shell configuration. | Yes: setup results and prompts grounded in script output. | Review the generated `Mkinclude` before copying it; optionally activate Python with `cmfpy` and leave it with `deactivate`. | Can identify which configuration is used for Fortran and how to activate the optional local Python environment. |
| 3. Build the model | The model executable is located in `src_main/`. | Enter `src_main/`, run `make all`, then list `MAIN_cmf`. | Yes: successful build completion and executable listing. | Run the build command and confirm `MAIN_cmf` is present. | Can locate `MAIN_cmf` after `make all`. |
| 4. Read the experiment settings | The specification describes the experiment; the GOSH script contains its settings. | Inspect `tutorial_design.md` and the standalone script using `cat` and a text editor. | Yes: visible indicators from the two files. | Find a setting in the script without modifying it. | Can locate the GOSH script and find a setting shown in the specification. |
| 5. Locate river-map files | The GOSH script selects NetCDF map variables and CSV bifurcation parameters from the Mekong map directory. | List `params.nml`, `nextxy_noedge.nc`, `ctmare.nc`, `elevtn.nc`, `rivwth_merit.nc`, and `bifprm.csv`; show `MAPDIR`, `NEXTXY`, and `RIVWTH`. Briefly note `1min/location.csv` as the high-resolution tile inventory. | Yes: actual names and representative sizes. | Match the selected connectivity and channel-width files to the script. | Can identify `params.nml` as map geometry and the NetCDF files selected by the script. |
| 6. Locate runoff files | The runoff directory contains dated files referenced by the script. | List January 1, January 2, and February 9 files; show dataset, directory, and filename settings. | Yes: actual filenames and representative sizes. | Match a listed runoff file to the script's path/name settings. | Can find the daily runoff files and corresponding GOSH settings. |
| 7. Locate input-mapping files | The `&DIMINFO` group describes the model grid, while `&INPUTDIM` describes the external runoff grid; the NetCDF matrix connects them. | List and display `diminfo_repo-mek_1deg.nml` and `inpmat_repo-mek_1deg.nc`; show `DIMINFO`, `INPMAT`, and `LINTERP`. | Yes: actual sizes and current Namelist excerpt. | Match the settings to the files and distinguish the model grid from the input runoff grid. | Can locate the descriptor/matrix and identify the purpose of each group. |
| 8. Run the experiment | The sample writes results under the directory selected using `PROJ`. | Show `PROJ`, `RUNDIR`, run command, success/status, and output listing. | Yes: captured run excerpt and result files. | Run from the documented directory and locate the selected run directory. | Can recognize successful completion and locate the run directory. |
| 9. Locate results | The output directory contains model outputs and logs. | List project outputs and show the model's normal completion message. | Yes: representative result files and completion evidence. | Locate the discharge output and model log. | Can find `outflw2000.bin` and `log_CaMa.txt`. |

## Experiment facts that the manual may summarize

The settings table should state: project `tutorial01-get_started`; map `map/mekong_15min` with `params.nml` geometry and individual NetCDF variables; runoff `inp/repo-mek_1deg_bin/runoff/`; mapping descriptor `diminfo_repo-mek_1deg.nml` and matrix `inpmat_repo-mek_1deg.nc`; 2000-01-01 00:00 through 2000-02-10 00:00 exclusive; `DT=3600` seconds with adaptive stepping; non-MPI and one OpenMP thread; daily Binary outputs `outflw`, `storge`, `sfcelv`, `flddph`, and `fldfrc`; project output under `tutorial/tutorial01-get_started/out/${PROJ}/`.

The manual should not repeat the complete experiment specification, reproduce the whole shell script, introduce visualization or observational comparison, or claim that the simulated values are scientifically validated.

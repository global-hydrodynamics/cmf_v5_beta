# Tutorial Design — Tutorial01: Get Started

**Purpose:** define the first-run actions, inputs, and acceptance criteria for the CaMa-Flood v5 getting-started tutorial. Shared implementation instructions are in [`../agent_tutorial_development.md`](../agent_tutorial_development.md); the learner-facing content is specified in [`design/manual_design.md`](design/manual_design.md).

## Section 0: Obtain CaMa-Flood

The v5 source repository is `global-hydrodynamics/cmf_v5_beta`, with default/base
branch `main`. Current v5b01 work, including the input names in this design, is on
`feature/package-builder`. During preparation, obtain that approved branch or its
ZIP so tutorial instructions and bundled data match. The maintainer plans one
merge into `main` when the v5b01 package is ready; after the merge, default `main`
becomes the standard acquisition route. This document does not claim that the
merge or formal release has already occurred. Place the checkout in a suitable
working directory; do not assume a machine-specific path.

Before the learner starts, the distributable tutorial checkout must not contain a compiled `src_main/MAIN_cmf` executable or Tutorial01-generated results. The learner builds the model with `make all` and then runs the sample. Do not remove shared developer build products while editing the source repository; verify this initial state in a clean learner snapshot.

## Learning outcomes

Tutorial01 introduces repository navigation and a first model run; it does not teach river hydrodynamics or numerical modeling. Learning outcomes focus on observable **operational skills** and simple file/configuration relationships.

| Stage | Operational skills | Basic relationship to identify | Observable evidence of learning |
| --- | --- | --- | --- |
| Obtain CaMa-Flood | Obtain the v5 branch or ZIP matching this tutorial revision and locate the checkout root. | The documented script, bundled inputs, and source revision must match. | The learner obtains the matching tutorial/data revision and identifies its root. |
| Find the repository | Confirm the root with `pwd` and `ls -lF`, run `s00-configure_cama_root.sh`, activate the updated shell configuration, and confirm `CMF_V50_ROOT`. | `s00` stores the repository root in the user's shell startup configuration but does not update the current shell automatically. | The learner can identify the repository root from `CMF_V50_ROOT` and the `/`/`*` file-type markers. |
| Prepare the environment | Run `s01`, optionally set up Python with `s02`, and register/activate `cmfpy` with `s03`. | The suggested root `Mkinclude` is separate from active `config/Mkinclude`; Python is optional for the Fortran simulation. | The learner can follow the setup prompts, protect an active configuration, and activate/deactivate the optional Python environment. |
| Build the model | Run `make all` in `src_main/` and locate `MAIN_cmf`. | Identify that the executable is produced in `src_main/` from model source. | The learner can find the executable after building. |
| Read experiment settings | Read this specification and inspect the standalone GOSH script. | Identify where experiment details are described and where the script settings are written. | The learner can locate a setting in the script after finding it in the experiment information. |
| Locate runoff files | List the annual NetCDF runoff file and find the dataset and variable settings. | Match the `runoff2000.nc` file, `runoff` variable, and `time` coordinate to the script settings. | The learner can locate the input file and identify its runoff and time variables. |
| Locate river-map files | List representative individual NetCDF map files and CSV bifurcation parameters; inspect `MAPDIR`, `NEXTXY`, and `RIVWTH`. | Match the script paths and filenames to products in the map directory. | The learner can point out the selected map directory, connectivity file, and width file. |
| Locate runoff-mapping files | List the input-dimension descriptor and NetCDF matrix and find `DIMINFO` and `INPMAT`. | Match those settings to the files in the map directory; distinguish the model grid from the runoff input grid. | The learner can find each referenced file and its setting in the GOSH script. |
| Run an experiment | Execute the Tutorial01 script from its documented directory and identify `PROJ` and `RUNDIR`. | Match the project name to the output directory shown by the script. | The learner can run the script, recognize its success message, and locate the selected run directory. |
| Locate results | List the project output and inspect the model log and NetCDF Restart. | Identify the daily discharge file, other requested NetCDF outputs, model log, and final Restart. | The learner can locate `o_outflw2000.nc`, `log_CaMa.txt`, and the end-of-run Restart. |

Starting from a matching v5 checkout with bundled Mekong samples and a prepared local build configuration, the learner builds the model, runs the 40-day experiment, and locates results under `tutorial/tutorial01-get_started/out/${PROJ}/`. A clean learner starting state omits the compiled `src_main/MAIN_cmf` executable and generated Tutorial01 outputs.

## Repository layout to introduce

The manual should show a compact tree based on the actual repository, including:

```text
cmf_v5_beta/
├── config/Mkinclude                 # Active v5 compiler configuration
├── src_main/                        # v5 Fortran source and MAIN_cmf after build
├── map/mekong_15min/                # Bundled 80 x 120 river map
│   ├── params.nml                   # Map grid and geographic bounds
│   ├── nextxy_noedge.nc             # River connectivity
│   ├── diminfo_repo-mek_1deg.nml    # Model and runoff-input grid metadata
│   └── inpmat_repo-mek_1deg.nc      # Runoff-to-map input matrix
├── inp/repo-mek_1deg/              # Annual NetCDF runoff dataset
├── gosh_test/                        # Developer GOSH workflows and operational checks
└── tutorial/tutorial01-get_started/
    ├── tutorial_design.md
    ├── tutorial01-get_started.sh    # Standalone educational GOSH experiment
    ├── README.md                   # Learner-facing tutorial manual
    └── out/tutorial01-get_started/   # Default project results; Git-ignored
```

The repository also contains root setup scripts and shared tools; include them in the explanatory text, not necessarily in this compact tree. `tutorial/design/` is developer-facing material and need not appear in the learner's main tree.

## Starting state and prerequisites

- Use a v5 source revision matching the tutorial and its bundled Mekong inputs. During v5b01 preparation, this is `feature/package-builder`; use `main` after that revision is merged. Require a clean learner snapshot without compiled `MAIN_cmf` or Tutorial01 results; do not clean a shared development checkout to produce it.
- The current state of `src_main/MAIN_cmf` and Tutorial01's `out/` is not prescribed. `make all` builds or updates the required executable, and the sample script replaces only its known generated files on rerun. Sample map, runoff, and matching input-matrix data are included; no scientific data download or map generation is required.
- `CMF_V50_ROOT` identifies the repository root. Run `s00-configure_cama_root.sh` once; source the startup file it identifies or open a new terminal, then check the variable.
- GNU Make, GNU Fortran with OpenMP, and NetCDF-Fortran are available. Run `s01-setup_fortran.sh`, review its recommended configuration, and manually copy the staged `Mkinclude` to the existing `config/Mkinclude` location before building.
- Python is optional for this Fortran simulation. `s02-python_setup.sh` creates the repository-local environment when selected; `s03-activate_cmf_pyenv.sh` registers the `cmfpy` activation alias. After sourcing the selected shell configuration or opening a new terminal, use `cmfpy` and `deactivate` as needed.
- The developer reset utility requires `config/Mkinclude` to exist and must preserve it.

## Experiment inputs and settings

- Map: `map/mekong_15min/`, 80 × 120 cells, 0.25-degree grid, and 10 floodplain layers. Geometry is in `params.nml`; individual map variables are NetCDF files and bifurcation metadata is in `bifprm.csv`.
- Selected map inputs: `nextxy_noedge.nc`, `rivwth_merit.nc`, and other individual NetCDF variables. High-resolution tile inventory is `map/mekong_15min/1min/location.csv`.
- Runoff: `inp/repo-mek_1deg/runoff2000.nc`, annual NetCDF `runoff(time, latitude, longitude)` daily `mm day-1`; the runoff grid is 20 × 30 and time uses `proleptic_gregorian` CF coordinates with interval bounds. The 2000 file has 366 daily records, including February 29.
- Runoff-to-map files: `map/mekong_15min/diminfo_repo-mek_1deg.nml` and `inpmat_repo-mek_1deg.nc`, generated for this map/runoff grid pairing. `&DIMINFO` describes the model grid; `&INPUTDIM` describes the external runoff input grid.
- Simulation: 2000-01-01 00:00 to 2000-02-10 00:00 exclusive (40 days), non-MPI, base timestep 3600 seconds, adaptive timestep and bifurcation enabled, reservoir operation disabled, one OpenMP thread.
- Preserve the scientific settings of `gosh_test/mek01-default_run.sh`, while using NetCDF for runoff, matrix input, model output, and Restart. The tutorial's standalone script keeps the same 40-day period, Mekong map, routing options, and physical parameters; it uses annual NetCDF runoff and one OpenMP thread. The maintained GOSH `mek01-default_run.sh` remains a developer-facing Binary I/O check and is unchanged.
- Require `CMF_V50_ROOT`, source `tools/cmf_shell_functions.sh`, and use `cmf_check_init`, `cmf_check_step`, and `cmf_check_success` for shared Shell error/progress reporting. Preserve the Fortran NAMELIST variable name `CMF_BASE`; populate it from `${CMF_V50_ROOT}`.
- Define `PROJ="tutorial01-get_started"` using the established experiment-name convention. Construct `RUNDIR` as the Tutorial01 script directory's `out/${PROJ}/`. Generated executable copy, Namelist, logs, five NetCDF model outputs, and final NetCDF Restart all belong there.
- A rerun of the same project may replace only that project's known generated files. Changing `PROJ` creates a separate experiment directory and must preserve the previous project directory. Do not remove the shared `out/` parent or other project subdirectories.
- Output variables: `outflw`, `storge`, `sfcelv`, `flddph`, and `fldfrc`; daily NetCDF output and one NetCDF Restart at the end of the run. Binary output and GrADS CTL generation are not part of the standard Tutorial01 workflow.

## Required workflow

1. Direct learners to `https://github.com/global-hydrodynamics/cmf_v5_beta`. During v5b01 preparation, show the `feature/package-builder` clone command or select that branch before Download ZIP. State that the default/base branch is `main` and becomes the standard route after the maintainer's planned merge when v5b01 is ready. Use a matching tutorial/data revision and a suitable local working directory.
2. From the repository root, run `pwd` and `ls -lF`, then `s00-configure_cama_root.sh`. Follow its printed shell-activation command or open a new terminal and verify `CMF_V50_ROOT`; explain that the configuration change does not take effect in the current shell automatically.
3. Prepare the Fortran environment with `s01-setup_fortran.sh`. Optionally create the Python environment with `s02-python_setup.sh`, then register it using `s03-activate_cmf_pyenv.sh`; source the selected shell configuration or open a new terminal before using `cmfpy`. Python is not needed for the simulation itself.
4. Activate `config/Mkinclude` by copying the reviewed staged `Mkinclude` manually; `config/` already exists.
5. From `${CMF_V50_ROOT}`, enter `src_main/` and run `make all` to build or update the current model executable.
6. Inspect the annual NetCDF runoff file, then the individual NetCDF river map, bifurcation CSV, and paired input-dimension and input-matrix files; relate their names to the GOSH settings.
7. Read `tutorial_design.md`, then inspect the plain-text standalone Tutorial01 GOSH configuration and its experiment settings.
8. From `tutorial/tutorial01-get_started/`, execute `./tutorial01-get_started.sh`; the default project output is `out/tutorial01-get_started/`.
9. Inspect the generated Namelist, logs, five NetCDF model outputs, and final NetCDF Restart under the project-specific directory.

Map generation and visualization are not required.

## Acceptance criteria

- Running `make all` from `src_main/` returns zero and leaves an executable `MAIN_cmf`, whether it is newly built or updated.
- Section 0 identifies the v5 repository and the matching branch for the tutorial revision.
- The root-directory demonstration uses `ls -lF`, with observed output showing directory and executable markers and an explanation that suffixes are not part of filenames.
- The standalone tutorial script defines the default `PROJ`, constructs its `RUNDIR` under `out/${PROJ}/`, does not call or source `gosh_test/mek01-default_run.sh`, and runs from its documented directory.
- The script requires `CMF_V50_ROOT`, uses the shared Shell functions for errors, progress and success, and assigns the existing NAMELIST `CMF_BASE` from the environment variable.
- The tutorial uses `params.nml`, individual NetCDF map variables, CSV bifurcation parameters, `diminfo_repo-mek_1deg.nml`, `inpmat_repo-mek_1deg.nc`, and annual NetCDF runoff.
- Tutorial01 and the model return zero; `log_CaMa.txt` reaches normal calculation completion.
- Five expected daily NetCDF output files, the Namelist, logs, executable copy, and one end-of-run NetCDF Restart are created under only `tutorial/tutorial01-get_started/out/tutorial01-get_started/`; no GrADS CTLs are generated.
- Each daily output contains 40 records for the 40-day interval. The end time is exclusive; output timestamps follow the model's NetCDF convention. The 2000 forcing file's 366 records include the leap day, though the experiment ends before February 29.
- Bundled map, runoff, and matching input-matrix files remain unchanged.
- In a disposable checkout, the developer reset can remove build products and one explicitly selected Tutorial01 project directory while preserving `config/Mkinclude`, bundled inputs, the `out/` parent, and unrelated project directories.

Successful execution is operational evidence, not scientific validation.

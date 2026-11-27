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

The general beta Package Builder is implemented: archive committed sources with
`package/archive_clean_repo.sh`, then assemble the existing clean tree and
CSV-selected Additional Data with `package/make_package.sh`. Set the same unused
VER in both scripts. The Additional Data default `../../cmf_v5_package_data` is
relative to the script's `package/` directory, independent of CWD; absolute paths
are supported. Output is `package/cmf_${VER}_pkg/`; existing outputs are protected.
See the [package guide](../../package/README.md#assemble-a-beta-testing-package).
This is an optional maintainer workflow, not a new learner activity or requirement
to obtain Additional Data for the bundled Mekong example.

The generated beta retains developer materials/legacy and excludes research/Git
administration. It is not a formal release or a dedicated learner-profile
package. Assembly checks do not replace Tutorial01 execution checks, which remain
pending in the assembled package. Existing public-redistribution uncertainties
remain; older v4 distributions are not a supported substitute.

Before the learner starts, the distributable tutorial checkout must not contain a compiled `src_main/MAIN_cmf` executable or Tutorial01-generated results. The learner builds the model with `make all` and then runs the sample. Do not remove shared developer build products while editing the source repository; verify this initial state in a clean learner snapshot.

## Learning outcomes

Tutorial01 introduces repository navigation and a first model run; it does not teach river hydrodynamics or numerical modeling. Learning outcomes focus on observable **operational skills** and simple file/configuration relationships.

| Stage | Operational skills | Basic relationship to identify | Observable evidence of learning |
| --- | --- | --- | --- |
| Obtain CaMa-Flood | Obtain the matching v5 beta branch/ZIP; use default main after the planned v5b01 integration. Locate the root folder. | GitHub sources and locally assembled beta packages are distinct from a formal release. | The learner obtains a matching tutorial/data revision and identifies its root. |
| Find the repository | Confirm the root with `pwd`, assign `cmf_root`, and inspect it with `ls -lF` for directories and executable scripts. | `ls -lF` adds display markers such as `/` for directories and `*` for executables; these markers are not filename characters. | The learner can locate `src_main/`, `map/`, `inp/`, and identify directory and executable markers in the listing. |
| Prepare the environment | Run the setup scripts, recognize check results and prompts, and locate the suggested configuration. | Identify that the suggested root `Mkinclude` is separate from active `config/Mkinclude`; recognize Python setup as optional for this tutorial. | The learner can follow the setup instructions and avoid replacing an active configuration without a backup. |
| Build the model | Run `make all` in `src_main/` and locate `MAIN_cmf`. | Identify that the executable is produced in `src_main/` from model source. | The learner can find the executable after building. |
| Read experiment settings | Read this specification and inspect the standalone GOSH script. | Identify where experiment details are described and where the script settings are written. | The learner can locate a setting in the script after finding it in the experiment information. |
| Locate river-map files | List representative map files and inspect `MAPDIR`, `NEXTXY`, and `RIVWTH`. | Match the script's path and filenames to files in the map directory. | The learner can point out the selected map directory, connectivity file, and width file. |
| Locate runoff files | List daily runoff files and find the relevant dataset and filename settings. | Match the directory and filename parts in the script to actual sample files. | The learner can locate a dated runoff file and the settings that point to its dataset and naming pattern. |
| Locate runoff-mapping files | List the input-dimension descriptor and matrix and find `DIMINFO` and `INPMAT`. | Match those settings to the two files in the map directory; identify `LINTERP` as another setting in the same block. | The learner can find each referenced file and its setting in the GOSH script. |
| Run an experiment | Execute the Tutorial01 script from its documented directory and identify `PROJ` and `RUNDIR`. | Match the project name to the output directory shown by the script. | The learner can run the script, recognize its success message, and locate the selected run directory. |
| Locate results | List the project output and inspect the model log. | Identify which generated file is discharge output and which file is the model log. | The learner can locate `outflw2000.bin`, `log_CaMa.txt`, and see evidence that the run completed. |

Starting from a clean matching v5 beta checkout (default `main` after integration) with bundled Mekong samples and a prepared local build configuration, the learner builds the model, runs the 40-day experiment, and locates results under `tutorial/tutorial01-get_started/out/${PROJ}/`. The distributed starting state omits the compiled `src_main/MAIN_cmf` executable and generated Tutorial01 outputs. General beta assembly is available, but Tutorial01 has not been verified in the assembled beta package or older distributions.

## Repository layout to introduce

The manual should show a compact tree based on the actual repository, including:

```text
cmf_v5_beta/
├── config/Mkinclude                 # Active v5 compiler configuration
├── src_main/                        # v5 Fortran source and MAIN_cmf after build
├── map/mekong_15min/                # Bundled 80 x 120 river map
│   ├── params.txt                   # Map dimensions, grid, and geographic bounds
│   ├── diminfo_repo-mek_1deg.nml     # Runoff-grid dimensions and mapping metadata
│   └── inpmat_repo-mek_1deg.bin     # Runoff-to-map input matrix
├── inp/repo-mek_1deg_bin/runoff/        # Bundled daily Binary runoff
├── gosh_test/                        # Developer GOSH workflows and operational checks
└── tutorial/tutorial01-get_started/
    ├── tutorial_design.md
    ├── tutorial01-get_started.sh    # Standalone educational GOSH experiment
    ├── manual_tutorial01-get_started.md
    └── out/tutorial01-get_started/   # Default project results; Git-ignored
```

The repository also contains root setup scripts and shared tools; include them in the explanatory text, not necessarily in this compact tree. `tutorial/design/` is developer-facing material and need not appear in the learner's main tree.

## Starting state and prerequisites

- Use a matching v5 beta source revision: feature/package-builder before the planned v5b01 merge, main afterward. It contains src_main/, config/, bundled Mekong map/runoff inputs, setup scripts and Tutorial01. Require a clean learner snapshot without compiled MAIN_cmf or Tutorial01 results; do not clean a shared development checkout to produce it. The general beta builder exists, but learner-profile packaging and Tutorial01 execution in its output remain unverified.
- The current state of `src_main/MAIN_cmf` and Tutorial01's `out/` is not prescribed. `make all` builds or updates the required executable, and the sample script replaces only its known generated files on rerun. Sample map, runoff, and matching input-matrix data are included; no scientific data download or map generation is required.
- GNU Make, GNU Fortran with OpenMP, and NetCDF-Fortran are available. Run `s01-setup_fortran.sh`, review its recommended configuration, and manually copy the staged `Mkinclude` to the existing `config/Mkinclude` location before building.
- Run `s02-python_setup.sh` for Python environment diagnosis/setup. Tutorial01's CTL tools use Python standard-library features; installing the full optional requirements set is not required for the sample run.
- The developer reset utility requires `config/Mkinclude` to exist and must preserve it.

## Experiment inputs and settings

- Map: `map/mekong_15min/`, Binary format, 80 × 120 cells, 0.25-degree grid, and 10 floodplain layers.
- Runoff: `inp/repo-mek_1deg_bin/runoff/`, daily Binary `mm/day` records in monthly files named `Roff____YYYYMM.one`; the sample grid is 20 × 30.
- Runoff-to-map files: `map/mekong_15min/diminfo_repo-mek_1deg.nml` and `inpmat_repo-mek_1deg.bin`, generated for this map/runoff grid pairing.
- Simulation: 2000-01-01 00:00 to 2000-02-10 00:00 exclusive (40 days), non-MPI, base timestep 3600 seconds, adaptive timestep and bifurcation enabled, reservoir operation disabled, one OpenMP thread.
- Preserve the scientific and I/O settings of `gosh_test/mek01-default_run.sh`. The tutorial's complete standalone script changes only repository-relative context, output isolation under `tutorial/tutorial01-get_started/out/${PROJ}/`, the project name, and OpenMP thread count to one. The maintained `gosh_test/` script remains unchanged.
- Define `PROJ="tutorial01-get_started"` using the established experiment-name convention. Construct `RUNDIR` as the Tutorial01 script directory's `out/${PROJ}/`. Generated executable copy, Namelist, logs, model outputs, CTLs, and Restart files all belong there.
- A rerun of the same project may replace only that project's known generated files. Changing `PROJ` creates a separate experiment directory and must preserve the previous project directory. Do not remove the shared `out/` parent or other project subdirectories.
- Output variables: `outflw`, `storge`, `sfcelv`, `flddph`, and `fldfrc`; daily Binary output and standard end-of-run Binary Restart.

## Required workflow

1. Direct learners to `https://github.com/global-hydrodynamics/cmf_v5_beta`. During v5b01 preparation, show `git clone --branch feature/package-builder https://github.com/global-hydrodynamics/cmf_v5_beta.git`, or select that branch before Download ZIP. State that the default/base branch is main and becomes the standard route after the maintainer's planned merge when v5b01 is ready. Explain beta assembly as an optional developer note, not formal release/model validation. Use a matching tutorial/data revision and a suitable local working directory.
2. Confirm the current development checkout root with `pwd`, define `cmf_root="$(pwd)"`, and inspect it with `ls -lF`. Explain that `/` marks directories and `*` normally marks executable files; suffixes are display markers, not part of filenames.
3. Prepare the Fortran and Python environments using the root setup scripts.
4. Activate `config/Mkinclude` by copying the reviewed staged `Mkinclude` manually; `config/` already exists.
5. From `${cmf_root}`, enter `src_main/` and run `make all` to build or update the current model executable.
6. Locate and list bundled map, runoff, input-dimension, and input-matrix files before relating their names to the GOSH settings.
7. Read `tutorial_design.md`, then inspect the plain-text standalone Tutorial01 GOSH configuration and its experiment settings.
8. From `tutorial/tutorial01-get_started/`, execute `./tutorial01-get_started.sh`; the default project output is `out/tutorial01-get_started/`.
9. Inspect the generated Namelist, logs, CTLs, model outputs, and Restart under the project-specific directory.

Map generation and visualization are not required.

## Acceptance criteria

- Running `make all` from `src_main/` returns zero and leaves an executable `MAIN_cmf`, whether it is newly built or updated.
- Section 0 identifies the v5 repository, distinguishes the current beta branch from main and the planned v5b01 merge, and documents two-stage beta assembly without claiming formal release or model validation.
- The root-directory demonstration uses `ls -lF`, with observed output showing directory and executable markers and an explanation that suffixes are not part of filenames.
- The standalone tutorial script defines the default `PROJ`, constructs its `RUNDIR` under `out/${PROJ}/`, does not call or source `gosh_test/mek01-default_run.sh`, and runs from its documented directory.
- Tutorial01 and the model return zero; `log_CaMa.txt` reaches normal calculation completion.
- Five expected daily Binary output variables and their CTLs, Namelist, logs, executable copy, and end Restart products are created under only `tutorial/tutorial01-get_started/out/tutorial01-get_started/`.
- Each daily output contains 40 records for the 40-day interval. The end time is exclusive; timestamp details follow the model's output convention.
- Bundled map, runoff, and matching input-matrix files remain unchanged.
- In a disposable checkout, the developer reset can remove build products and one explicitly selected Tutorial01 project directory while preserving `config/Mkinclude`, bundled inputs, the `out/` parent, and unrelated project directories.

Successful execution is operational evidence, not scientific validation.

# CaMa-Flood v5 beta

## Overview

CaMa-Flood (Catchment-based Macro-scale Floodplain) is a river hydrodynamics model for regional, continental, and global river and flood simulations. It routes runoff through a river network and represents river channels and floodplain storage using sub-grid topography. The model computes river discharge and flow velocity using the local inertial equation, and diagnoses water level and inundated area from water storage.

The repository includes adaptive time stepping, river bifurcations, reservoir operation, levee representation, upstream inflow and sea-level boundary options, and tools for diagnostic downscaling of flood depth. Optional extensions include water temperature and ice, tracers, and sediment transport. Their maturity, data requirements, and available combinations differ; consult the relevant documentation before enabling them.

## Getting Started

### Development repository and planned user package

This is the `global-hydrodynamics/cmf_v5_beta` development repository, based on `main`. Developers work in a clone or fork, with the tracked Mekong map and runoff samples under `map/` and `inp/`. After installing the compiler/libraries and configuring the build, the intended minimum workflow is compilation and a documented small Mekong test without Package Additional Data. Existing run instructions are in [Tutorial01](tutorial/tutorial01-get_started/manual_tutorial01-get_started.md) and [the developer workflow guide](gosh_test/README.md); a unified fresh-clone model regression command with independently approved references is still under development.

The distribution design has three components: **GitHub Repository** (code and approved small test data), **Package Additional Data** (separately versioned larger datasets), and **Distributed Package** (a generated, complete user package without Git history). The v5 package assembler, additional-data manifest and integrated package validation are planned; they are not available commands yet. The [maintained design specification](docs/development_and_distribution_design.md) distinguishes requirements, implementation status and open decisions. General users are the intended audience for the completed package; developers use this repository and [CONTRIBUTING.md](CONTRIBUTING.md).

Existing v4 downloads and version-specific manuals remain historical/user references, including the [official CaMa-Flood website](https://global-hydrodynamics.github.io/CaMa-Flood/), [v4.20 manual](doc/Manual_CaMa-Flood_v420.docx), and [legacy user guideline](doc/CaMa-Flood_Guideline.md). They do not establish v5 package availability. The v4 repository is maintained separately; do not apply v5 changes there.

The current v5 model is under `src_main/`, compiler templates under `config/`, execution checks under `gosh_test/`, tutorials under `tutorial/`, and plotting resources under `visualization/`. Legacy v4 `src/`, `gosh/`, and `adm/` are being relocated to the local `legacy/` reference tree; that reorganization is not yet committed. Do not use legacy build instructions as the v5 entry point.

[`variable_table/README.md`](variable_table/README.md) describes the map, output and Restart inventories. The [map guide](map/README.md) distinguishes the tracked Mekong development/test sample from larger separately supplied maps. Dataset availability does not by itself establish scientific validation or production suitability.

### Development environment setup

From the repository root, run the interactive setup scripts:

```bash
./s01-setup_fortran.sh
./s02-python_setup.sh
```

The Fortran script checks GNU Fortran, OpenMP, and a working NetCDF-Fortran installation, then can write a recommended machine-specific `./Mkinclude`. Review it before manually copying it to `config/Mkinclude`; it never changes the active v5 configuration or legacy `adm/Mkinclude`. The Python script creates or reuses the isolated repository `.venv/`, installs `requirements.txt`, and installs the included CMF Colormaps package from `visualization/cmf_colormap/` in editable mode. This makes `cmf_colormap` available to tutorials using that environment; packages are not installed into system Python. The repository-local `.venv` is the recommended Python setup, while researchers may keep an existing venv, Conda, or HPC-managed environment and configure it manually. The setup script does not modify external environments. Both setup scripts ask before creating or updating the environment and only diagnose when no terminal is attached. Activate the configured environment with `source .venv/bin/activate` before running Python tutorials. See the [Python environment guide](docs/python_environment.md) for both approaches and troubleshooting.

`mek01` uses Binary input data; the standard v5 build still enables NetCDF. `mek02` uses NetCDF runoff and map inputs. MPI is optional and remains disabled in the recommended configuration. Python 3.10 or newer is needed for Python utilities; specialist workflows may have additional dependencies documented in their component guides.

The optional ERA5-Land downloader also requires CDS account credentials and dataset terms acceptance. The legacy N-year flood-depth scripts and the GTSM preprocessing notebook use additional dependencies not included in the shared environment. Windows users should use WSL2 with Ubuntu for these shell workflows.

## Repository Structure

| Path | Responsibility |
| --- | --- |
| `legacy/` (local relocation in progress) | Historical v4 source, scripts and build settings; not a v5 entry point. |
| [config/](config/) | Separate v5 compiler and library configuration templates. |
| [src_main/](src_main/) | v5 model-source tree. |
| [gosh_test/](gosh_test/) | Developer-oriented v5 build, simulation, and operational verification workflows. |
| [tutorial/](tutorial/) | v5 tutorial specifications, executable examples, and learner-facing manuals. |
| [map/](map/) | River-map preprocessing, regionalization, river parameters, input mapping, and gauge/reservoir allocation. |
| [inp/](inp/) | Runoff forcing download and preparation tools. |
| [etc/](etc/) | Optional-scheme workflows, parameter preparation, downscaling, validation, and analysis. |
| [tools/](tools/) | Shared utilities: month-length helper and GrADS output/Restart descriptor generators (formerly `util/`). |
| [doc/](doc/) | Scientific manuals, user documentation, and package-preparation guidance. |
| [docs/](docs/) | Development coordination information. |
| [AGENTS.md](AGENTS.md) | Authoritative development rules for human developers and AI coding agents. |
| [Versions.md](Versions.md) | Source-code change history. |
| [README.md](README.md) | Introduction and navigation for the repository. |

Within `src_main/`, `cmf_drv_*` manages initialization, advancement, and finalization; `cmf_ctrl_*` coordinates model components; `cmf_calc_*` implements calculations; and `yos_cmf_*` holds shared configuration, state, map, time, and diagnostic variables. [MAIN_cmf.F90](src_main/MAIN_cmf.F90) is the stand-alone entry point. The main manual describes the core organization and hydrodynamic calculations.

## Documentation

The existing manuals remain the detailed scientific and workflow references. Their filenames identify applicable versions where available; they do not imply that all later extensions are covered.

| Topic | Documentation |
| --- | --- |
| Model formulation, basic setup, standard input/output, and execution | [Main manual, v4.20 (Word)](doc/Manual_CaMa-Flood_v420.docx); [user guideline](doc/CaMa-Flood_Guideline.md) |
| River parameters and runoff input matrices | [Map-parameter tools](map/src/src_param/README.md) |
| Runoff-to-map input matrix | [v5 Input Matrix generation workflow](map/tools/script_params/s03-generate_inpmat.sh) |
| Runoff forcing preparation | [ERA5-Land download and conversion](inp/ERA5-Land_download/README.md) |
| Reservoir operation | [Reservoir manual, v4.20 (Word)](doc/Manual_ReservoirOperation_v420.docx); [parameter-preparation workflow](map/src/src_dam/ReadMe.md) |
| Levee parameters | [Levee guide](doc/levee.md); [Word manual](doc/LeveeParameter.docx) |
| Upstream inflow | [Upstream inflow manual (Word)](doc/Mannual_UpstreamInflowScheme.docx) |
| MPI/OpenMP, precision, and high-performance computing | [HPC notes (Word)](doc/Note_HighPerformanceComputing.docx); [example workflows](etc/options_HPC/README.md) |
| River gauge allocation | [Gauge allocation manual (Word)](doc/Manual_AllocateRiverGauges.docx); [attribute-error supplement (Word)](doc/Supp_GaugeAttributeError.docx) |
| Flood-depth downscaling | [Workflow guide](etc/downscale_flddph/ReadMe.md); [method notes (Word)](doc/Note_Downscaling.docx) |
| Water temperature and ice | [Heatlink stability and diagnostics](src_main/heatlink/README.md) |
| Comparison with observations | [Validation examples](etc/validation/ReadMe.md) |
| Distribution preparation | [Package-creation guide](doc/HowTo_Make_Package.md) |

Small tests are located under [src_main/common/test/](src_main/common/test/), [src_main/mod/test/](src_main/mod/test/), [src_main/io/test/](src_main/io/test/), [src_main/phys/test/](src_main/phys/test/), and [src_main/heatlink/test/](src_main/heatlink/test/). Check their Makefiles and runners for dependencies and execution steps: some `test` targets only build executables. Native-grid remapping tests and integration-validation instructions are documented in its guide above.

## Development and Contributions

Start with [CONTRIBUTING.md](CONTRIBUTING.md) for feature branches, focused PRs and testing. Read [AGENTS.md](AGENTS.md) for development rules, AI-agent behavior, shared-project coordination and approval boundaries. Consult [docs/dev_status.md](docs/dev_status.md) for active-project coordination and the status-publication workflow defined in `AGENTS.md`.

For a worked example of designing and refining scientific tutorials with
conversational AI, repository-aware coding agents, and researcher review, see
[Guide01](tutorial/guide01_how_to_develop_tutorial/README.md).

## Versions and Releases

See [Versions.md](Versions.md) for recorded changes and the [official website](https://global-hydrodynamics.github.io/CaMa-Flood/) for distribution information. Source development and data-rich distribution packages are maintained separately; do not assume that `main` is identical to a particular downloadable package. The v5 package-generation workflow is still planned. For reproducible work, record the source commit or tag and the datasets used.

## Citation and License

Please cite the model description and numerical-method papers when using CaMa-Flood:

- Yamazaki, D. (2025). **Advancing global river hydrodynamics simulations by catchment-based macro-scale floodplain modeling approach.** *Geoscience Letters*, 12, 72. [doi:10.1186/s40562-025-00452-z](https://doi.org/10.1186/s40562-025-00452-z).
- Yamazaki, D., Kanae, S., Kim, H., & Oki, T. (2011). A physically based description of floodplain inundation dynamics in a global river routing model. *Water Resources Research*, 47, W04501. [doi:10.1029/2010WR009726](https://doi.org/10.1029/2010WR009726).
- Yamazaki, D., de Almeida, G. A., & Bates, P. D. (2013). Improving computational efficiency in global river models by implementing the local inertial flow equation and a vector-based river network map. *Water Resources Research*, 49(11), 7221–7235. [doi:10.1002/wrcr.20552](https://doi.org/10.1002/wrcr.20552).

When using the river water temperature model, also cite:

- Tokuda, D., Kim, H., Yamazaki, D., & Oki, T. (2019). Development of a global river water temperature model considering fluvial dynamics and seasonal freeze-thaw cycle. *Water Resources Research*, 55(2), 1366–1383. [doi:10.1029/2018WR023083](https://doi.org/10.1029/2018WR023083).

Use the [CaMa-Flood Zenodo archive](https://doi.org/10.5281/zenodo.4609654) to find and cite the specific archived software version used. The [official references](https://global-hydrodynamics.github.io/CaMa-Flood/#references--related-papers) provide additional model, scheme, and dataset publications.

The model source code is distributed under the [Apache License 2.0](LICENSE). Separately distributed river maps, forcing, and other datasets have their own licensing terms. Consult the terms supplied with each dataset and the [official licensing information](https://global-hydrodynamics.github.io/CaMa-Flood/#license-to-use-cama-flood-model); the software license does not grant rights to all accompanying data.

## Contact and Contributions

For package access and project inquiries, contact Dai Yamazaki at **yamadai [at] iis.u-tokyo.ac.jp**. Community discussion is available through the [CaMa-Flood user group](https://groups.google.com/g/cama-flood-user).

Report reproducible bugs or propose source-code improvements through [GitHub Issues](https://github.com/global-hydrodynamics/CaMa-Flood_v4/issues). Include the source revision, relevant configuration, environment, reproduction steps, and diagnostic output. Follow [AGENTS.md](AGENTS.md) when undertaking development work.

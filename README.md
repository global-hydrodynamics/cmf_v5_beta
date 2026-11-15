# CaMa-Flood v5 beta

**Under active development — this is a beta development repository, not an official stable release. Some features, workflows and documentation are incomplete or have not been fully validated.**

## Project Overview

CaMa-Flood (Catchment-based Macro-scale Floodplain) is a river hydrodynamics model for regional, continental and global river and flood simulations. It routes runoff through a river network, represents river channels and floodplain storage using sub-grid topography, computes discharge and flow velocity using the local inertial equation, and diagnoses water level and inundated area from water storage.

The model includes adaptive time stepping, river bifurcations, reservoir operation, levees, upstream inflow and sea-level boundaries, and diagnostic flood-depth downscaling. Optional extensions include water temperature and ice, tracers and sediment transport. Their presence in the source tree does not imply that every v5 configuration or combination is validated.

The v5 software effort aims to improve readability and maintainability, make external contributions easier, reproduce development/testing/distribution workflows, organize documentation, tutorials and visualization, and support collaboration between researchers and AI coding agents. These software goals are distinct from improving scientific accuracy; operational tests alone do not validate the model science.

## Development Status

| Category | Current status |
| --- | --- |
| Previously exercised | Earlier macOS checks cover stand-alone builds, selected Binary/NetCDF input/output and Restart paths, Mekong simulations, and Tutorial01. See the [model workflow evidence](docs/model_source_workflow_plan.md) and [Tutorial01 validation](research/records/validation_runs/VR-0126.md) for revisions and limits. |
| Under development | A current end-to-end fresh-clone workflow, independently approved model-regression references and broader platform/optional-feature coverage remain to be established. Earlier runs do not guarantee every current workflow. |
| Retained legacy | Historical v4 model/build/run files are tracked under `legacy/`. Legacy tools also remain in `etc/` and `map/src/`; some are still dependencies of current examples. |
| Planned | Versioned Package Additional Data, reproducible v5 user-package assembly and integrated package verification are not yet implemented as a complete workflow. |

Automated GitHub Actions checks are temporarily disabled pending a small, reproducible v5 regression suite. Existing checks remain available through the [manual validation guide](docs/migration_consistency_audit.md#manual-checks-retained-from-the-retired-workflow).

Current coordination is in [docs/dev_status.md](docs/dev_status.md); the [maintained design](docs/development_and_distribution_design.md) separates intended requirements from implementation. Dated project snapshots are labeled as historical; current work uses the migrated layout.

## Getting Started for Developers

Clone the development repository:

```bash
git clone https://github.com/global-hydrodynamics/cmf_v5_beta.git
cd cmf_v5_beta
```

Use Bash, GNU Make, GNU Fortran, NetCDF-Fortran (`nf-config`) and Python 3.10 or newer. The recommended GNU configuration enables OpenMP, NetCDF and single precision; MPI is disabled. See the [build guide](config/README.md) for toolchain installation and alternatives.

Run the interactive Fortran diagnostic/setup helper:

```bash
./s01-setup_fortran.sh
```

If it generates a root-level `Mkinclude`, review it and activate it as the ignored `config/Mkinclude` following the build guide. An existing active configuration must be reviewed before replacement. The helper does not activate it automatically. Complete this configuration step before building.

Prepare the repository-local Python environment, then build and run the basic experiment:

```bash
./s02-python_setup.sh
source .venv/bin/activate
./gosh_test/compile.sh
(cd gosh_test && ./mek01-default_run.sh)
```

The setup helpers ask before making local changes and only diagnose without an interactive terminal. Python setup installs `requirements.txt` and the bundled CMF Colormaps package into `.venv/`; existing external environments are supported through the [Python guide](docs/python_environment.md).

The basic experiment uses the tracked `map/mekong_15min/` map, daily Binary forcing in `inp/test-mek_1deg/`, and their matching input matrix. It runs 40 days from 2000-01-01 to 2000-02-10 (end exclusive), without the large additional-data package. Results go to `gosh_test/out/mek01/` (override the project with `PROJ`, or the complete path with `RUNDIR`); reruns replace this sample's known generated outputs. The script must run from `gosh_test/`, as shown above.

For settings and the two-year NetCDF example, see the [developer execution guide](gosh_test/README.md). For an explained first experiment, use the [Tutorial01 manual](tutorial/tutorial01-get_started/manual_tutorial01-get_started.md). Current v5 execution starts in `gosh_test/`, not the historical `legacy/gosh/`. The full current-revision clean-clone build/run/visualization sequence is not yet verified as an integrated procedure.

## Repository and Package Distribution

| Component | Role |
| --- | --- |
| **GitHub Repository** | Primary developer environment: source, configuration, documentation, tools and approved small Mekong test inputs. |
| **Package Additional Data** | Intended separately versioned global/regional maps, larger forcing and other approved data for extended tests and package assembly. The manifest and distribution workflow are still being designed. |
| **Distributed Package** | Intended complete product for general users, generated from a selected Git revision plus additional data, without `.git/` or Git history. The v5 assembler and verified package are not yet available. |

Existing v4 packages are separate versioned products; they are not v5 beta releases. See the [development and distribution design](docs/development_and_distribution_design.md) for data policy, reproducibility requirements and open decisions. Dataset-specific access and redistribution terms still apply.

## Repository Structure

| Directory | Role |
| --- | --- |
| [src_main/](src_main/) | Current v5 numerical model, drivers, I/O, shared state and optional components. |
| [config/](config/) | Fortran build templates; active `config/Mkinclude` is machine-specific and ignored. |
| [tools/](tools/) | Shared utilities, including `igetday` and output/Restart CTL generators; former root `util/` contents are integrated here. |
| [map/](map/) | Map tools, metadata and the Mekong test map; historical tools remain in `map/src/`. |
| [inp/](inp/) | Runoff preparation tools, metadata and tracked small forcing samples. |
| [gosh_test/](gosh_test/) | Current developer build/run workflows and separately labeled legacy examples. |
| [tutorial/](tutorial/) | Reproducible experiment examples, specifications and learner manuals. |
| [visualization/](visualization/) | Map/output visualization projects, shared plotting resources and Figure Gallery. |
| [variable_table/](variable_table/) | Map, model-output and Restart variable inventories. |
| [docs/](docs/) | Current design, workflow and development-status documents. |
| [research/](research/) | Evidence-linked development history, decisions and validation records. |
| [legacy/](legacy/) | Historical v4 `src/`, `gosh/` and `adm/`, moved from the root and retained as references. |
| [etc/](etc/) | Retained legacy extensions, processing and validation tools; selected current workflows still use them. |
| [doc/](doc/) | Scientific manuals and historical user/package documentation. |

The root `requirements.txt` defines shared Python dependencies. New v5 model work belongs in `src_main/`; see its [source guide](src_main/README.md). Neither the legacy relocation nor the utility consolidation means all old workflows have been migrated.

## Tutorials and Visualization

[Tutorials](tutorial/README.md) teach model use through reproducible experiments. Tutorial01 provides a beginner manual and short Mekong run. [Tutorial02](tutorial/tutorial02-mekong_netcdf_4exp/README.md) provides a multi-year NetCDF experiment and comparison workflow; earlier four-experiment execution is recorded in [VR-0123](research/records/validation_runs/VR-0123.md), while its full learner manual remains unfinished. [Guide01](tutorial/guide01_how_to_develop_tutorial/README.md) documents researcher/AI-assisted tutorial development.

The [Visualization Gallery](visualization/README.md) links [river-map examples](visualization/river_map/README.md) and [model-output analysis](visualization/output_analysis/README.md), including discharge, flooded area and flood depth. These projects provide a structure for adding further examples; use their own input and execution instructions rather than assuming every entry point runs from a fresh clone.

In particular, some output-visualization entry points re-extract data from annual model outputs under `out/`, even when compact samples are tracked. Guide01 and flood-depth visualization also use the Fortran downscaler in `etc/downscale_flddph/`. Additional experiments can need external data or locally generated results; incomplete path/dependency work is described in the [design's implementation status](docs/development_and_distribution_design.md#11-current-implementation-boundary-2026-11-15).

## Contributing

Develop an independent contribution on a feature branch, run appropriate checks, review and commit only intended changes, and submit a PR against `main`. Maintainers review and can independently test the branch before merging. [CONTRIBUTING.md](CONTRIBUTING.md) explains the workflow, existing component-test commands and minimal versus extended testing; [AGENTS.md](AGENTS.md) defines shared-project coordination and AI-agent instructions. More specific guides for bug fixes, schemes, tutorials and Gallery contributions are planned.

## Documentation and Legacy References

The v4 manuals remain useful scientific background and records of earlier interfaces. Their execution commands and directory layouts are not the standard v5 instructions. Use the current guides above for v5 setup and the references below for their documented versions.

| Topic | References |
| --- | --- |
| Model formulation and historical usage | [Main manual, v4.20](doc/Manual_CaMa-Flood_v420.docx); [legacy user guideline](doc/CaMa-Flood_Guideline.md) |
| Maps, parameters and runoff | [Current map guide](map/README.md); [current runoff guide](inp/README.md); [legacy parameter tools](map/src/src_param/README.md) |
| Reservoirs and levees | [Reservoir manual](doc/Manual_ReservoirOperation_v420.docx); [legacy preparation](map/src/src_dam/ReadMe.md); [levee guide](doc/levee.md); [levee manual](doc/LeveeParameter.docx) |
| Upstream inflow and HPC | [Upstream inflow manual](doc/Mannual_UpstreamInflowScheme.docx); [HPC notes](doc/Note_HighPerformanceComputing.docx); [legacy HPC examples](etc/options_HPC/README.md) |
| Gauge allocation | [Allocation manual](doc/Manual_AllocateRiverGauges.docx); [attribute-error supplement](doc/Supp_GaugeAttributeError.docx) |
| Downscaling and observations | [Downscaling workflow](etc/downscale_flddph/ReadMe.md); [method notes](doc/Note_Downscaling.docx); [legacy validation examples](etc/validation/ReadMe.md) |
| Water temperature and ice | [Heatlink diagnostics](src_main/heatlink/README.md); optional v5 configurations require separate validation. |
| Distribution and history | [Current distribution design](docs/development_and_distribution_design.md); [historical v4 package guide](doc/HowTo_Make_Package.md); [Versions.md](Versions.md); [research records](research/README.md) |

Record the source revision, build configuration and datasets for reproducible work. The [official website](https://global-hydrodynamics.github.io/CaMa-Flood/) provides published model/distribution information; repository `main` is not a stable release identifier.

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

Report reproducible bugs or propose source-code improvements through [GitHub Issues](https://github.com/global-hydrodynamics/cmf_v5_beta/issues). Include the source revision, relevant configuration, environment, reproduction steps, and diagnostic output. Follow [AGENTS.md](AGENTS.md) when undertaking development work.

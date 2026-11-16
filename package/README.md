# CaMa-Flood v5 Package Builder

Status: planning / under development. This directory is the temporary development workspace for package-building scripts, configuration and documentation. The dataset catalog records runoff and global-map selections; no installer or package-generation script is implemented yet.

## Working-directory layout

```text
work/
├── cmf_v5_beta/              # Git development repository
│   ├── src_main/
│   ├── map/
│   ├── inp/
│   ├── tools/
│   └── package/              # Package Builder workspace (current location)
├── cmf_v5_package_data/      # Authoritative additional data, outside Git
│   ├── map/
│   └── inp/
└── cmf_v5b01_pkg/            # Independently generated beta 01 package
```

The names above describe the intended sibling layout, not hard-coded local paths. Each package version has its own output directory.

## Principles

- Track Package Builder scripts, configuration and this README in the repository's root `package/` directory. Do not create `tools/package/` at this stage; reconsider that location after the build environment stabilizes.
- Keep the authoritative additional data outside the development repository in `cmf_v5_package_data/`. It is not Git-managed for now.
- Match additional-data paths to their package destinations: for example, copy `cmf_v5_package_data/map/glb_15min/` to `cmf_v5b01_pkg/map/glb_15min/`.
- Allow additional data to be copied or linked into local development `map/` and `inp/` directories for convenience, while excluding those additions from Git tracking. The initial ELSE_GPCC installation uses real copies excluded through `inp/.gitignore`; automated installation remains planned.
- Generate packages from Git-managed source files plus the authoritative external data. Locally installed additional data in the development repository are not authoritative package inputs.
- Preserve source data and generate the package in an independent output directory.
- Future scripts must derive the repository root from their own location and avoid embedded absolute paths, so relocation remains possible.

## Planned tools

- `install_package_data.sh`: copy or link additional data into the development checkout.
- `make_package.sh`: assemble Git-managed files and authoritative additional data into a distribution package.
- `package_data.csv`: the current authoritative dataset catalog; future scripts will use it.

Detailed behavior will be specified in separate tasks. The broader product roles are described in [the development and distribution design](../docs/development_and_distribution_design.md); `package/` is the current approved tooling location.

## Dataset catalog

[package_data.csv](package_data.csv) is the authoritative additional-data catalog. Each row describes one dataset, not one annual file.

| Column | Meaning |
| --- | --- |
| dataset_id | Unique dataset identifier. |
| source_path | Relative dataset directory under cmf_v5_package_data/. |
| target_path | Relative destination under the development or distribution root. |
| file_pattern | Dataset-relative Python `Path.glob` pattern selecting files; `**/*` includes files recursively, including map-root files. |
| format | Data format. |
| description | Purpose and known coverage; registration is not content validation. |

The initial ELSE_GPCC row selects runoff*.nc for 1979–2010. The conversion script beside those data is not selected or copied. To register a dataset, add a unique row with relative paths, the intended pattern, format and description; ensure local installation paths are ignored before copying and do not overwrite existing files without approval.

cmf_v5_beta/ is the Git development checkout, cmf_v5_package_data/ holds authoritative additional data outside Git, and cmf_v5b01_pkg/ is the independently generated distribution. Preserve original datasets. install_package_data.sh and make_package.sh will later automate catalog-driven copying; neither script nor a distribution package is created in this task.

## Global 15-minute map selection

The `glb_15min` dataset row uses `source_path=map/glb_15min`,
`target_path=map/glb_15min`, and `file_pattern=**/*`. The source is relative to
the external `cmf_v5_package_data/` root, never the local checkout's map copy.

| Include | Exclude |
| --- | --- |
| Model-grid `.bin`, `netcdf/`, and standard parameter products | High-resolution Binary `1min/` |
| Compressed `1min_nc/` including `location.txt` | `script*/`, `src*/`, `code/` and generation source files |
| Observation/station information, bifurcation products, CTL and auxiliary text | Build products, logs, temporary files, caches and `.DS_Store` |

**Distribution format: compressed NetCDF** for high-resolution maps.
**Legacy-compatible working format: Binary generated on demand.** Use the
[high-resolution restoration tool](../map/tools/script_bin2nc/README.md#restore-high-resolution-binary-working-files-s04)
when legacy processing needs Binary. Do not package both `1min/` and `1min_nc/`.
Model-grid Binary remains included, alongside model-grid NetCDF. This first
selection does not prune generated standard products or change the Input Matrix
format; further data reduction and Input Matrix NetCDF are separate work.

### Exclusion semantics and implementation boundary

The catalog retains its existing six-column schema. `file_pattern` identifies
candidate files, but cannot itself express the exclusion policy above. The
`glb_15min` description explicitly refers here for the required filtering;
`**/*` must not be treated as permission to copy the entire source blindly.
The existing ELSE_GPCC row still selects only `runoff*.nc`.

For a future implementation, the minimal proposed extension is one optional
`exclude_patterns` column, rather than another configuration file or copy
routine. The proposed patterns are:

```text
1min/;script*/;src*/;code/;__pycache__/;.git/;*.sh;*.bash;*.csh;*.ksh;*.py;*.pyc;*.F90;*.f90;*.F;*.f;*.c;*.cpp;Makefile*;*.o;*.mod;*.log;*.tmp;.DS_Store
```

Proposed semantics: split on `;`; patterns ending in `/` match relative parent
directory components with case-sensitive shell-style `fnmatch` rules and exclude
their descendants. Other patterns match basenames at any depth. Thus `1min/`
never excludes `1min_nc/`, and `.bin` is not a blanket exclusion. This column
has **not** been added; approve that schema extension when implementing the
assembler, or implement the documented filtering another explicitly reviewed
way. An assembler must not claim support for this row until it applies the
inclusion/exclusion policy. The read-only registration inventory applies those
documented rules, not a package-building command.

There is currently no installer or package assembler to update or execute.
These are explicit selection requirements for those planned tools,
not an implemented package-generation command. Do not add a second copy routine
or another selection configuration alongside this catalog.

Resolve the default store as the logical sibling `../cmf_v5_package_data/`
relative to the checkout, permitting that directory to be a symbolic link.
Do not embed the resolved Dropbox location. A future installer/assembler must
report an inaccessible store or missing registered dataset as an error; it must
not create substitute data, fall back to the local map copy or silently skip a
registered source. It must read sources without modification and write only to
an independent destination. Catalog selection is not licence clearance: record
source provenance, redistribution terms and attribution before distribution.

GitHub maintains the small Mekong sample and shared generators under `map/tools/`.
The ignored `map/glb_15min/` checkout copy is neither authoritative package input
nor the home for the only copy of a maintained generator. No tracked files were
found under that path during registration, so no index removal was required.

## Authoritative README for the additional-data store

[PACKAGE_DATA_README.md](PACKAGE_DATA_README.md) is the Git-managed source of the explanatory README intended for `../cmf_v5_package_data/README.md` (relative to the development repository root). Maintain it here, not directly in the external store. Copying it to the store is a separate, explicitly assigned operation; this documentation change does not perform that copy.

When registering or changing a dataset, update [package_data.csv](package_data.csv) and, when descriptions, provenance or conditions change, PACKAGE_DATA_README.md. The catalog selects dataset files; the README explains their role, source, conversion and unresolved redistribution conditions. See [AGENTS.md](../AGENTS.md) for the agent rule.

NetCDF dataset directories normally omit `_nc`; Binary variants use `_bin` when a distinction is needed. The global NetCDF dataset was renamed from `ELSE_GPCC_nc/` to `ELSE_GPCC/` in both the development repository and the additional-data store. The former global Binary directory has been removed.

# CaMa-Flood v5 Package Builder

Status: planning / under development. This directory is the temporary development workspace for package-building scripts, configuration and documentation. The dataset catalog is initialized; no installer or package-generation script is implemented yet.

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
| file_pattern | Filename pattern selecting files within the source directory. |
| format | Data format. |
| description | Purpose and known coverage; registration is not content validation. |

The initial ELSE_GPCC row selects runoff*.nc for 1979–2010. The conversion script beside those data is not selected or copied. To register a dataset, add a unique row with relative paths, the intended pattern, format and description; ensure local installation paths are ignored before copying and do not overwrite existing files without approval.

cmf_v5_beta/ is the Git development checkout, cmf_v5_package_data/ holds authoritative additional data outside Git, and cmf_v5b01_pkg/ is the independently generated distribution. Preserve original datasets. install_package_data.sh and make_package.sh will later automate catalog-driven copying; neither script nor a distribution package is created in this task.

## Authoritative README for the additional-data store

[PACKAGE_DATA_README.md](PACKAGE_DATA_README.md) is the Git-managed source of the explanatory README intended for `../cmf_v5_package_data/README.md` (relative to the development repository root). Maintain it here, not directly in the external store. Copying it to the store is a separate, explicitly assigned operation; this documentation change does not perform that copy.

When registering or changing a dataset, update [package_data.csv](package_data.csv) and, when descriptions, provenance or conditions change, PACKAGE_DATA_README.md. The catalog selects dataset files; the README explains their role, source, conversion and unresolved redistribution conditions. See [AGENTS.md](../AGENTS.md) for the agent rule.

NetCDF dataset directories normally omit `_nc`; Binary variants use `_bin` when a distinction is needed. The global NetCDF dataset was renamed from `ELSE_GPCC_nc/` to `ELSE_GPCC/` in both the development repository and the additional-data store. The former global Binary directory has been removed.

# CaMa-Flood v5 — Additional Package Data

This repository-external store contains authoritative additional datasets used to construct CaMa-Flood v5 distribution packages. It is maintained separately from the Git development repository and is not Git-managed for now.

## Relationship to development and distribution

```text
work/
├── cmf_v5_beta/                # Git-managed development sources and package tools
├── cmf_v5_package_data/        # Authoritative additional datasets (this store)
│   ├── inp/ELSE_GPCC/
│   ├── map/glb_15min/
│   └── map/TE-Japan_01min/
└── cmf_v5b01_pkg/              # Independently generated distribution package
```

The authoritative selection catalog is `cmf_v5_beta/package/package_data.csv`. Its relative source and target paths describe where selected files belong. Local copies in the development checkout are for convenience and are not authoritative inputs for package generation. Original datasets in this store must not be modified by installation or package-building scripts.

## Available datasets

### inp/ELSE_GPCC/

| Item | Description |
| --- | --- |
| Dataset | Global ELSE_GPCC runoff forcing |
| Period | 1979–2010 inclusive, 32 years |
| Format | NetCDF-4, one file per year |
| Data files | `runoff1979.nc` through `runoff2010.nc` |
| Generation script | `s00-convert_binary_to_netcdf.py`, retained beside the data |
| Catalog selection | `runoff*.nc`; the generation script is not selected by this pattern |

The period and file inventory have been identified, but NetCDF contents, value equivalence, precision and compression settings have not been independently validated in this catalog-initialization work.

### map/glb_15min/

Global 15-minute model maps are supplied as additional package data. Their
authoritative source is `cmf_v5_package_data/map/glb_15min/`; GitHub holds the
small Mekong sample and generation/conversion tools. Local checkout copies are
not authoritative package inputs.

The catalog includes model-grid Binary, model-grid `netcdf/`, standard generated
parameter data, observation/station information, bifurcation products and other
auxiliary text. High-resolution `1min_nc/` plus its `location.txt` are distributed
as compressed NetCDF; `1min/` Binary is excluded and can be restored on demand
with `cmf_v5_beta/map/tools/script_bin2nc/s04-restore_highres_binary.sh`. Do not
include both high-resolution formats. Generation directories (`script*/`,
`src*/`, `code/`), script/source files and temporary/build/log files are excluded
by the selection policy in `cmf_v5_beta/package/README.md`; the optional final
`exclude_patterns` CSV column encodes these rules for both Import and Diff. Existing standard `.bin` products are
not removed by those exclusions. Input Matrix format and further data pruning
are deferred to a later round.

This registration does not alter the stored data or establish scientific
validation. Map-product provenance, redistribution permissions and required
attribution still need to be assembled before distributing a package. A previous
package's contents alone do not establish redistribution permission.

### map/TE-Japan_01min/

Japan 1-minute model maps are additional package data, with authoritative
source `cmf_v5_package_data/map/TE-Japan_01min/`. The model grid has 1500 × 1320
cells over 123–148°E, 24–46°N (`params.txt`). Model-grid Binary, `netcdf/`,
standard parameter products, station/bifurcation information and auxiliary
text are included. High-resolution distribution uses compressed `15sec_nc/`
with `location.txt`; `15sec/` Binary is excluded and restored only when needed.
Generation directories, scripts and build/log/temporary files are excluded
according to `cmf_v5_beta/package/README.md`. Any Git-managed map-specific workflows are protected from Import; the local
data copy is ignored.

This registration does not change the data or validate its contents. The
upstream source edition, processing provenance, redistribution conditions and
required attribution are not yet confirmed here and must be recorded before
package distribution. No new download URL is asserted by this registration.

## ELSE_GPCC source, conversion and redistribution

The source product is ELSE_GPCC runoff. Existing project documentation associates it with Kim et al. (2009), [doi:10.1029/2009GL039006](https://doi.org/10.1029/2009GL039006). The exact upstream edition and complete processing provenance still need to be recorded; a citation alone is not a redistribution permission record.

The conversion workflow reads daily global Binary runoff and creates annual NetCDF files without spatial extraction. The original Binary contract is 360 × 180 little-endian Float32 values per day. The generation script is stored with the archive for provenance. Its actual revision, invocation, precision/quantization options and validation results for these files remain to be documented; do not assume lossless conversion or approved numerical accuracy from the filenames alone.

Redistribution conditions for this global archive are **not yet confirmed in this description**. Record the applicable license/permission, required attribution and maintainer approval before selecting it for actual distribution. Catalog registration or local availability does not resolve those conditions.

## Management and updates

- Maintain the explanatory source at `cmf_v5_beta/package/PACKAGE_DATA_README.md` in Git. This file is intended to be copied to `cmf_v5_package_data/README.md`; it is not independently authored here.
- Agents should not directly edit this repository-external store by default. Data placement, replacement and README copying require a separately assigned operation.
- Register or revise datasets in `cmf_v5_beta/package/package_data.csv`, and update the Git-managed README source when the description, provenance, coverage or terms change.
- Keep dataset directories aligned with their intended package destinations, for example `inp/ELSE_GPCC/` under both data and package roots.
- Preserve original data. Do not silently overwrite existing files; retain generation/version and validation evidence when datasets are revised.
- Development copies must be excluded through dataset-local Git ignore rules (`inp/.gitignore` and `map/.gitignore`). Do not commit the large data to the development repository.
- Developer Import and read-only Diff are implemented in `cmf_v5_beta/package/install_package_data.sh` and `diff_package_data.sh`. Import creates ordinary editable local copies and never deletes target-only files. Both use the same catalog selection/exclusions, leaving this store unchanged. Distribution assembly remains planned.

The logical sibling `cmf_v5_package_data/` may be a symbolic link to externally
managed storage. Tools must use that logical location without hard-coded
Dropbox paths and must clearly fail if it or a required dataset is inaccessible;
no data should be generated or copied as an implicit fallback. Developer Import and Diff use that location by default, with `--source` for an
alternative store. Distribution-package assembly remains unimplemented.

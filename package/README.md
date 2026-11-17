# CaMa-Flood v5 Package Builder

Status: developer Import and read-only Diff are implemented. This root directory holds the Package Builder tools, catalog and documentation. Distribution-package assembly (`make_package.sh`) is still planned and is not implemented.

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
- Allow additional data to be copied or linked into local development `map/` and `inp/` directories for convenience, while excluding those additions from Git tracking. Import creates editable real files excluded through `inp/.gitignore` and `map/.gitignore`; it never installs dataset symlinks.
- Generate packages from Git-managed source files plus the authoritative external data. Locally installed additional data in the development repository are not authoritative package inputs.
- Preserve source data and generate the package in an independent output directory.
- Future scripts must derive the repository root from their own location and avoid embedded absolute paths, so relocation remains possible.

## Tools

- `install_package_data.sh`: one-time developer setup, copying selected data into this checkout.
- `diff_package_data.sh`: independently compare authoritative data and local development copies.
- `package_data.py`: shared selection, bounded-memory comparison and safe copying (Python standard library).
- `package_data.csv`: the sole dataset selection catalog, used by both commands.
- `make_package.sh`: future independent distribution assembler; **not implemented**.

The commands require Bash, Python 3.8 or newer, and Git. No scientific Python packages or rsync are required. The broader product roles are described in [the development and distribution design](../docs/development_and_distribution_design.md); `package/` is the current approved tooling location.

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
| exclude_patterns | Optional final column; semicolon-separated directory-component or basename exclusions (see below). |

The initial ELSE_GPCC row selects runoff*.nc for 1979–2010. The conversion script beside those data is not selected or copied. To register a dataset, add a unique row with relative paths, the intended pattern, format and description; ensure local installation paths are ignored before copying and do not overwrite existing files without approval.

cmf_v5_beta/ is the Git development checkout, cmf_v5_package_data/ holds authoritative additional data outside Git, and cmf_v5b01_pkg/ is the future independently generated distribution. Import changes only the local development copies. A generated distribution is not produced by these tools.

## Import and Diff commands

Commands locate the checkout from their own script directory, independently of
current working directory. The default source is the logical sibling
`../cmf_v5_package_data/`; a symlink at that store root is supported. Never hard-code
an external-storage location. Use `--source` if the sibling is not available:

```bash
./package/diff_package_data.sh
./package/diff_package_data.sh --source /path/to/cmf_v5_package_data --details
./package/diff_package_data.sh --dataset glb_15min --output /tmp/data_diff.csv
./package/install_package_data.sh --dry-run
./package/install_package_data.sh --source /path/to/cmf_v5_package_data
./package/install_package_data.sh --dataset glb_15min
```

`--dataset` accepts a catalog ID and may be repeated. Every selected source dataset
must exist and select at least one file; missing products are errors, not silent
fallbacks. The three registered datasets are selected by default. `--details`
prints per-dataset selected source counts/bytes and all status/file lists.

Diff compares file size and successive 1 MiB byte chunks, never mtime alone.
Binary/NetCDF contents are compared as files, without decoding scientific fields.
It reports:

| Status | Meaning / Import action |
| --- | --- |
| IDENTICAL | Same content; skip. |
| MODIFIED | Content differs; require overwrite approval. |
| SOURCE_ONLY | Missing locally; copy after confirmation. |
| TARGET_ONLY | Local file absent from the source selection; retain unchanged. |

Use Diff during development to investigate whether local changes/additions have
not been reflected in Additional Data. It does not infer their scientific meaning,
merge them or write back to the authoritative store. Diff never changes data.
`--output` writes only the explicitly requested CSV report (dataset_id, status,
repository-relative path, source_size, target_size). Reports must be outside the
source store and all catalog target datasets; tracked files and Git metadata
cannot be overwritten. Diff returns 0 even when differences exist.

### Import confirmation and failure handling

Import always performs and prints Diff before copying. It prints candidate file
counts/bytes and skipped/retained counts. With no conflicts, confirm new copies
with `[y/N]`. With differing existing files, answer these two questions:

1. `Overwrite existing files? [y/N]`: No cancels the entire Import, including new files.
2. `Ask before overwriting each differing file? [Y/n]`: Yes asks for each file, showing
   its source/target sizes; each `[y/N]` defaults to skip. No overwrites all conflicts.

All approvals are collected before copying begins. Identical files never prompt.
Declined individual files and TARGET_ONLY files remain unchanged. Nothing is deleted
from the source or target dataset. This is a one-time setup tool, not synchronization
or a history/merge system; later local edits are normal and can be inspected with Diff.

In a pipe/CI, missing interactive approval fails before copying. `--yes` explicitly
approves new-file imports only and **does not approve conflicts**. The separate
`--overwrite-all` explicitly approves all new and differing files without prompts;
use it only after reviewing Diff. `--dry-run` never prompts or writes, and shows
new files, conflicts, sizes and free-space errors. Neither flag bypasses safety checks.

Import refuses Git-tracked destination files/ancestors even if identical or an
overwrite was approved. All source-selected destinations must be ignored by Git;
otherwise fix the dataset-local ignore rule and review the catalog before retrying.
No Git index or ignore files are changed automatically. The small Mekong fixtures
are not catalog targets and remain untouched. Excluded map-generation scripts
are neither overwritten nor presented as missing Additional Data.

Paths must be safe relative paths with no `..`, absolute paths or `.git` traversal.
Source/checkout roots must be independent, with neither containing the other.
The store-root symlink is allowed; links inside datasets or destination paths are
rejected rather than followed. Excluded directories are pruned before traversal.
Use actual dataset files inside the store and ordinary destination directories.

Each file is streamed into a temporary file in the destination directory, flushed,
verified against source size/content, made owner-editable, then atomically replaced.
A failed copy/verification retains that file's original contents and removes its
temporary file. Successful earlier files may remain after a later failure; there
is no whole-dataset rollback. Correct the error and rerun Diff/Import. Identical
completed files will skip. Obvious free-space shortages are detected before copying,
including space for the temporary file; disk/full/permission errors can still occur
later. Avoid concurrent edits during comparison/import; detected source/target
metadata changes cause an error and require a fresh Diff. Files do not need to be
loaded into memory in full; the intended total is at most about 10 GB.

Exit status: 0 success, 1 user cancellation, 2 validation/I/O/noninteractive-approval
error, 130 interrupted. Missing source: supply `--source` or install the external
store separately. Missing dataset: check its catalog-relative source path. Unsafe,
tracked or unignored target: correct the catalog/layout/ignore rule, rather than
forcing an overwrite. No failure generates substitute scientific data.

### Tests

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s package/tests -v
bash -n package/install_package_data.sh package/diff_package_data.sh
```

The tests use small temporary Git repositories and synthetic bytes; they cover
selection, four statuses, confirmation/CI behavior, non-ASCII paths, symlinks,
Git protection, verification/partial-copy failures and disk-space checks. They
never import or modify real scientific data. Package generation and scientific
content validation are outside this implementation.

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
[high-resolution restoration tool](../map/tools/script_format_conv/README.md#restore-high-resolution-binary-working-files-s04)
when legacy processing needs Binary. Do not package both `1min/` and `1min_nc/`.
Model-grid Binary remains included, alongside model-grid NetCDF. This first
selection does not prune generated standard products or change the Input Matrix
format; further data reduction and Input Matrix NetCDF are separate work.

### Exclusion semantics and implementation boundary

The catalog retains all six original columns and adds optional `exclude_patterns`
as the final column. This is the only selection configuration; no parallel manifest
or dataset registry is introduced. `file_pattern` selects candidate regular files;
`exclude_patterns` then filters them on both source and target, including
TARGET_ONLY discovery. The glb_15min row uses exactly the existing policy:

```text
1min/;script*/;src*/;code/;__pycache__/;.git/;*.sh;*.bash;*.csh;*.ksh;*.py;*.pyc;*.F90;*.f90;*.F;*.f;*.c;*.cpp;Makefile*;*.o;*.mod;*.log;*.tmp;.DS_Store
```

Split exclusions on `;`. Patterns ending in `/` match relative parent directory
components using case-sensitive shell-style `fnmatch` rules; all descendants are
excluded and not traversed. Other patterns match a file basename at any depth.
Thus `1min/` never excludes `1min_nc/`; `15sec/` never excludes `15sec_nc/`.
Model-grid `.bin` products remain included. Empty/absent exclude_patterns means no
exclusions; six-column catalogs remain readable. Keep the approved map exclusions
when editing the catalog: `**/*` alone is not the map-selection policy.

Resolve the default store as the logical sibling `../cmf_v5_package_data/`
relative to the checkout, permitting that directory to be a symbolic link.
Do not embed the resolved Dropbox location. The tools
report an inaccessible store or missing registered dataset as an error. They
never create substitute data, fall back to the local map copy or silently skip a
registered source. They read sources without modification and write only to
an independent destination. Catalog selection is not licence clearance: record
source provenance, redistribution terms and attribution before distribution.

GitHub maintains the small Mekong sample and shared generators under `map/tools/`.
The ignored `map/glb_15min/` checkout copy is neither authoritative package input
nor the home for the only copy of a maintained generator. No tracked files were
found under that path during registration, so no index removal was required.

## Japan 1-minute map selection

The entire local `map/TE-Japan_01min/` installation is Git-ignored, just like
`map/glb_15min/`, including local script copies. Use the maintained templates
under `map/tools/`; this tracking policy does not change catalog selection.

`TE-Japan_01min` uses relative source and target `map/TE-Japan_01min`
and candidate pattern `**/*`. The authoritative source is the external
`cmf_v5_package_data/map/TE-Japan_01min/`, including when the store is a
symbolic link. Its `params.txt` specifies 1500 × 1320 model cells, 1-minute
spacing, 123–148°E and 24–46°N. Supporting high-resolution data use 15 seconds,
not 1 minute.

Apply the same selection policy as the global map above, substituting
`15sec_nc/` (include, with `location.txt`) and `15sec/` (exclude). Include
model-grid Binary, `netcdf/`, standard parameter products, station/bifurcation
information and auxiliary text. Exclude generation directories and sources,
build products, logs, caches and temporary files. The exclude_patterns column
implements this same policy, replacing `1min/` with `15sec/`.
Do not copy `**/*` without this filtering. Restore high-resolution Binary on
demand with the shared restoration tool and `HIRES="15sec"`.

Any Git-managed map-specific workflows are protected; excluded scripts/source
files are not imported or reported as missing data. Shared maintained generators
remain under `map/tools/`. Installed data are excluded by `map/.gitignore`;
existing Git history is preserved. The
external data store is not modified by this registration. Source edition,
redistribution conditions and required attribution remain to be confirmed;
registration and local availability are not validation or permission to publish.

## Authoritative README for the additional-data store

[PACKAGE_DATA_README.md](PACKAGE_DATA_README.md) is the Git-managed source of the explanatory README intended for `../cmf_v5_package_data/README.md` (relative to the development repository root). Maintain it here, not directly in the external store. Copying it to the store is a separate, explicitly assigned operation; this documentation change does not perform that copy.

When registering or changing a dataset, update [package_data.csv](package_data.csv) and, when descriptions, provenance or conditions change, PACKAGE_DATA_README.md. The catalog selects dataset files; the README explains their role, source, conversion and unresolved redistribution conditions. See [AGENTS.md](../AGENTS.md) for the agent rule.

NetCDF dataset directories normally omit `_nc`; Binary variants use `_bin` when a distinction is needed. The global NetCDF dataset was renamed from `ELSE_GPCC_nc/` to `ELSE_GPCC/` in both the development repository and the additional-data store. The former global Binary directory has been removed.

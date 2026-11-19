# CaMa-Flood v5 Package Builder

Status: clean-source extraction, beta distribution-directory assembly, developer Import and read-only Diff are implemented. This root directory holds the Package Builder tools, catalog and documentation. Local assembly does not authorize public redistribution or establish scientific runtime validity.

## Working-directory layout

```text
work/
├── cmf_v5_beta/              # Git development repository
│   ├── src_main/
│   ├── map/
│   ├── inp/
│   ├── tools/
│   └── package/              # Tools, repo_clean_${VER}/ and cmf_${VER}_pkg/
├── cmf_v5_package_data/      # Authoritative additional data, outside Git
│   ├── map/
│   └── inp/
└── ...                      # Additional external work directories, if needed
```

The names above describe the intended sibling layout, not hard-coded local paths. Each package version has its own independent output directory under package/.

## Principles

- Track Package Builder scripts, configuration and this README in the repository's root `package/` directory. Do not create `tools/package/` at this stage; reconsider that location after the build environment stabilizes.
- Keep the authoritative additional data outside the development repository in `cmf_v5_package_data/`. It is not Git-managed for now.
- Match additional-data paths to their package destinations: for example, copy `cmf_v5_package_data/map/glb_15min/` to `cmf_v5b01_pkg/map/glb_15min/`.
- Allow additional data to be copied or linked into local development `map/` and `inp/` directories for convenience, while excluding those additions from Git tracking. Import creates editable real files excluded through `inp/.gitignore` and `map/.gitignore`; it never installs dataset symlinks.
- Generate packages from Git-managed source files plus the authoritative external data. Locally installed additional data in the development repository are not authoritative package inputs.
- Preserve source data and generate the package in an independent output directory.
- Future scripts must derive the repository root from their own location and avoid embedded absolute paths, so relocation remains possible.

## Numbered workflow

Generated metadata belongs inside each output tree's `package/` directory:
`repo_clean_${VER}/package/PACKAGE_BUILD_INFO.txt` is retained as
`cmf_${VER}_pkg/package/PACKAGE_BUILD_INFO.txt`, and assembly writes
`cmf_${VER}_pkg/package/PACKAGE_MANIFEST.json`. Neither is written at the output
root. Recreate old clean trees with `p01` before using `p02`; existing outputs
are never moved or overwritten automatically.


- `s00-diff_package_data.sh`: compare additional data and local development copies (read-only).
- `s01-install_package_data.sh`: import selected additional data into the development checkout when needed.
- `p01-archive_clean_repo.sh`: extract committed source for the chosen package version.
- `p02-make_package.sh`: assemble that clean source with the authoritative additional data.

The `s` commands support local development; package creation uses `p01` then
`p02`. Commit intended source/document changes before `p01`, and use the same
`VER` for both package steps. An Import run is not required before assembly;
`p02` reads the external additional-data store directly. Number prefixes apply
only to Shell entry points; Python helper names are unchanged.

## Tools

- `s01-install_package_data.sh`: one-time developer setup, copying selected data into this checkout.
- `s00-diff_package_data.sh`: independently compare authoritative data and local development copies.
- `package_data.py`: shared selection, bounded-memory comparison and safe copying (Python standard library).
- `package_data.csv`: the sole dataset selection catalog, used by both commands.
- `p01-archive_clean_repo.sh`: extract committed `HEAD` to `package/repo_clean_${VER}/` (see below).
- `archive_clean_repo.py`: standard-library inventory, literal exclusions, blob/mode verification and atomic publication helper.
- `package_source_exclude.txt`: clean-source exclusions, independent of the additional-data catalog.
- `p02-make_package.sh`: assemble the existing clean tree and CSV-selected additional data into `cmf_${VER}_pkg/`.
- `make_package.py`: read-only planning, verified staged assembly and SHA-256 manifest.

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

cmf_v5_beta/ is the Git development checkout, cmf_v5_package_data/ holds authoritative additional data outside Git, and package/cmf_${VER}_pkg/ is the independently assembled beta distribution. Import changes only local development copies; p02-make_package.sh separately produces the distribution directory.

## Import and Diff commands

Commands locate the checkout from their own script directory, independently of
current working directory. The default source is the logical sibling
`../cmf_v5_package_data/`; a symlink at that store root is supported. Never hard-code
an external-storage location. Use `--source` if the sibling is not available:

```bash
./package/s00-diff_package_data.sh
./package/s00-diff_package_data.sh --source /path/to/cmf_v5_package_data --details
./package/s00-diff_package_data.sh --dataset glb_15min --output /tmp/data_diff.csv
./package/s01-install_package_data.sh --dry-run
./package/s01-install_package_data.sh --source /path/to/cmf_v5_package_data
./package/s01-install_package_data.sh --dataset glb_15min
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
bash -n package/s01-install_package_data.sh package/s00-diff_package_data.sh
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
| Compressed `1min_nc/` including `location.txt` | Build products and temporary files |
| `COG/` for immediate visualization | Logs, caches and `.DS_Store` |
| Generation script/source directories and Makefiles, as provenance snapshots | Git metadata |
| Observation/station information, bifurcation products, CTL and auxiliary text | Build products, logs, temporary files, caches and `.DS_Store` |

**Distribution format: compressed NetCDF** for high-resolution maps.
**Legacy-compatible working format: Binary generated on demand.** Use the
[high-resolution restoration tool](../map/tools/script_format_conv/README.md#restore-high-resolution-binary-working-files-s04)
when legacy processing needs Binary. Do not package both `1min/` and `1min_nc/`.
Model-grid Binary remains included, alongside model-grid NetCDF. This first
selection does not prune generated standard products or change the Input Matrix
format; further data reduction and Input Matrix NetCDF are separate work.

### Visualization inputs and generation provenance

For both map datasets, include `COG/` so visualization can start without first
regenerating those rasters. Also include the scripts, source files, settings,
README files and Makefiles stored with the authoritative dataset: they record
how that version of the additional data was generated. These are provenance
snapshots; active shared development remains under the Git repository's
`map/tools/`. Inclusion does not imply that every historical recipe is a
maintained or independently reproducible entry point.

High-resolution Binary directories remain excluded (`1min/` for Global,
`15sec/` for Japan); restore them from compressed NetCDF when required.
The catalog selects existing files only; it does not generate missing COGs or
refresh provenance snapshots. Import/Diff and beta assembly enforce the same
selection; no raster generation is performed.

### Exclusion semantics and implementation boundary

The catalog retains all six original columns and adds optional `exclude_patterns`
as the final column. This is the only selection configuration; no parallel manifest
or dataset registry is introduced. `file_pattern` selects candidate regular files;
`exclude_patterns` then filters them on both source and target, including
TARGET_ONLY discovery. The glb_15min row uses exactly the existing policy:

```text
/1min/;__pycache__/;.git/;*.pyc;*.o;*.mod;*.log;*.tmp;.DS_Store
```

Split exclusions on `;`. `/TAG/` excludes only the directory directly under
the dataset root: `/1min/` excludes raw Binary but preserves `COG/1min/`;
`/15sec/` likewise preserves `COG/15sec/`. Other patterns ending in `/` match relative parent directory
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
information and auxiliary text, `COG/`, and generation scripts/source snapshots.
Exclude build products, logs, caches and temporary files. The exclude_patterns column
implements this same policy, replacing `/1min/` with `/15sec/`.
Do not copy `**/*` without this filtering. Restore high-resolution Binary on
demand with the shared restoration tool and `HIRES="15sec"`.

Generation scripts/source snapshots are selected by both Import and Diff,
so local edits can appear as MODIFIED or TARGET_ONLY and retain the existing
confirmation protections. Shared maintained generators remain under `map/tools/`. Installed data are excluded by `map/.gitignore`;
existing Git history is preserved. The
external data store is not modified by this registration. Source edition,
redistribution conditions and required attribution remain to be confirmed;
registration and local availability are not validation or permission to publish.

## Authoritative README for the additional-data store

[PACKAGE_DATA_README.md](PACKAGE_DATA_README.md) is the Git-managed source of the explanatory README intended for `../cmf_v5_package_data/README.md` (relative to the development repository root). Maintain it here, not directly in the external store. Copying it to the store is a separate, explicitly assigned operation; this documentation change does not perform that copy.

When registering or changing a dataset, update [package_data.csv](package_data.csv) and, when descriptions, provenance or conditions change, PACKAGE_DATA_README.md. The catalog selects dataset files; the README explains their role, source, conversion and unresolved redistribution conditions. See [AGENTS.md](../AGENTS.md) for the agent rule.

NetCDF dataset directories normally omit `_nc`; Binary variants use `_bin` when a distinction is needed. The global NetCDF dataset was renamed from `ELSE_GPCC_nc/` to `ELSE_GPCC/` in both the development repository and the additional-data store. The former global Binary directory has been removed.


## Clean beta Git source extraction

Run from any directory using the script path:

```bash
./package/p01-archive_clean_repo.sh --dry-run
./package/p01-archive_clean_repo.sh
```

Edit `VER="v5b01_$(date +%Y%m%d)"` near the top of the Bash script to use a
fixed version, for example `v5b01_20261119`. The default uses the execution host's
local date. Versions must start `v5b01_` and use letters, numbers, `_`, `.` or `-`.
Output is always `package/repo_clean_${VER}/`. Existing paths, including empty
directories and symlinks, are errors; there is no overwrite option. macOS or Linux
(including WSL) with Bash, Git, tar and Python 3.8+ are supported. Atomic no-replace
rename support is required; unsupported hosts fail without publishing output.

The Bash entry point pins one HEAD commit, discovers the repository from its own
location, inventories Git objects, and pipes `git archive --format=tar` into tar
in a private temporary directory. The helper removes explicit exclusions and
verifies every retained file's committed blob hash, size and executable status
before atomic no-replace publication. This catches export-ignore/export-subst
attributes that would silently drop or transform retained sources. The same
commit is written to `package/PACKAGE_BUILD_INFO.txt`, with version, branch, timestamp,
repository name, tool and stage. No compile, data overlay or final package build.

Uncommitted tracked edits, staged additions and untracked files cause a warning;
only the pinned commit is used. Ignored local additional data never enter the
archive. Already tracked samples remain even when a `.gitignore` pattern would
otherwise match them. All file payloads and executable flags are retained;
archive timestamps and provenance timestamps do not promise byte-identical whole
output trees across executions. Generated build information is the only added
file. No source file is rewritten to repair links to excluded development logs.

`package_source_exclude.txt` has deliberately small literal syntax:

- `/directory/` or `/parent/directory/`: root-relative directory and descendants.
- `.gitignore` or another literal basename: files with that name at every depth.
- Blank lines and full-line `#` comments are ignored. No globs, substring matches,
  negation, path traversal or inline-comment syntax.

Initial exclusions: root `.git/`, `.github/`, `research/`; `.gitignore`,
`.gitattributes` and `.gitmodules` files at every depth. Git archive itself never
contains repository history. Independently of the editable list, root-package
`repo_clean_*` and `.repo_clean_tmp.*` trees are always excluded, even if accidentally
tracked. The root ignore rules exclude generated outputs and temporary staging
under the existing whitelist policy. No tracked build/cache artifacts were found
in the initial audit; no additional extension-wide filters were introduced.
Mekong Binary, NetCDF and COG samples remain part of the committed source tree.

Tracked symlinks are reported. Absolute, escaping, cyclic or dangling/excluded
link targets fail before extraction; links that resolve within the retained tree
are preserved as links. Nothing follows unsafe targets to copy external data.
Failure removes only the invocation's mktemp directory, leaving no completed
output. Concurrent creation of the destination is rejected atomically.

Dry-run performs no extraction and creates no output/staging directory. It prints
version, pinned full commit ID, branch, planned output, tracked/excluded/retained
file counts, per-rule exclusion counts, symlinks and estimated retained payload
bytes from Git blob metadata. Payload size excludes directory overhead and the
small generated provenance file. Source hashing at real extraction is streamed
in 1 MiB blocks, without loading map rasters into memory.

For this **beta test edition**, user/developer materials are intentionally kept
together: AGENTS.md, CONTRIBUTING.md, legacy/, docs/, tests and all other retained
tracked paths remain. Research logs stay in the development repository but are
excluded from the clean beta tree. User/developer documentation may be separated
for a formal release later. This extraction is only the Git-source stage. The separate p02-make_package.sh
assembly stage described below integrates additional data. Existing Import/Diff
commands and package_data.csv are unchanged.

Focused verification (temporary Git fixtures, no real scientific data changes):

```bash
bash -n package/p01-archive_clean_repo.sh
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s package/tests -p test_archive_clean_repo.py -v
```

Tests cover exact committed bytes/modes, developer and sample preservation,
exclusions and literal near matches, dirty/untracked/ignored inputs, another CWD,
provenance, ignore rules, nested generated outputs, unsafe links, existing output
protection and cleanup on tar/archive-attribute failures. A real source extraction
must be checked separately; this is not a model-execution validation.


## Assemble a beta testing package

This produces a **CaMa-Flood v5 beta testing package**, not a formal release.
Set matching `VER` values in both entry points; no automatic synchronization is
attempted. p01-archive_clean_repo.sh defaults to the local run date, whereas
p02-make_package.sh initially uses the explicit `v5b01_20261119` setting. To package
another version, edit the values before running:

```bash
# From the repository root:
./package/p01-archive_clean_repo.sh --dry-run
./package/p01-archive_clean_repo.sh

# Run assembly from package/ (or call it by path from any other directory):
cd package
./p02-make_package.sh --dry-run
./p02-make_package.sh
```

An existing clean tree is reused without running archive again. Both commands
refuse existing same-version outputs; retain them and choose a new version when
needed. Assembly output: `package/cmf_${VER}_pkg/`. It contains independent real
copies of the clean sources and additional datasets. AGENTS.md, CONTRIBUTING.md,
legacy/ and developer documentation remain. Git administration/research files and
nested generated trees are rejected rather than reintroduced or silently pruned.
An excluded data path already in clean sources is a policy conflict and errors;
assembly never deletes authoritative clean inputs to resolve it.

User settings at the top of p02-make_package.sh:

```bash
VER="v5b01_20261119"
# Relative to the package/ directory; absolute paths are also permitted.
PACKAGE_DATA_DIR="../../cmf_v5_package_data"
```

**Relative additional-data paths are resolved from the directory containing
p02-make_package.sh (`package/`), never the current working directory or repository
root.** The default reaches the external sibling of cmf_v5_beta. Absolute paths
are supported. The store root may be a symlink; selected dataset children may not
be symlinks, following existing Import/Diff policy. Dry-run uses exactly the same
path resolution and validation as assembly and creates no files or bytecode.

The clean input must be `package/repo_clean_${VER}/`, contain matching version and
valid commit/branch/stage fields in package/PACKAGE_BUILD_INFO.txt, and retain major
source directories. It is the sole source-tree authority. The tool does not copy
from the development worktree, rerun Git archive or update an old clean tree with
new builder/source files. To include later source changes, explicitly create a
new clean version with the extraction stage first. Build-info source revision is
inherited as provenance; assembly checks current clean contents, not Git history.

Planning reuses load_catalog/files_for/file_pattern/exclude_patterns/no_symlinks
from package_data.py. It requires every registered dataset, reports all detected
missing/invalid datasets and differing-path conflicts before copying, and shows
clean/dataset counts and bytes, duplicate counts, exclusion rules and total size.
Same-path identical regular files are retained once; different contents or type/
symlink conflicts stop the build. Source/destination containment is rejected.
A conservative free-space check reserves planned payload, the largest in-flight
file and directory/manifest overhead. This cannot guarantee against later disk
exhaustion, which is handled as a failed, unpublished build.

Assembly copies into a private same-filesystem temporary tree, reusing the 1 MiB
chunk verified copier. Source executable modes are restored (Import deliberately
makes local data editable instead). Safe internal relative clean symlinks remain
links; additional data are copied as real files, never links to the external
store. The tool verifies the complete source/data union, all copied bytes, clean
file modes and symlink containment, then records hashes. It detects changes to
selected files, clean inventory and CSV through device/inode/size/mode/time
snapshots; this is best-effort detection, not a filesystem snapshot or lock.
Only an entirely verified tree is published with the existing atomic no-replace
publisher. Failure cleans the invocation's temporary tree; no existing package
is removed or overwritten.

package/PACKAGE_MANIFEST.json contains version/date, inherited source commit and branch,
clean version, builder version/code SHA-256, CSV SHA-256, Dataset IDs/counts/bytes,
per-file relative paths/sizes/types/SHA-256 and Dataset content fingerprints.
For symlinks the checksum covers link text. No Additional Data version is invented:
`version: null` accompanies content fingerprints. Relative configured store paths
are recorded with their package/-directory basis; an absolute host path is
redacted to its store basename. Console diagnostics may show resolved paths.
The file inventory excludes the manifest itself to avoid self-hashing; package
counts/bytes explicitly include it. Timestamps vary between builds; data hashes
and Dataset fingerprints identify retained contents independently of timestamps.

These structural checks do not compile Fortran, run model science, regenerate
NetCDF/COG, compress an archive, upload a release or establish redistribution
permission. Existing unresolved licenses/attribution/provenance in
PACKAGE_DATA_README.md remain unresolved. Local generation and external public
redistribution are separate decisions.

Verification with small temporary fixtures (no real-data copies):

```bash
bash -n package/p02-make_package.sh
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s package/tests -v
```

The assembly tests cover package-relative defaults from multiple CWDs, absolute
and linked root paths, no-write dry-run, missing/version/containment/output errors,
CSV selection/COGs/raw-Binary exclusions, identical/different collisions,
chunked copies, corruption/mutation/space failures, cleanup, executable modes,
manifest totals/hashes, safe links and unchanged inputs. Real-data dry-run and
one actual package build are separate integration checks, documented in research.

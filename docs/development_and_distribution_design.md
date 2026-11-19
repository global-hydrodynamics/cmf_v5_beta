# CaMa-Flood v5: Package Distribution and Community Development Design

**Status:** Draft / Under Development  
**Target:** CaMa-Flood v5 beta  
**Purpose:** Design principles and intended specifications  
**Scope:** Package creation, test data management, external contributions, and pull request workflow

This is a maintained design specification, revised as implementation and review progress. Requirements and conceptual examples below describe the intended design; they do not establish that the packaging tools, regression environment, or release process already exist. Section 11 records the current implementation boundary, and Section 12 records decisions still needed.

Current development repository: `global-hydrodynamics/cmf_v5_beta`, base branch `main`. The previous `global-hydrodynamics/CaMa-Flood_v4` repository is retained for v4 maintenance and historical evidence; v5 work does not modify it. Historical repository URLs and research Task IDs remain valid evidence and must not be rewritten merely to match current naming.

Development rules are maintained in [AGENTS.md](../AGENTS.md); practical contribution guidance is in [CONTRIBUTING.md](../CONTRIBUTING.md). This document maintains the current design, while [research/](../research/README.md) records how decisions were reached.

## 1. Background and Motivation

### 1.1 Limitations of the previous development workflow

In CaMa-Flood v4 and earlier versions, the source repository and distributed model package were maintained through a workflow that was not fully reproducible by external developers.

The GitHub repository did not necessarily include the data required to execute the model, while the official package was assembled separately by the maintainers.

This created several difficulties:

- External developers could modify source code but could not easily reproduce the official model execution environment.
- Testing required developers to independently obtain and configure suitable map and forcing data.
- Package preparation and integration testing depended heavily on the maintainers.
- The relationship between source code contributions and the distributed package was not sufficiently transparent.
- Changes could be integrated before complete execution testing, potentially requiring subsequent corrections or reversions.

The fundamental problem was not that external developers were unable to test their modifications, but that **the project did not provide a common, readily reproducible development and testing environment**.

### 1.2 Objectives of the v5 redesign

CaMa-Flood v5 aims to provide:

1. **Usability:** A ready-to-use model package for ordinary users.
2. **Reproducibility:** A transparent and reproducible process for constructing the distributed package from version-controlled sources and separately distributed data.
3. **Testability:** A GitHub repository containing sufficient data to perform meaningful small-scale model tests.
4. **Contributability:** A workflow in which external developers can implement, test, and submit modifications without depending on the maintainers for routine execution tests.
5. **Maintainability:** A contribution process that minimizes unnecessary changes, prevents accidental data commits, and allows maintainers to review and test contributions before merging.

The overall principle is:

**Developers should be able to test their own changes before submitting them, and maintainers should be able to reproduce those tests before merging.**

## 2. Three-Part Distribution Architecture

The v5 distribution system consists of three components.

### A. GitHub Repository

The official version-controlled development repository.

Contents:

- Fortran model source code
- Shared tools and processing scripts
- Configuration templates
- GOSH execution scripts
- Tutorial and visualization source files
- Documentation and development guidelines
- A small Mekong river map
- Minimal runoff forcing data
- Reference model outputs and verification scripts needed for regression testing

**Requirement:** A fresh clone of the repository must support compilation and a documented small-scale model test without requiring the additional data package.

The repository is the primary working environment for developers.

### B. Package Additional Data

A separately distributed collection of datasets required to construct the full model package.

Typical contents:

- Global and regional river maps not included in Git
- Larger runoff forcing datasets
- Additional reference datasets required by GOSH and tutorials
- Other approved datasets required for the official package

This component is not maintained as ordinary Git-tracked data.

Its directory structure should match the destination paths used in the model package, allowing the packaging tool to assemble the package without requiring manual relocation of files.

The additional data should include a version identifier and a manifest documenting its contents.

### C. Distributed Package

The ready-to-use distribution for ordinary users.

It is generated by combining:

**GitHub Repository + Package Additional Data → Distributed Package**

The package:

- Contains the source code, scripts, documentation, and required datasets.
- Retains the directory structure expected by GOSH and tutorials.
- Does not contain the `.git/` directory or Git history.
- Excludes development-only files and unnecessary temporary artifacts.
- Can be built and used without requiring users to understand Git.
- Does not require users to download and merge the additional data themselves.

The distributed package is a **generated product**, not an independently maintained source tree.

## 3. Package Creation Workflow

### 3.1 Packaging script

A packaging script shall be provided in the GitHub repository.

Its responsibilities are to:

1. Read the selected GitHub source revision.
2. Verify the additional data package and its version.
3. Create a clean package output directory.
4. Copy the required tracked source files, scripts, documentation, and small test datasets.
5. Add the required datasets from the additional data package.
6. Check for missing files, unexpected overwrites, and directory conflicts.
7. Exclude `.git/`, unnecessary development artifacts, and temporary files.
8. Record the source revision and additional data version used to generate the package.
9. Perform basic structural validation and, where practical, an execution smoke test.

**Important:** The packaging script must not modify the original GitHub working directory.

The output must be generated in a separate destination.

### 3.2 Reproducibility requirements

The same source revision and additional data version should generate an equivalent package.

The packaging process should therefore record:

- Git commit hash or release tag
- Additional data package version
- Package creation script version
- Package creation date
- Optional checksums for verification of data integrity

The packaging operation must fail clearly if a required dataset is missing or if an unexpected overwrite would occur.

### 3.3 Relationship to GitHub

The packaging script and its configuration are version-controlled.

The additional data and generated package are not committed to the source repository.

The package is generated from a known, reviewable source revision, rather than directly from arbitrary uncommitted modifications in a developer's working directory.

## 4. Repository Structure and Data Management

### 4.1 Basic directory policy

Existing v5 directory names should be retained wherever possible.

A conceptual structure is:

```text
CaMa-Flood_v5/
├── src_main/             # Model source
├── config/               # Configuration templates
├── tools/                # Shared tools
├── map/                  # Map tools and datasets
│   └── mekong_15min/     # Small official test map
├── inp/                  # Runoff inputs and related tools
│   └── test_mek_1deg/    # Minimal test forcing
├── gosh/                 # Execution workflows
├── tutorial/             # Tutorials
├── visualization/        # Visualization tools
├── variable_table/       # Variable definitions
├── research/             # Development records
├── .github/              # CI and GitHub configuration
└── ...
```

The specific small test datasets and their existing locations should be confirmed before implementation.

**Current-name clarification:** The tree above is conceptual, not an instruction to rename directories. Current tracked forcing is `inp/repo-mek_1deg_bin/` (daily Binary records in monthly files) and `inp/repo-mek_1deg/` (annual NetCDF), with `map/mekong_15min/` as the map. Maintained v5 execution workflows currently live in `gosh_test/`; the conceptual `gosh/` entry does not authorize moving them or treating historical v4 scripts as v5 entry points. Preserve these existing locations unless a separate change is approved.

**A separate `github_test/` data directory is not required.**

Instead, official small test datasets remain in the ordinary model input and map directory structure and can be used directly by existing GOSH scripts.

Test scripts and reference outputs may be organized separately where needed, without duplicating large input datasets.

### 4.2 Git-tracked datasets

The repository should track only explicitly approved small datasets.

Each dataset must have:

- A defined testing purpose
- A documented source and license
- A reproducible format and directory structure
- A reasonably limited file size
- A clear relationship to the associated tests

These datasets must not be overwritten during package construction.

### 4.3 Git ignore policy

The `.gitignore` file should explicitly exclude:

- Datasets supplied exclusively through Package Additional Data
- Locally generated model output
- Compiler-generated files
- Temporary files and processing intermediates
- Python caches and virtual environments
- Local, machine-specific configuration files
- Other files that are not intended to be contributed

The goal is to ensure that **ordinary model execution does not create unrelated Git changes**.

A clean `git status` should normally show only the source code, scripts, documentation, or intentionally modified official test data.

The ignore rules should not accidentally hide new source files that developers are expected to contribute.

## 5. Development and Testing Workflow

### 5.1 Primary development environment

External developers primarily work in a clone or fork of the GitHub repository.

Because the repository contains a minimal executable dataset, developers should be able to:

1. Clone the repository.
2. Configure and compile CaMa-Flood.
3. Run the official small-scale Mekong test.
4. Modify model source code or related tools.
5. Repeat the test and compare results.
6. Commit and submit the intended changes.

This workflow must not require access to the full additional data package.

### 5.2 Extended testing

Developers who need more extensive testing can obtain Package Additional Data.

They can then construct a full package or configure the development environment to reference the additional datasets.

Examples include:

- Global simulations
- High-resolution regional experiments
- Additional runoff experiments
- New river physics requiring extended input data
- Tutorial-based verification
- Large-scale performance evaluation

The extended test environment should use the same source code as the development repository.

### 5.3 Testing requirements

Testing is organized into two levels.

**Level 1: Minimal repository tests**

- Compilation
- Essential model execution
- Small-scale Mekong simulation
- Comparison against approved reference output
- Relevant script and metadata checks

These should be executable from a clean GitHub clone and, where practical, through GitHub Actions.

**Level 2: Extended package tests**

- Regional or global execution
- Additional forcing or boundary conditions
- More extensive physical and numerical validation
- Performance, MPI, and other specialized tests

These are performed when the nature of the changes requires them.

Not every pull request must pass a global simulation.

Regression tests must compare against independently approved reference outputs; a modified implementation must not silently redefine its own expected results.

## 6. External Development and Contribution Policy

### 6.1 Basic principles

External developers are assumed to have basic programming and source-control skills.

The contribution workflow should therefore be based on **trust, clear guidelines, and reviewable changes**, rather than extensive restrictions on local development.

Developers are free to organize their local working environment, use additional data, and conduct experiments as needed.

However, only changes intended for contribution should be included in a pull request.

### 6.2 Branch management

Each independent contribution should be developed on a dedicated feature branch based on an appropriate current version of `main`.

The recommended sequence is:

1. Create a feature branch.
2. Implement the modification.
3. Execute relevant tests.
4. Review the modified files and staged changes.
5. Commit only the intended contribution.
6. Push the feature branch.
7. Open a pull request against the official repository.

Developers should not submit their entire experimental working environment or unrelated modifications.

The project should recommend reviewing the difference between the feature branch and the target branch before submitting a PR.

### 6.3 Scope of a pull request

A pull request should contain a logically coherent contribution.

Typical contents include:

- Source code changes
- Relevant tests
- Required configuration updates
- Small test data, where necessary
- Documentation updates
- A description of verification results

A PR should normally exclude:

- Large additional datasets
- Generated model outputs, except approved reference outputs
- Personal settings
- Temporary files
- Unrelated refactoring
- Unrelated research experiments

The guiding principle is:

**One contribution, one reviewable set of changes.**

### 6.4 Requirements for a new feature

For new physical processes, numerical schemes, or model extensions, developers should preferably provide:

**A. Small-scale verification**

- A minimal test case using the official Mekong dataset where feasible
- Any additional small input data needed
- Expected outputs or quantitative verification criteria
- A description of the scientific behavior being tested

**B. Extended or global verification**

- Evidence that the feature works in larger-scale applications, where relevant
- Required additional datasets or instructions for obtaining them
- Clear documentation of data dependencies

The first component should normally be included in GitHub when appropriate.

Large datasets required for the second component should be distributed through Package Additional Data or another documented data source.

These are preferred contribution requirements, not an absolute obligation for every small bug fix or preliminary feature.

### 6.5 Updating additional data

A contribution may require the additional data package to be updated.

In that case, the developer should describe:

- The required new data
- Their source and licensing conditions
- The required destination directory
- Compatibility with existing tests
- Whether the data are necessary or optional

The maintainers decide whether to incorporate the data into the official additional data package.

This allows source changes and data updates to be coordinated without requiring large datasets to be committed to GitHub.

## 7. Pull Request Review and Integration

### 7.1 Pre-merge verification

External contributions should be tested before being merged into `main`.

The maintainer may:

- Inspect the PR diff and commit history.
- Review automated CI results.
- Check out the PR branch locally.
- Execute the small official test.
- Perform extended experiments using Package Additional Data when necessary.
- Request scientific or technical revisions.

The PR branch can be tested in an independent working directory or Git worktree without modifying the main development environment.

**Merging into `main` is not a prerequisite for testing.**

### 7.2 Merge policy

A PR should be merged only after its intended modifications have been reviewed and the relevant tests have passed.

Direct changes to the official `main` branch should be restricted.

A failed test should normally result in a revision to the PR branch, not a merge followed by a revert.

### 7.3 Role of automated tests

GitHub Actions should provide a basic and reproducible validation environment.

Automated tests complement, rather than replace, scientific review.

The maintainer remains responsible for judging the physical validity and compatibility of changes affecting model science.

## 8. Recommended Documentation

The project should maintain a small number of clear documents:

| Document | Purpose |
|---|---|
| `README.md` | Repository overview, installation, and quick-start test |
| `CONTRIBUTING.md` | Branch, commit, PR, and testing guidelines |
| `AGENTS.md` | Development instructions for AI coding agents |
| Package build README | Additional data requirements and package creation |
| Test documentation | Reference data, validation criteria, and test commands |

Documentation should emphasize practical examples instead of excessive procedural rules.

AI coding agents should follow the same repository and contribution policies as human developers.

## 9. Beta Implementation Priorities

### Required for the initial beta

- [ ] Identify the smallest usable Mekong map and runoff dataset.
- [ ] Confirm that they can be redistributed through GitHub.
- [ ] Ensure a fresh clone can compile and execute the small test.
- [ ] Establish reference outputs and a repeatable validation command.
- [ ] Separate additional package data from Git-tracked datasets.
- [ ] Update `.gitignore` for additional datasets and generated files.
- [ ] Implement a reproducible package creation script.
- [ ] Verify that the generated package runs existing GOSH and tutorial examples.
- [ ] Write concise contribution guidelines.
- [ ] Test the workflow using a sample feature branch and pull request.

### Can be improved after beta testing

- Additional regression tests
- More complete automated numerical validation
- More compiler and platform combinations
- Extensive MPI and HPC testing
- Automated additional-data version management
- More advanced review and release automation

The beta should prioritize a working end-to-end process rather than a comprehensive development infrastructure.

## 10. Design Summary

The proposed v5 architecture establishes a clear relationship between three products:

**GitHub Repository:** A version-controlled source and minimal testing environment for developers.

**Package Additional Data:** Large datasets needed for complete model execution and extended validation.

**Distributed Package:** A reproducibly generated, ready-to-use model distribution for users.

The central change from the previous development workflow is that **external contributors can independently implement and test their modifications using the same publicly documented process as the maintainers**.

The project does not require contributors to reproduce a maintainer-specific package assembly procedure or submit their entire local working environment.

Instead, contributors provide focused, tested changes, while maintainers review and integrate them before generating official distributions.

This approach is intended to reduce the technical barriers to community contributions while keeping the CaMa-Flood development and distribution system simple and maintainable.

## 11. Current implementation boundary (2026-11-19)

The principles above are the adopted direction. Their implementation remains incomplete.

| Area | Observed state | Remaining work |
| --- | --- | --- |
| Minimal repository inputs | Mekong map, Binary runoff sample, and 2000–2005 annual NetCDF forcing are already tracked in ordinary map/input directories. | Select the official minimal case and verify its complete fresh-clone execution and redistribution evidence. No separate GitHub-only input tree is planned. |
| Model and execution entry points | `src_main/`, `config/`, `gosh_test/`, and Tutorial01 provide existing build/run materials with earlier operational evidence. | Consolidate a current clean-clone recipe; do not describe this documentation task as a new model execution or package test. |
| Regression references | Component tests exist; earlier model comparisons are recorded in research. | Independently approve the official model-reference revision, variables, calendar, precision and comparison criteria, then provide a repeatable command. Historical execution success is not this approval. |
| Migration baseline | Legacy root src/gosh/adm relocation and direct util-to-tools consolidation are committed in 29b889c4; current main inherits them. | Use legacy/ only as reference and the active src_main/config/gosh_test/tools paths for v5 work. |
| Additional data | `package/install_package_data.sh` implements developer Import; `diff_package_data.sh` provides independent read-only file Diff. The sole `package_data.csv` catalog preserves its six fields and adds optional exclude_patterns. Symlinked sibling stores, bounded-memory comparison, Git/ignore protections and verified atomic local copies are supported. | Distribution version/provenance/redistribution review and independent package assembly remain future work. No real-data Import was performed by the implementation task; see the [package guide](../package/README.md). |
| Distributed Package | `package/archive_clean_repo.sh` extracts a pinned committed HEAD to `package/repo_clean_${VER}/`, with explicit exclusions, byte/mode validation and build provenance. This is only the clean Git-source stage; no final assembler or verified runnable distribution exists. | Integrate approved additional data in a later independent stage, then verify the assembled package structurally and through approved execution checks. |
| Legacy packaging instructions | `archive_src.sh`, `doc/make_package.sh` and the old package guide describe v4-oriented workflows. | Preserve them as historical references; do not present them as the v5 assembly command. |
| Contribution guidance | CONTRIBUTING.md now documents feature branches, focused diffs, two test levels and pre-merge review. | Validate the full contributor workflow with an independently tested feature branch/PR in a later task. |
| PR validation | The former source/map workflow is removed from active GitHub Actions by maintainer instruction; tests and inputs remain. | Automated CI is temporarily disabled pending a small, reproducible v5 suite. Use the retained manual checks; no replacement workflow is added here. |

Migration cleanup corrects Guide01's confirmed repository-root calculations without changing its experiment or scientific calculations; full experiment execution is not claimed by those path checks. The p02 f01/f02 visualization entry points still re-extract from local annual outputs despite having compact tracked samples: separating extraction from plotting is a later interface/workflow task, not a repository-rename fix. Guide01 and p02 flood-depth downscaling still compile `etc/downscale_flddph/src/downscale_flddph_trib.F90`; retain that source. Legacy etc Makefiles retain their original adm assumptions and are not supported v5 entry points. See [the migration audit](migration_consistency_audit.md) for classifications and retained manual validation. Do not move all of etc or expand its dependencies.

`doc/` and `etc/` are retained for now. Shared calculation belongs in tools, visualization in visualization, map-specific processing in map, and runoff-specific processing in inp. Category subdirectories under tools should be introduced only when an approved migration needs them; the current shared utility consolidation does not create tools/code.

The intended ignore policy also remains partly unimplemented: the current broad extension rules can hide extensionless source files or expose additional NetCDF data, and historical snapshots included tracked Python caches. The 2026-11-19 clean-source inventory finds no tracked Python caches or compiler artifacts. Ignore rules cannot protect already tracked files or guarantee that another branch will never track an added-data path. Review dataset destinations and generated-file tracking before implementing installation. Do not introduce a custom protection or coordination service.

A developer beta may retain unfinished and explicitly labeled legacy features. The generated user package is the intended complete distribution product; this document does not announce that such a v5 package is already available. Tutorial learner-package selection is a separate educational profile described in the tutorial documents, not a rule to delete developer records or reference solutions from Git.

## 12. Open Questions and staged follow-up

These related acceptance decisions are tracked as [KG-0036](../research/records/knowledge_gaps/KG-0036.md).

These decisions do not block the present documentation work. Resolve each before its dependent implementation; record the rationale here and the decision history under research.

- **Official minimal model test and references (important):** Section 5 requires approved references, but no current single regression contract selects the run period, variables, build/precision settings and tolerances. Earlier 40-day and multi-year Mekong runs are evidence, not an automatic choice of the official reference. This choice controls test cost and numerical acceptance.
- **Additional-data contract (important):** Select the first datasets, source permissions, destination paths, manifest/version compatibility fields, and copy versus optional read-only links after workflow inspection. Existing mixed code/data directories and absolute legacy links prevent choosing a universal directory-overlay method without further work.
- **Package selection and equivalence (important):** Specify which developer-only files are excluded, how tutorial learner profiles relate to the full package, and what “equivalent package” means when creation dates differ (Section 3.2). For the beta, preserve AGENTS.md, CONTRIBUTING.md, legacy/, docs/, tests and tracked samples, while excluding research/, .github/ and Git-specific files. Research history remains in Git. Formal releases may separate user/developer documentation later. Equivalent retained source means committed file bytes and executable flags; generated provenance timestamps differ. Additional-data manifests and final-package equivalence remain future decisions.

Recommended sequence: reconcile the migrated policy and existing working-tree changes; approve a minimal-case validation contract; inventory approved additional data; specify package file selection and manifest; implement assembly and focused tests as separate tasks; finally verify the selected source revision in a clean checkout and the generated package in an independent directory. Each implementation stage follows the branch/scope approval and proportional validation rules in AGENTS.md.


### Approved beta source-extraction stage (2026-11-19)

The beta intentionally retains developer/AI-agent materials alongside user
sources. No minimal user-only profile is applied. `package/archive_clean_repo.sh`
uses git archive for a pinned HEAD, explicit literal exclusions in
package_source_exclude.txt, safe staging and no-overwrite publication. Root
research/ and .github/ plus Git-specific files are excluded; research records stay
in the development repository. Tracked scientific samples are not filtered by
extensions or ignore status. An in-tree symlink is retained; unsafe links abort.

PACKAGE_BUILD_INFO.txt records source revision/branch, version and execution date.
The extracted files retain committed bytes/modes; the timestamped provenance is
not a claim of byte-identical complete archives. No final compressed archive,
additional-data integration, Fortran compilation or model execution is performed.
See [the package guide](../package/README.md#clean-beta-git-source-extraction).

# Contributing to CaMa-Flood v5 beta

Develop in a clone or fork of `global-hydrodynamics/cmf_v5_beta`. The repository contains the model, tools and approved small Mekong map/runoff samples in their ordinary `map/` and `inp/` locations. Install local compiler/Python dependencies using the [build guide](config/README.md) and [Python guide](docs/python_environment.md). Keep machine-specific `config/Mkinclude` and `.venv/` local. The [development and distribution design](docs/development_and_distribution_design.md) distinguishes the GitHub environment, optional Package Additional Data and the planned complete user package.

## Feature branches and focused changes

Use a dedicated feature branch based on an appropriate current `main` for each independent contribution; keep using that branch as the contribution develops. Coordinate with the owner when joining an existing shared project. The shared-project and agent approval rules are in [AGENTS.md](AGENTS.md); this guide does not grant agents permission to create branches, commit, push or merge outside their assignment. Local experiments and private branches need no separate dashboard entry.

Commit only the source, relevant tests, necessary configuration templates and documentation that belong to the change. Small data/reference additions need a documented purpose, provenance and redistribution permission. Exclude additional large datasets, ordinary model outputs, compiler products, Python caches, credentials and unrelated experiments/refactoring.

Review the working tree and staged changes before committing, and compare the complete contribution against its target before opening a PR:

```sh
git status --short
git diff
git diff --cached
git diff main...HEAD
```

Use the current target ref when it differs from local main. Stage only intended files or hunks; ignore rules do not remove files already tracked by Git. Do not discard another contributor's changes to make a checkout clean.

## Proportionate tests

GitHub Actions is temporarily disabled while the v5 regression strategy is redesigned. Use the [retained manual checks](docs/migration_consistency_audit.md#manual-checks-retained-from-the-retired-workflow) and report what you actually ran; do not assume an automated PR check has executed.

The intended Level 1 is a fresh-clone build and small Mekong model test with independently approved regression references. Existing [developer workflows](gosh_test/README.md) and [Tutorial01](tutorial/tutorial01-get_started/manual_tutorial01-get_started.md) provide build/run instructions; a unified model regression command is not yet established. Report the actual workflow, revision, configuration, inputs and comparisons you used rather than claiming the planned test environment is complete.

The following existing component checks were executed successfully during this documentation update. Run from the repository root with Python 3; they check metadata/data contracts and CTL generation, not model science or the full Level 1 workflow:

```sh
python3 -B map/tests/validate_mekong_sample.py
python3 -B map/tests/validate_map_variables.py
PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest map.tools.tests.test_generate_ctl -v
```

Choose additional checks for the changed scientific calculation, interface or workflow; see [the test-design rules](AGENTS.md#cama-flood-v5-test-design-principles). Level 2 covers regional/global data, optional physical processes, MPI and performance when relevant. Not every PR needs a global run. Document external data requirements and how maintainers can reproduce the check; do not commit the large data. Reference updates require independent approval and must not silently redefine expected results from the changed implementation.

## Pull requests and review

Describe the problem and resulting behavior, scope/affected components, tests actually run and their results, data/build dependencies, and any numerical/interface effects, limitations or skipped checks. Identify needed additional-data updates with source, terms, destination and whether they are required or optional. Link an Issue when one is used; no custom coordination system is required.

Open the PR against main with a coherent, reviewable diff. Maintainers review code, available test evidence, scientific implications and compatibility, and can run the PR branch in an independent checkout/worktree before merging. Merging is not required for testing. Address failures on the feature branch. Automated tests support scientific review; they do not replace it. Direct changes or merges to the official main require the maintainer authorization described in AGENTS.md.

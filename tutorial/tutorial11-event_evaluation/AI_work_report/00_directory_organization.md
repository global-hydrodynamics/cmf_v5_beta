# Tutorial11 directory organisation and path compatibility

Date: 2026-11-24. Task: DT-0181. Validation: VR-0225.

## Scope and changes

Maintainer authorises an L1 directory/path-maintenance change on the existing
feature/package-builder branch. Followed cama-development and
large-model-refactoring: no scientific refactoring, analysis, acquisition,
simulation, figure generation or environment reconstruction.

Moved all existing root-level processing entry points (10) to run_script/ and
all existing plotting entry points (11) to plot_script/. Filenames and modes
were retained:19 files at0755; f23 and f24 were already0644 and remain so.
The retired f01-gfm_3sec_validation.sh was already absent, as were three original
synthesis reports; existing deletions were not restored or newly introduced.
No compatibility wrappers, symlinks or duplicate launchers were added.

Renamed the process document to README.md, retaining its scientific sequence,
Step descriptions/status and dependencies. Added landing-page navigation,
configuration ownership, directory roles and invocation examples. Step05 water
levels and06–10 remain reserved; conceptual16–17 are partly exercised by21–24;
18–20 unassigned;24 final;25 canceled. The English case study is local; links to
the three absent original syntheses point to their retained Git versions.

SCRIPT_DIR now means launcher directory; TUTORIAL_DIR resolves its parent.
Former tutorial-root uses of SCRIPT_DIR now use TUTORIAL_DIR, including model
run/output paths, metadata, settings and Python implementation arguments.
Repository-root/CMF_BASE detection follows the tutorial root. Existing values,
Python defaults/fallbacks, CLI flags, scientific settings and output locations
are preserved. Prompts, AGENTS and technical-report references were updated.
Only executable-reference strings in14_simulation_setup.json (2) and
15_simulation_output_visualization.json (1) changed; stored results and hashes
retain their historical meaning. Development-log commands remain historical.

No implementation Python or scientific Survey Report was edited. Existing tests
refer directly to script/ Python files and require no path modification.
No active direct outside-Tutorial reference to these moved files was found;
outside changes are limited to the required docs/dev_status.md proposal and
research development_tasks/events/validation_runs indexes.

## Checks actually performed

- All21 destinations present; root entry points absent; all root Prompts retained.
- All21 mode bits match the starting files, including the two0644 files.
- bash -n passes for all21; sh -n also passes for the POSIX s14 entry point.
- Complete old/new Shell text comparison after normalising only path anchors,
  tutorial-root aliases and relocated references passes for every launcher.
- Disposable layouts with spaces in their names execute only path/User settings
  declarations. All21 launchers match old/new resolved values from repository,
  tutorial and unrelated directories:126 declaration probes. Physical/logical
  /tmp aliases were normalised in the checker, without changing production paths.
- Three actual relocated entry points (s21,s03d,f04) were executed from an unrelated
  directory with a no-op Python executable. Captured arguments locate the correct
  implementation and tutorial root. No data processing or Figure write occurs.
- An initial f24 smoke attempt could not use the environment-supplied stub because
  its existing Python setting is a fixed .venv/bin/python path; that environment
  is absent. No Figure was regenerated. Kept its setting unchanged and used f04
  for the third argument-capture check; f24 declaration/syntax checks pass.
- README/AGENTS/Prompt relative paths and anchors:114 occurrences resolve.
- No old active Shell references remain in those files or JSON handoffs.
- Available scientific reports (including the English synthesis) and Python
  implementations are byte-identical to task start. Metadata diff is limited
  to the three executable-reference values. No scientific dataset was rescanned.
- git diff --check and scope review pass. Research index validation retains15
  unrelated pre-existing errors; no new structural errors introduced.

The temporary focused checker is execution evidence, not a new scientific
regression suite. Existing scientific tests and full workflows were not rerun.
These checks demonstrate relocation/path compatibility, not scientific skill.

## Compatibility limits and preservation

Callers must use run_script/ or plot_script/; old root-level shell paths are
intentionally unsupported by this reorganisation. Invoke the two0644 plotting
scripts with bash. Missing analysis dependencies/data are not reconstructed.
Unchanged scientific reports retain old relative process-document links, which
now refer to README.md; repairing those links would require editing reports
explicitly frozen by the maintainer. The README documents the mapping rather
than adding a forbidden duplicate process document or symlink. Existing missing
syntheses are accessed through retained Git links, not restored local files.
Some Python help/docstrings and historical research/development records may
mention former shell names; implementations and past records remain unchanged.

Knowledge-gap review: no new scientific/architectural question. The unresolved
scientific issues documented in existing reports remain. Changes are left
uncommitted for review; no commit, push or branch switch was requested.

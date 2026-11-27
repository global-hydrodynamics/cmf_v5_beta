# Preprocessing code conventions: map and runoff tools

## Scope and reading order

Apply this guide to new or locally modified maintained code under `map/` and
`inp/`: shared Fortran/Python tools, Shell templates and dataset-specific entry
scripts. It does not request a formatting sweep or migration of historical code.
Read the [root development policy](../AGENTS.md) first, then
[map instructions](../map/AGENTS.md) or [input instructions](../inp/AGENTS.md),
this guide and the responsible component README. Approval, coordination,
research, testing and publication policy remain solely in the root guidance.

The transferable principles below come from
[`src_main/FORTRAN_DESIGN.md`](../src_main/FORTRAN_DESIGN.md) and
[`src_main/FORTRAN_STYLE.md`](../src_main/FORTRAN_STYLE.md), adapted to standalone
preprocessing tools. Those source-model documents continue to govern
`src_main/`; they are not a formatting template for every language or utility.

## A. Shared principles

| Principle adopted | Application to preprocessing |
| --- | --- |
| Scientific meaning before syntax | Explain verified units, array shape, index base, orientation, special values and input/output contracts where they are not evident. |
| Why → What → How | State an established scientific or technical reason first, then the data/product affected, then a non-obvious implementation detail. Omit narration of simple assignments and loops. |
| Evidence before interpretation | Separate observed behavior, maintainer-confirmed intent and open questions. An equation or variable name alone is not evidence of its scientific purpose. |
| Responsibility and interfaces | Make configuration, execution control, file access and calculation stages recognizable; distinguish callable interfaces from implementation details. Use comments/grouping before proposing a structural rewrite. |
| Numerical and data preservation | Preserve arithmetic/reduction order, kinds, thresholds, masks/sentinels, array/record order, filenames and supported interfaces under the root policy. A readability pass is not an optimization or scientific correction. |
| Proportional structure | Prefer small cohesive changes. Do not add modules, dependencies, helper layers or defensive checks merely to make code appear uniform. |
| Useful failures | The Fortran/Python data consumer owns input validation and diagnostics identifying the operation and file/tile. Preserve current conditions, exit codes and message contracts during readability work. |

Use blank lines for a change in scientific/computational purpose; keep an
operation with its error check. Do not mechanically decorate every statement.
Preserve copyright, licence and attribution text. Report a material uncertainty
for separate review instead of inserting an invented Why.

### Main Procedure Transparency

Apply this principle to Fortran, Python and Shell main procedures: a reader
should understand the purpose, main inputs, scientific decisions and outputs
without opening helper implementations.

- Keep major scientific calculations and selection conditions visible near the
  top of the execution flow. Move technical I/O, validation and memory details
  into cohesive helpers where useful, without hiding the data they handle.
- **I/O Visibility Principle:** show major scientific inputs and outputs in the
  main flow: filenames, receiving/written variables, roles and units. Expose
  meaningful Binary record numbers/layouts at the call site where needed.
  Prefer explicit path/array/record arguments over opaque calls such as
  `read_base_map()` or `write_results()`; use short comments for their meaning.
  Low-level open/read/write/close, size checks and I/O diagnostics may stay in
  helpers. Scientific data dependencies must remain visible; temporary files,
  internal buffers and incidental configuration need not all be listed.
- Choose helper boundaries by responsibility, not line count. Avoid splitting
  small operations when doing so obscures dependencies, or introducing trivial
  wrapper layers. Prefer comments explaining scientific meaning and products
  over narration of syntax.
- Preserve check locations, failure conditions, arithmetic order and data
  contracts when extracting details. Separation does not authorize changing
  scientific behavior or moving necessary checks past the consuming operation.
- Review the main procedure on its own: which files are read, what their data
  mean, which conditions select data, how values are aggregated, and what is
  written where? If those answers require opening helpers, improve the call
  sites rather than returning bulky I/O or defensive code to the main flow.

## B. Language-specific application

### Fortran

Follow the [root declaration/readability guidance](../AGENTS.md#fortran-source-readability).
For new or edited lines, aim for at most **128 characters** including indentation;
use free-form continuation where appropriate. Do not rewrap unrelated historical
code, preprocessor guards or fixed-form source mechanically.

- Keep `IMPLICIT NONE`, imports and declarations recognizable. Prefer
  `USE ..., ONLY:` for new dependencies when practical; preserve existing kinds,
  imports, declaration order, array shapes and initialization during style work.
- Group declarations by scientific/computational role. Include verified units,
  dimensions, index conventions and sentinel roles rather than guessed meanings.
- Keep calculations and I/O recognizable as separate stages. Add a small
  procedure inventory with one-line responsibilities only when a long file
  benefits from it; do not split procedures in a comment/formatting task.
- Preserve local capitalization, indentation and established spellings such as
  `REAL*8`. Existing map-tool `[1]`, `[2]` headings and
  `! ================================================` separators are valid;
  use them for major process changes, not around every branch.
- Retain the map tool families and scoped shared-module naming from the
  [root naming rules](../AGENTS.md#shared-fortran-module-naming-maptoolscode).
  Do not rename established interfaces to enforce style.

### Python

Use [Python Design](python_design.md) for scientific/workflow decisions and
[Python Style](python_style.md) for local presentation, under the
[root policy](../AGENTS.md#python-source-readability). The preprocessing contracts
below remain applicable; do not transfer Fortran layout or line limits to Python.

Give standalone modules a short purpose docstring. Use cohesive functions and
necessary type hints/docstrings to expose units, array dimension order, dtype,
missing-value behavior and ownership of I/O. Document automatic masking/scaling
or raw-bit handling where it affects the tool contract; do not change that
behavior during readability work. Avoid trivial helpers, duplicate
transformations and framework-like abstractions that obscure the data path.
For standalone CLI stdout, follow the input/parameter/calculation/output
conventions in [Python Design](python_design.md#standalone-cli-output). Keep
Shell step messages in Shell, and report map files at their resolved paths only
after successful reads or writes.

For preprocessing CLIs, normally use positional arguments for required core
inputs and essential parameters that are always supplied; keep their order
stable and documented. Use lowercase, hyphen-separated named options for
optional behavior and parameters with defaults. Prefer boolean flags such as
`--check-map` with `action="store_true"` over optional positional keywords.
Avoid excessive positional arguments when their meaning becomes difficult to
distinguish. Apply this convention when creating or refactoring a tool; it does
not require immediate repository-wide migration. Preserve numerical behavior
when modernizing an interface.

### Shell

Follow the [root Shell policy](../AGENTS.md#shell-script-design-principles).
Shell should read like commands a human would execute: visible settings, working
directory, program calls and meaningful completion/error summaries. Keep the
`User settings` section near the beginning, use explicit literal assignments,
and retain environment fallbacks only for documented intentional interfaces.

For every newly written or refactored map-preprocessing workflow, use this
initialization block immediately after the script header and `set -eu`, in this
exact order:

```sh
# CaMa-Flood general setting (check CMF root, import CMF common shell functions)
PYTHON_CMD="python3"
: "${CMF_V50_ROOT:?CMF_V50_ROOT is not set. Run s00-configure_cama_root.sh first.}"
. "$CMF_V50_ROOT/tools/cmf_shell_functions.sh"
```

When selecting a high-resolution map, explain the selection briefly at the call
site:

```sh
HIRES_TAG=$(cmf_select_hires_tag "$HIRES_TAG")  # Select high-res map (e.g., 1min, 15sec, 3sec).
HIRES_TAG=$(cmf_select_hires_tag "$HIRES_TAG" --single-area)  # Select a single-area high-res map.
```

For input-matrix workflows, label grid settings as properties of the external
runoff input, not the CaMa-Flood map domain. For example:

```sh
# Standard global 1-degree ELSE_GPCC runoff input grid.
ROFFTAG="test-1deg"  # Runoff dataset/grid identifier.
GRSIZEIN=1.0         # Input runoff grid resolution [degree].
WESTIN=-180.0        # Input runoff grid western boundary [degree].
EASTIN=180.0         # Input runoff grid eastern boundary [degree].
NORTHIN=90.0         # Input runoff grid northern boundary [degree].
SOUTHIN=-90.0        # Input runoff grid southern boundary [degree].
OLAT="NtoS"          # Input runoff grid latitude ordering (north to south).
HIRES_TAG=""         # Empty recommends the coarsest available high-res map.
```

Start the separately labeled `User settings` section immediately afterward.
Keep scientific parameters, dataset identifiers and essential input paths in
that section; do not duplicate interpreter or ROOT initialization there.

Do not use the obsolete `CMF5_ROOT` or guess the repository root from a
relative path. Use `cmf_check_init`, `cmf_check_step` and `cmf_check_success`
instead of inline traps or duplicated progress banners. Locate shared map
programs with `CODE_DIR="$CMF_V50_ROOT/map/tools/code"`; keep map-specific
paths relative to the selected map directory. Apply this incrementally as
individual workflows are refactored, not as a repository-wide cleanup.

Product Shells own dataset/region/period/time-resolution/format settings.
Download and Convert Shells receive explicit arguments and orchestrate the
corresponding Python programs. Map wrappers select configuration and sequence
commands. Scientific transformations, file/metadata validation and detailed
diagnostics belong to Fortran/Python, not duplicate Shell implementations.
Keep only the command parsing and job/log control required by the existing
interface; do not add new parsers, fallback paths, nested helpers or log chatter
for hypothetical cases. Preserve existing CWD/explicit external-map conventions.

Make the invoked program recognizable at its command site. A shared directory
variable such as `CODE_DIR` is useful, but avoid separate `EXEC_*` variables
that hide the program name; prefer `"$PYTHON_CMD" "$CODE_DIR/program.py" ...`
directly. Do not add preflight `[ -f ]` checks for an explicitly invoked
program unless the Shell must select or prepare it; let the command fail and
use the workflow's normal error reporting.

### Standard preprocessing Shell structure

New or refactored preprocessing wrappers use four recognizable parts:

1. **CaMa-Flood general setting:** the standard block above (Python interpreter,
   ROOT validation and common Shell function import).
2. **User settings:** scientific parameters, input datasets and essential paths.
3. **Processing steps:** direct Python calls with required positional arguments,
   using `cmf_check_init`, `cmf_check_step` and `cmf_check_success` for progress.
4. **Optional Python CLI flags:** a concise reference at the end, grouped by
   invoked program. Document only supported options; the comments do not set
   flags or add Shell selection variables.

Python CLIs should keep essential files and always-required scientific
parameters as stable positional arguments. Standard choices belong in Python
defaults (for the channel tools: NetCDF maps, NetCDF runoff and input-matrix
interpolation). Optional or legacy behavior uses descriptive named flags. Shell
wrappers retain scientific settings but should not repeat defaults or expose
rare modes through extra variables. Group optional-flag comments after the
processing commands and success call, separately for each Python program.

For new or readability-refactored map wrappers, use simple assignments for
scientific settings and input paths. Put standard processing choices in Python
defaults rather than repeating them as Shell settings. Add a legacy-mode flag
directly to a Python invocation only when that workflow needs the legacy mode.
Retain environment overrides only when they are an intentional, documented
interface. Load required shared Shell libraries near the start, with each
required environment-variable check in the calling script immediately before
the source command. For paths, use the repository root for centrally maintained
shared data and the map root for map-specific data; keep that ownership clear
in the setting comment.

## Component data contracts to keep visible

### Maps

Consult [map metadata](../variable_table/map_metadata_spec.md) and the maintained
[variable registry](../variable_table/map_variables.csv), rather than copying
its complete table into source comments. Explain the relevant subset at its
reader/writer boundary:

- River-network and unit-catchment topology, bifurcation relationships, and
  1-based/0-based indices; do not infer current shape from historical names.
- Array orientation and Binary dtype/signedness, complete-record order and
  endianness; Fortran `(NX,NY)` with x fastest differs from Python axis notation.
- NetCDF variable names, dimensions, coordinate direction, fill values and
  other meaningful special codes; masks must not silently reinterpret codes.
- Resolution, units, cell centers versus edges and extraction boundary rules.
- MPI partition/ordering and parallel task/output ownership; formatting must
  not change reductions, scheduling, shared state or numerical reproducibility.

`diminfo_*.nml` is simulation dimension information for both model and input
grids; `inpmat_*.nc` is their correspondence matrix (with optional Binary
compatibility form). The descriptor is a native `&DIMINFO` Fortran Namelist,
read and written by Python through `f90nml`; legacy positional TXT files use
the explicit migration tool. Metadata role, storage format and distribution
role are separate concerns. Registry maintenance and maintainer-controlled
fields remain governed by the root metadata policy.

### Runoff inputs

Use the [input guide](../inp/README.md) and dataset README for units, space/time
axes, dtype and missing values. Distinguish accumulated depth, timestep depth,
rates and means; file grouping is independent of time resolution and does not
imply averaging. Keep date boundaries, record origins and any padding explicit.
The [ERA5-Land guide](../inp/download_ERA5-Land/README.md) defines the Product →
Download → Convert responsibilities. Its
[KG-0019](../research/records/knowledge_gaps/KG-0019.md) time-attribution question
remains open. Comment improvements do not authorize changing accumulation
handling, negative/reset rules, timestamps or units.

## C. Model-specific conventions not transferred

Do not impose `CMF_DRV_*`, `CMF_CTRL_*`, `CMF_CALC_*`, `YOS_CMF_*`, model utility
prefixes, model `LOGNAM`/`CMF::` message formats, or source-model Namelist
registration/alignment on preprocessing tools. Model driver/coupler lifecycle,
time advancement, Restart ordering, model state ownership, and exact procedure
inventory duplication are specific to their owning source modules. Do not import
`PARKIND1` kinds or the historical model-name prefix taxonomy merely for visual
consistency. Preserve the standalone tool's verified types and interfaces.

## Applying the guide without a rewrite

Inspect only the target code and immediate contracts needed to explain it.
Separate comment/layout improvements from proposed function extraction, new
I/O modules or pipeline changes. For a comment-only pass, use changed links,
syntax and source/token or AST comparison to confirm unchanged executable
content; use the root validation policy if a task changes behavior. Do not run
large map generation or long model experiments to validate prose.

Known improvement candidates, not changes authorized by this guide, include
separating file discovery/metadata checks from conversion in long standalone
tools and making scientific kernels easier to test independently. Preserve the
existing architecture until an individually scoped task justifies restructuring.

### Open questions and review limits

No new scientific interpretation is established by this guide. Existing
component questions, including KG-0019, remain in their authoritative records.
The conventions/readability review found no material new scientific or
architectural gap requiring a decision in this task. It does not certify
conformance of every existing file or cross-component/release readiness.

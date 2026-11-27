# CaMa-Flood Python Design Conventions

## Purpose and scope

This guide describes the design of new or substantially modified Python scripts used in CaMa-Flood scientific processing, tutorials, and visualization. It complements [Python Source Style](python_style.md), which governs file-local presentation. The [root development policy](../AGENTS.md) and applicable component `AGENTS.md` files govern authorization and scope; preserve verified scientific data contracts and more specific component conventions. Use the [development rules index](development_rules_index.md) to find them. These guidelines are recommendations for new work and focused refactoring, not a mandate to rewrite existing scripts.

The goal is **human-configurable, AI-executable, and AI-independent** research: researchers should understand a workflow, change common settings, and run it without editing Python internals or relying on an AI agent. Scientific accuracy and reproducibility take priority over stylistic uniformity.

## 1. Workflow-first organization

- A script should state its scientific purpose and high-level processing sequence in a short module docstring before implementation details.
- Python entry points should normally use `main()` near the end, followed by `if __name__ == "__main__": main()`. Do not force the Fortran principal-procedure-first source order onto Python.
- **Workflow first means conceptual visibility, not placing executable statements at the top.** Keep `main()` readable as an ordered overview: parse inputs, load data, transform/analyze, visualize/export. Split it only when doing so clarifies responsibilities.
- Small, linear scripts may keep the operation inside `main()`; avoid extracting one-use wrappers solely to meet a length target. A larger `main()` that mixes CLI parsing, data transformation, and detailed plotting is a candidate for focused decomposition.
- Separate responsibilities where beneficial: I/O, scientific transforms, plotting, and orchestration. Do not build a generic framework for a single tutorial step.
- Keep import-time side effects minimal. Parsing arguments, writing files, downloading data, and executing a model belong in the explicit entry path, not at module import.

### Standalone CLI output

A standalone scientific program should make its own execution understandable when run without its Shell wrapper. Report the main inputs actually read, calculation-affecting parameters, the principal calculation or transformation, and outputs after their writes succeed, as relevant. Include resolved paths so NetCDF/Binary selection and output-directory overrides are unambiguous. For a simple equation, show the implemented expression with the actual runtime values; for a complex algorithm, give a short method description. Do not dump the argument namespace, repeat paths, or print incidental implementation files. Report only optional outputs that were enabled and successfully written.

Use concise ordinary `print()` messages and major-stage progress only when useful, especially for long-running work. Do not add a logging framework, verbosity mode, per-cell messages, or duplicate Shell `[STEP]`/success banners. Shell remains responsible for user settings, workflow ordering, step headings and final workflow status; Python remains responsible for data I/O, scientific parameters, calculations and program-level progress. Keep stdout useful when the CLI is invoked directly.

When displaying a formula, preserve all terms and conditions. For example, print `rivhgt = max(1.0, 0.1 * Q^0.5 + 0.0)` using the invocation's actual values; do not omit offsets, thresholds or masks.

## 2. Human-facing configuration and ownership

- For Tutorial and visualization workflows with a Shell entry point, put **commonly changed** experiment, dataset, temporal, geographic, and figure settings in a clearly labeled `User settings` section in the Shell script. Each setting requires a useful inline comment describing meaning, units, valid options, and important special behavior when applicable.
- Python receives these settings through explicit CLI arguments, validated metadata, or an existing documented configuration contract. Do not maintain competing user-editable values in Shell and Python. Existing Python CLI defaults may remain for direct-call compatibility, but explicitly supplied Shell values take precedence; they are not a second routine configuration interface.
- Keep large station lists, scene inventories, and other structured inputs in their authoritative CSV/JSON/NetCDF metadata; expose their file path rather than duplicating the contents as Shell variables.
- Internal implementation constants, physical definitions, standard category labels, and non-user-facing algorithms stay in Python or the relevant authoritative data contract. **Not every literal is a user setting.**
- Default values in Python must not silently override a Shell value. Distinguish a user setting from a derived value and from immutable reference metadata.
- Standalone library functions do not require a Shell wrapper. Follow the owning component's interface conventions.

## 3. Scientific semantics and data contracts

- Document scientifically consequential quantities: physical meaning, units, temporal support (instantaneous/mean/maximum), geographic reference system, spatial resolution, dimension order, coordinate orientation, sentinel values, masks, and category definitions where relevant.
- Explain *why* an uncommon transform or mask is needed and *what* the result represents, before narrating individual operations. Examples include treating GFM `255` as NoData rather than dry land, or distinguishing the fraction of valid classified pixels from the flooded fraction of a whole grid cell.
- Do not assume a variable's meaning from its name. Verify against the implementation, metadata, or agreed scientific design. If unknown, state the uncertainty; do not create a confident comment from a guess.
- Separate measured, simulated, derived, and display-only quantities. Do not label a satellite classification as model inundation depth, or a water-including river pixel as necessarily overbank flooding.
- Data and output contracts belong at the function boundary (docstring where nontrivial), supported by authoritative external specifications. Avoid duplicating full contracts in every caller.

## 4. Function interfaces and state

- Prefer explicit inputs, return values, and `pathlib.Path` for paths when consistent with nearby code. Type hints are encouraged where they clarify contracts; they are not a reason to construct complex type hierarchies.
- Make nontrivial scientific contracts visible at the function boundary. Use the [function/docstring presentation guidance](python_style.md#3-functions-and-docstrings) for their concise written form; do not repeat full external specifications in each caller.
- Group related constants and data definitions by role. A dataclass or another structured type is optional when it makes related data easier to understand, not a required pattern.
- Avoid mutable global workflow state. Module constants for truly fixed classifications or conventions are acceptable. Event-specific, user-editable settings should not silently live as Python globals when the established interface is Shell/metadata.
- Prefer one authoritative operation over duplicate transformations scattered across plotting functions. Preserve file and step handoff contracts.

## 5. Reproducibility and errors

- Preserve input provenance, selected time, units, transformations, and important configuration in saved outputs or the established Step metadata/Work Report. Do not invent redundant tracking structures.
- Keep validation close to the code consuming the input. Fail clearly on missing required inputs, unsupported options, inconsistent CRS/time semantics, or invalid data contracts. Do not silently substitute scientifically different methods.
- Distinguish valid zero/dry values from NoData and outside-domain pixels. Preserve category values and documented resampling behavior.
- Use informative, targeted progress and error messages; avoid logs per pixel/row or repeated noise. Do not change existing error or logging behavior in a style-only pass.
- Keep generated outputs and tracked source data separate according to the owning Tutorial/visualization rules. Do not publish to the Visualization Gallery without explicit authorization.

## 6. Scientific and compatibility preservation

A dedicated readability or formatting pass must **not** change calculations, operation order, float precision or dtype, interpolation/resampling, mask precedence, aggregation periods, coordinate handling, array orientation, input/output names, CLI interfaces, file formats, external service behavior, or default figure semantics. Even apparently equivalent refactors can change scientific results.

If a proposed change would modify those contracts, separate it from style cleanup and follow the [root approval and validation policy](../AGENTS.md). Obtain approval when that policy requires it, for example for intentional numerical changes or compatibility-breaking interfaces; this guide adds no new approval gate. Do not conceal it within comment cleanup. Preserve existing licenses and attribution.

## 7. Scope and validation by development stage

Apply the [root staged validation policy](../AGENTS.md#cama-flood-v5-test-design-principles); the distinctions below route effort, not add a separate test mandate.

- **Writing the guidance:** review consistency with existing Fortran, Tutorial and visualization documents; no Python execution is required.
- **Style-only update:** inspect the diff, syntax-check changed files where practical, and confirm there is no change in logic or public interfaces. Do not rerun unrelated scientific simulations.
- **Interface change:** test the affected Shell-to-Python option flow and a representative invocation; verify defaults remain unchanged.
- **Scientific processing change:** follow the repository's risk/stage guidance and validate the actual modified data contract with representative evidence.

A code review should classify findings as style/readability, documented uncertainty, or scientific change. Report out-of-scope matters instead of expanding an assigned formatting task.

## 8. Relationship to other guidance

- [Python Source Style](python_style.md): module docstrings, comments, spacing, naming, section headings, and local readability.
- [Fortran Design](../src_main/FORTRAN_DESIGN.md) and [Fortran Style](../src_main/FORTRAN_STYLE.md): analogous principles for Fortran; Python does not inherit Fortran-specific syntax, procedure ordering, model naming, or logging rules.
- [Tutorial development guidance](../tutorial/agent_tutorial_development.md): executable tutorial contracts and learner-facing workflow; tutorial-specific specifications and local agent rules remain applicable.
- [Visualization development guide](../visualization/repository_development_guide.md) and [figure-making guideline](../visualization/figure_making_guideline.md): Shell/Python responsibilities, figure configuration ownership, project structure and scientific/visual conventions.
- [Shared preprocessing conventions](preprocessing_code_conventions.md): map/input workflow visibility, language-specific application and component data contracts.
- [Root AGENTS](../AGENTS.md) and applicable component instructions: authoritative approval, branch, scope, safety, reporting, and publication policy.

# CaMa-Flood Python Source Style

## Purpose and scope

This is a file-local readability guide for Python scripts in CaMa-Flood. Use [Python Design Conventions](python_design.md) for architecture, scientific semantics, data contracts, and behavior-preserving implementation decisions. This document applies primarily to new scripts, substantially modified files and explicitly assigned readability/formatting passes; do not reformat the repository wholesale. Follow the [root policy](../AGENTS.md), applicable component instructions and established local style for older utilities.

**Design goal: Workflow First.** A human reader should recognize the purpose and execution sequence before studying scientific or plotting details. Python's conventional `main()`-at-bottom layout is compatible with that goal when the top-level module docstring explains the workflow.

## 1. Recommended file order

For a nontrivial executable script, prefer:

1. Shebang (if executable) and a meaningful **module docstring**.
2. `from __future__` imports where used, then standard-library, third-party, and local imports.
3. Documented immutable constants and shared definitions.
4. Helper functions, organized by responsibility or approximate workflow order.
5. `main()` as the concise orchestration entry point.
6. `if __name__ == "__main__": main()` at the end.

Do not move `main()` above helpers merely to copy Fortran's procedure ordering. Do not introduce a placeholder `main()` for a reusable library module without an executable entry point.

### Module docstring

For a substantial script, communicate purpose, key inputs, output, and 3–5 workflow stages. Mention scientifically consequential limitations. Prefer concise text to a boilerplate inventory of every function. Small, self-explanatory scripts can use a short summary plus any critical scientific caveat.

```python
#!/usr/bin/env python3
"""Plot model and observation discharge at selected stations.

Inputs: matched time-series CSV and comparison metadata.
Output: multi-panel hydrograph PNG.
Workflow:
    1. Read and select time series.
    2. Plot model and observed values.
    3. Save the figure.
Note: observation time zone and units may be unconfirmed.
"""
```

Do not claim that a workflow performs a conversion or validation that is not in the code.

## 2. Layout, naming, and imports

- Use four spaces per indentation level and generally follow PEP 8 naming (`snake_case` functions/variables, `UPPER_CASE` constants). Preserve existing public identifiers unless a separately approved change requires renaming.
- Prefer readable lines and the established local style. A line up to about 160 characters may remain unwrapped when a single expression or call is clearer that way, as allowed by the existing root convention. This is not a target width or a strict formatter limit; do not impose an 88-, 120- or 128-character-only rewrite on legacy files.
- Use parentheses for multi-line expressions and calls rather than backslash continuation.
- Keep import groups visually separate. Preserve necessary import ordering for backend setup or documented side effects (for example, setting a matplotlib backend before importing pyplot).
- Avoid `from module import *` in new code. Do not rewrite unrelated imports or force a formatter/linter where the project has not adopted one.
- Use blank lines for changes in processing purpose, not mechanically around every conditional or loop. Two blank lines between top-level functions; consistent whitespace within a function.

## 3. Functions and docstrings

- Give principal functions and scientifically nontrivial helpers a purpose-first docstring. Simple helpers may use a single line.
- Use a longer docstring when parameters, returns, units, side effects, time meaning, grid/mask conventions, or assumptions are otherwise unclear. One consistent plain-English format is enough; NumPy-style parameter sections are optional, not compulsory.
- Avoid documenting obvious Python types at length when type hints already convey them. Prefer explaining physical and scientific meaning.
- Use type hints where they clarify inputs, results or data roles; annotating every trivial helper or constructing type hierarchies is not required.
- Present `main()` as a readable sequence of meaningful steps; use [Design section 1](python_design.md#1-workflow-first-organization) for decisions about decomposition.
- In a standalone CLI, use concise `Inputs`, `Parameters`, `Calculation`, and `Output` labels only when they help. Print resolved paths and actual runtime equation values; report a product only after its write succeeds. Keep program output independent of its Shell wrapper and follow [Design section 1](python_design.md#1-workflow-first-organization) for responsibility boundaries. Do not duplicate Shell step banners or add a logging/verbosity framework.
- Separate argument parsing, input reads, calculation, and writes with blank lines; use numbered `#*** N.` headings only when a program's length or stages benefit from them. Do not add headings to short linear CLIs.
- New helper names should express their effect (`load_classification`, `select_station_series`, `render_panels`) rather than generic terms such as `process_data`.

## 4. Comments and visual hierarchy

### Scientific comments

Prioritize **Why**, then **What**, then **How** when the algorithm is not obvious. Document nontrivial assumptions, units, mask meanings, temporal alignment, provenance, and intentional scientific constraints. Do not repeat code syntax in prose.

```python
# GFM code 255 means NoData, not valid dry land.
# Mask it so absent observations do not appear as non-flooded pixels.
masked = np.ma.masked_equal(data, 255)
```

### Major process headings

Within `main()` or a large processing function, label only meaningful major stages. To parallel the Fortran `!*** N.` convention, use the Python form `#*** N. ...` when a numbered workflow improves scanning:

```python
def main() -> None:
    """Run the hydrograph comparison workflow."""
    #*** 1. Read user-provided inputs
    args = parse_arguments()
    records = load_timeseries(args)

    #*** 2. Select comparison data
    selected = select_stations(records, args)

    #*** 3. Plot and save
    figure = render_hydrographs(selected, args)
    save_figure(figure, args.output)
```

- Number stages in execution order within that function; update outdated numbers or descriptions during related edits.
- Number only important stages, not every assignment, `if`, or `for`. Short functions need no numbered headings.
- A normal `# Read input` comment is sufficient for a minor transition; blank lines may be clearer than headings.
- Avoid decorative separator blocks around each function. Keep larger section separators only where an existing file uses them consistently and they clarify navigation.

## 5. Constants and user settings

- Explain non-obvious scientific constants near their declaration (units, category meanings, source, domain of validity). Do not add redundant comments to self-explanatory values.
- Use [Design section 2](python_design.md#2-human-facing-configuration-and-ownership) for configuration ownership and structured inputs. For an actual user-facing Shell setting, the **Shell inline comment** is the primary immediate guide; Python arguments may include concise `help=` text as well. Keep that text aligned with the implemented units, choices and special behavior; do not advertise hypothetical options.

## 6. Style-only review boundaries

A style pass may improve docstrings, comments, local spacing, grouping, and clear naming of new private symbols. It must preserve scientific meaning and runtime behavior. In particular:

- Preserve the scientific and compatibility contracts listed in [Design section 6](python_design.md#6-scientific-and-compatibility-preservation), including logging and error behavior. A style pass does not authorize functional changes.
- No new helper abstractions merely to fit the template; function extraction is a separate focused readability/refactoring task when needed.
- No wholesale autoformatting or unrelated edits.
- If scientific meaning is uncertain, flag it rather than inventing a docstring.

## 7. Lightweight review checklist

For the changed file only, ask:

1. Can a researcher learn the purpose, inputs/outputs, and processing sequence from its header?
2. Is the executable flow understandable through `main()` or the existing entry point?
3. Do nontrivial functions and scientific transformations explain their contracts and important assumptions?
4. Are the comments accurate, concise, and free of syntax narration?
5. Are Shell-controlled settings and Python internals clearly separated?
6. Did the style pass leave processing, scientific semantics, and public behavior unchanged?

For documentation-only work, inspect references and examples; do not run science workflows. For a later code-formatting pass, use focused syntax/diff checks as appropriate and leave broader validation to changes that affect contracts.

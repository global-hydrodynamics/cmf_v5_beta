# Development Rules and Guidance Index

Use this page to find the current instructions for a component. It is a
navigation aid, not an independent policy source. The root [`AGENTS.md`](../AGENTS.md)
governs repository-wide approval, branch, safety, research, and publication
rules. Check every applicable `AGENTS.md` on the path being changed, then read
only the guidance needed for the task.

## How to read these documents

- **Policy / agent instructions** govern how work is authorized and carried out.
- **Design specifications and contracts** state intended behavior and data
  interfaces; they do not prove that a feature is implemented or validated.
- **Guides and READMEs** explain a component's maintained workflow and usage.
- **Plans, logs, and research records** preserve proposals, decisions, history,
  and evidence. They are not automatically current implementation authority.
- **Skills** provide a procedure for finding and applying rules. They do not
  replace the rules themselves.

When a task spans components, apply the relevant guidance for each component.
Do not copy the same policy into multiple documents; update its authoritative
source and link to it.

## Repository and component guidance

| Area | `AGENTS.md` | Primary guidance | Document role / notes |
| --- | --- | --- | --- |
| Repository-wide development | [`../AGENTS.md`](../AGENTS.md) | [`docs/ai_development_workflow.md`](ai_development_workflow.md); [`docs/development_and_distribution_design.md`](development_and_distribution_design.md) | Root AGENTS is authoritative policy. AI workflow is a handoff/evidence process; development and distribution document is the maintained architecture/design specification. |
| `src_main/` model Fortran | [`src_main/AGENTS.md`](../src_main/AGENTS.md) | [`src_main/FORTRAN_DESIGN.md`](../src_main/FORTRAN_DESIGN.md); [`src_main/FORTRAN_STYLE.md`](../src_main/FORTRAN_STYLE.md) | Design conventions cover scientific/runtime architecture and contracts; style guide covers source readability and formatting. |
| `map/` preprocessing | [`map/AGENTS.md`](../map/AGENTS.md) | [`docs/preprocessing_code_conventions.md`](preprocessing_code_conventions.md); [`variable_table/map_metadata_spec.md`](../variable_table/map_metadata_spec.md); [`variable_table/map_variables.csv`](../variable_table/map_variables.csv); component READMEs | Shared code conventions and map-data contracts; local READMEs document commands and map-specific paths. |
| `inp/` runoff preparation | [`inp/AGENTS.md`](../inp/AGENTS.md) | [`docs/preprocessing_code_conventions.md`](preprocessing_code_conventions.md); [`docs/netcdf_output_conventions.md`](netcdf_output_conventions.md); [`inp/README.md`](../inp/README.md); [`inp/runoff_datasets.csv`](../inp/runoff_datasets.csv) | Shared code conventions, NetCDF output contract, dataset guide and registry. ERA5-Land details and unresolved KG-0019 are in the linked input documentation/research record. |
| `gosh_test/` execution examples | [`gosh_test/AGENTS.md`](../gosh_test/AGENTS.md) | [`gosh_test/README.md`](../gosh_test/README.md); maintained experiment scripts | The local AGENTS document is explicitly a working draft of recommended practices, not a finalized standard. Root policy remains authoritative. |
| `tutorial/` | [`tutorial/AGENTS.md`](../tutorial/AGENTS.md) | [`tutorial/agent_tutorial_development.md`](../tutorial/agent_tutorial_development.md); [`tutorial/agent_manual_authoring.md`](../tutorial/agent_manual_authoring.md); [`tutorial/how_to_develop_tutorials.md`](../tutorial/how_to_develop_tutorials.md); each tutorial's design specification | Reusable agent instructions and human workflow guide; each tutorial design is its own experiment/learning contract. The requirements CSV is a review aid, not a specification replacement. |
| `visualization/` | [`visualization/AGENTS.md`](../visualization/AGENTS.md) | [`visualization/repository_development_guide.md`](../visualization/repository_development_guide.md); [`visualization/figure_making_guideline.md`](../visualization/figure_making_guideline.md); [`visualization/visualization_catalog.csv`](../visualization/visualization_catalog.csv) | Development guide defines project structure, names, workflow and publication; figure guideline covers scientific/visual quality; catalog is a discovery/status index. Use `cama-visualization` for this work. |
| `package/` | [`package/AGENTS.md`](../package/AGENTS.md) | [`docs/development_and_distribution_design.md`](development_and_distribution_design.md); [`package/README.md`](../package/README.md); [`package/PACKAGE_DATA_README.md`](../package/PACKAGE_DATA_README.md); [`package/package_data.csv`](../package/package_data.csv) | Maintained design specification plus operational guide and selection catalog. Additional-data README is Git-managed documentation; the external data store is not the default editing target. |
| `research/` | None | [`research/README.md`](../research/README.md); relevant decision, discussion, gap, validation, or stage record | README governs evidence, privacy and record structure. Individual records preserve evidence/history; they are not general coding rules. |
| `tools/`, `config/`, `etc/` | None | Directory [`README.md`](../tools/README.md), [`README.md`](../config/README.md), or [`README.md`](../etc/README.md), plus root AGENTS | Component-specific usage and paths; no separate agent-policy file currently exists. |
| `legacy/` | None | Local [`README.md`](../legacy/src/README.md), [`README.md`](../legacy/adm/README.md), and [`README.md`](../legacy/gosh/README.md) | Historical reference. Do not treat legacy instructions as current maintained v5 workflow unless a task explicitly targets it. |

## Skills: when to combine them

| Skill | Responsibility |
| --- | --- |
| [`cama-development`](../.agents/skills/cama-development/SKILL.md) | Discover and apply the CaMa-Flood repository and component rules. |
| [`large-model-refactoring`](../.agents/skills/large-model-refactoring/SKILL.md) | Choose scope and validation effort based on development stage and scientific risk. |
| [`cama-visualization`](../.agents/skills/cama-visualization/SKILL.md) | Implement and review visualization-specific structure, science, graphics, and publication. |

For example, a `src_main/` numerical change uses the repository and Fortran
rules plus risk-proportionate validation; a Tutorial 11 figure uses tutorial
and visualization rules, without implying Gallery publication; package work
uses repository approval rules and the package design/catalog. Apply only the
Skills relevant to the assigned task.

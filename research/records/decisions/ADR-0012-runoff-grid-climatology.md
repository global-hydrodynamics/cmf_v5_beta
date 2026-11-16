# ADR-0012: Runoff-grid climatology with explicit daily coastal-minimum semantics

- Status: accepted scope by explicit maintainer task; AI-authored summary pending maintainer review
- Date: 2026-11-16
- Task: DT-0105; events: EV-0486, EV-0487, EV-0488, EV-0489
- Owner: Dai Yamazaki (maintainer); implementation: Codex
- Approved working branch: feature/package-builder; no commit/push authorized

## Context and confirmed decision

The maintainer requested reproducible ELSE_GPCC 1981–2010 climatology from
NetCDF and reusable processing for other runoff products. Section 13 explicitly
requires preservation of scientific Why, units, assumptions and compatibility
limits. The climatology supplies mean discharge for channel width/depth
estimation. Zero/missing runoff can prevent estimates for small coastal rivers;
a land mask must not be mandatory. Minimum-neighbor filling is a conservative
choice, not a physically proven optimum.

Compute on the runoff grid without river maps, diminfo or Input Matrices.
Preserve the 365-day cycle, omit February 29, correct original source days using
a frozen uncorrected-mean donor/target mask, then re-average. Do not substitute
minimum of an already averaged field. The removal of Input-Matrix selection is
an approved scientific-domain change, not merely a language translation.
All intermediates/exports stay under ignored workflow output; do not replace
map/data/ELSE_GPCC_clm-1981-2010.one or modify the input NetCDF.

## Verified legacy behavior and implementation choices

[day_clim.F90](../../../etc/runoff_preset/src/day_clim.F90) averages matching
calendar days in year order. [ave_clim.F90](../../../etc/runoff_preset/src/ave_clim.F90)
actually writes their annual sum, not a mean rate. The v5 final field explicitly
divides by 365*86400 to satisfy the existing channel reader's mm/s contract.
[mod_runoff.F90](../../../etc/runoff_preset/src/mod_runoff.F90) selects mapped
nonpositive-mean targets and positive-mean donors; their daily values can be zero.
No actual coastline is tested. It wraps longitude unconditionally.

New explicit choices: invalid negative/masked/nonfinite daily values are missing;
exclude invalid daily donors, preserve valid zero donors; average valid years per
calendar day and save counts; require all 365 days for the annual mean. Reject
incomplete date coverage, unknown units/calendars and ambiguous intervals.
Wrap only full 360-degree grids. These choices are documented, not claimed to
have already been independently scientifically validated. Full ELSE_GPCC counts
are 30 for every day/cell, so missing-year exclusion does not explain this run's
differences. The main workflow uses float32 chronological sums and preserves
coordinate order. Synthetic legacy comparison is exact when masks agree.

## Consequences, evidence and knowledge review

[Implementation and rationale](../../../map/tools/script_runoff_preset/README.md)
separate confirmed intent, verified source rules and new policy. Input Matrix
use remains downstream; the same runoff product can support different maps.
Twelve [focused tests](../../../map/tools/tests/test_runoff_preset.py) pass;
VR-0151 records real-data comparison. Old reference remains unchanged.

Knowledge-gap review identified KG-0037: historical generation provenance is not
fully recoverable; changed-domain physical effects require review before manual
adoption. Inland zero filling and lack of water-balance/land-mask constraints
remain explicit limitations. No physical correctness is inferred from execution.

## Subsequent maintainer adoption — 2026-11-16

EV-0490 records the maintainer's explicit judgment that the observed differences
are acceptable and their manual copy of the new Binary/NetCDF into map/data/.
These are now the canonical climatology. EV-0491 verifies both SHA-256 hashes
against the generated files (Binary 7a5876df2934e87cb7db9ffd1ace38bc68d3f9268a7f6c3ba69c21db4108ae6a; NetCDF 4e0c5205fee14ec6ed102f239f71a070eb1f6a4beb62d961a7fbdc73ad6f981b).
No agent data copy or recomputation was performed in this follow-up. The
adoption question is settled; incomplete historical provenance and independent
physical validation remain open limitations, not reasons to ignore the newly
confirmed canonical dataset. Earlier validation statistics refer to the former
reference hash, not the adopted product.

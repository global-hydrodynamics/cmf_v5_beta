# Step24 — Flood Inundation Downscaling, Visualization, and Assessment

Only **Sentinel-1A, orbit 038784, S1A_o038784_dt049389** is processed.
The five source GRD scenes form one acquisition, not five target acquisitions.
Exact saved Step03 footprint timestamps span **2021-07-15 05:49:37.397 to
05:51:42.396 UTC**; the envelope midpoint is **05:50:39.896500 UTC**.
Nearest actual model CF output: **06:00:00 UTC**, index **341** (zero-based),
**560.1035 seconds later**. No temporal interpolation or model rerun.

## Inputs and time interpretation

The existing `experiment/Rhine2021/o_flddphRhine2021Jul.nc` contains hourly
`flddph(time,lat,lon)` in metres, `cell_methods=time: point`, with CF units
`seconds since 2021-07-01 00:00`. A missing explicit zone in CF reference-time
units uses zero offset. The Step14 Shell labels its run as UTC and feeds the
ERA5-Land UTC sequence without a local-time shift. Output labels are model
endpoint point samples (first record July1 01:00), not interval averages.
Inherited KG-0019 forcing-accumulation attribution is not resolved by this Step.
Observation metadata are read from Step03 selected passes, pass inventory and
source-product acquisition footprints; none are modified or downloaded again.

## Existing method and map compatibility

Reuse `tools/downscale_flddph/script/downscale_flddph.py`, the maintained
tributary-aware Python port of `downscale_flddph_trib.F90`. Input `flddph` is
floodplain water depth at model output time. The method assigns the coarse
catchment depth via `catmxy`, subtracts `flddif`, applies tributary/backwater
adjustments, and retains the existing `rivwth`-based permanent-water minimum
of **0.1 m**. This is not interpolation of coarse depth. No new physics or
algorithm is introduced. Additional simulation variables are not required.

Map: `map/Rhine_15min`, matching the simulation's 40×32 coarse grid and
600×480 1min grid. Required maps used in this run are NetCDF `nextxy`, `uparea`,
`catmxy`, `downxy`, `flddif`, `rivwth`; map/input cell-centre coordinates and
shape are validated by the existing implementation. Catchment indices are local
one-based Rhine indices. Actual map files and hashes are recorded in metadata.

Use Step02 **satellite analysis** bounds **4–8°E, 49–52°N**; the larger
simulation bounds are 3–13°E, 45–53°N. The five-coarse-cell internal buffer
reaches 2.75–9.25°E, 47.75–53.25°N, beyond regional map coverage at west/north.
Missing buffer context can affect boundary-adjacent tributary/backwater behavior;
this preliminary regional result has not established boundary independence.

## Reproduction and outputs

From repository root, with `.venv` containing NumPy, netCDF4 and Matplotlib:

```sh
bash tutorial/tutorial11-event_evaluation/run_script/s24-downscale_inundation.sh
bash tutorial/tutorial11-event_evaluation/plot_script/f24-inundation_1min.sh
```

The first command selects a snapshot in a temporary directory (removed after
processing) and writes exactly one final depth NetCDF in ignored `out/`:
`24_flddph_1min_S1A_o038784_dt049389_20210715T060000Z.nc`.
It may replace this reproducible Step24 output; original simulation, map and
observation inputs remain unchanged. NetCDF metadata record original source,
time index, observation envelope/midpoint, selected time/difference, method,
map sources/options, experiment, resolution and preliminary status.
`metadata/24_downscaling_verification.json` is the formal metadata handoff.
The second command only renders `figure/f24-inundation_1min.png` from that output.
Generated NetCDF data remain local and are not added to Git.

## Focused execution and verification (L0–L1)

- One acquisition, no S1B/other acquisition; midpoint computed from exact scene
  timestamps. Nearest time checked over the available CF axis; +560.1035 s.
- Output `flddph(lat,lon)`, float32 metres, **180×240**; 1/60° spacing,
  north-first latitude, WGS84 centre coordinates and exact requested outer bounds.
- **42,960 valid pixels**: 37,429 dry and 5,531 positive-depth pixels;
  **240 masked pixels**, all coincident with invalid/unmapped source `catmxy`.
- Valid depths **0–10.8741369 m**; no negative or non-finite valid values.
  Source fill 1e20 becomes masked output -9999, never dry zero.
- Saved diagnostic PNG reviewed: extent/orientation, river-like spatial pattern,
  no obvious raster-processing artifacts; dry beige, NoData gray, positive
  depths YlGnBu 0–10 m, values above scale indicated by colorbar extension.
- This establishes execution and basic consistency only. Positive depth includes
  permanent river water and is not a flood-event classification. No GFM overlap,
  accuracy metrics, 20m/finer result, other acquisition, or independent scientific
  validation. Steps01–23, source observations, model/map data and Gallery unchanged.

## Scientific-assessment documentation completion — 2026-11-24

The revised instruction makes scientific interpretation part of Step 24. The
superseded standalone-assessment request was interrupted before its write
command executed: no separate assessment-step files, references or commits
existed when checked. Nothing was deleted or reverted. Useful evidence reviewed
for that request is consolidated into the existing Step 24 Survey Report and
four-part Prompt. No separate later assessment Step is introduced.

### Sources reviewed and facts confirmed

Reviewed root/tutorial/local AGENTS, tutorial development guidance and current
process/Step prompts; applied cama-development, cama-visualization and
large-model-refactoring guidance at documentation-focused L0–L1 scope. Main
scientific evidence is the Steps 01–04,11–15,21–24 Survey/Work Reports, Step 03
classification provenance and acquisition footprint/inventory, Step 14 setup,
Step 21 allocation, Step 23 comparison/handoff and Step 24 verification metadata.
Existing Fig 1, Fig 23 and Fig 24 provide illustration, not quantitative proof.

Read actual existing NetCDF headers: flddph and outflw are 744×32×40; units m
and m 3/s respectively; cell methods time: point and time: mean. Step 14 records
15 arcmin, hourly ERA5-Land input, no spin-up and the July 1–August 1-exclusive
run. Step 24 records the exact five-scene acquisition midpoint,06 UTC selection,
+560.1035 s,1 arcmin 180×240 output and retained count/range checks above. No new
pixel statistics or hydrological analysis were computed for this update.
Step 03 source metadata confirm classes 0–4 form valid support; source code
`f03c-flood_fraction_1min.py` confirms that denominator. The full 20 m classified
TIFF remains absent; reported full-source statistics are inherited provenance.

Mohr et al.(2023), NHESS23,525–551, doi 10.5194/nhess-23-525-2023 was checked
on the publisher page for title/authorship, event context and hydrological
limitations. Official EODC GFM Recommendations were checked through indexed
service documentation (direct page exposed no readable body), supporting only
general SAR detection caveats, not a claim about the local processing version.
Links and full bibliographic references are in the Survey Report.

### Documentation changes and checks

Updated the established p 24 filename with PartsA–D and reusable instructions;
replaced the short Survey with objective/method, distribution, event context,
four limitation categories, interpretation, future directions and conclusions.
The Work Report retains actual A–C execution evidence and adds this D completion
record. Updated the workflow overview/status to identify Step 24 as the final
assessment and remove stale statements that no event simulation exists.

Focused checks: technical claims against retained JSON/CSV and actual output
headers; new/changed local links and figure paths; separation of demonstrated
facts, hypotheses and unresolved questions; review that no unperformed matching,
metric or skill validation is described as completed. Preserved prior metadata,
figures, analysis data and calculation/plotting source. No model/downscaling
run, figure regeneration, new script, observation download or accuracy analysis.

### Unresolved evidence and knowledge-gap review

The Survey does not rank insufficient simulated water, unresolved spatial
width and quantity/class mismatch as causes. River-water versus overbank
inundation, local reach support/upstream proxies, initial-state and edge-buffer
sensitivity, KG-0019 forcing-time attribution, observation support and SAR
uncertainty remain unresolved. Existing Step 22 observation units/timezone
are still unspecified. Higher-resolution maps and finer terrain address
different questions and are proposed opportunities, not guaranteed fixes.

A source discrepancy was noticed during literature review: Mohr et al.section 3.2.2
lists Prümzurlay peak level at 05:30 UTC, whereas the retained Step 01 ledger and
Step 23 reference use 10:30 UTC from their cited LfU report. These references may
reflect different estimates/definitions; that explanation is unverified. No
source was silently substituted and no discharge lag was computed for that
water-level reference. Reconciliation belongs to future observation review.
The Survey flags source-time discrepancies without treating either as resolved.

This completion is scientific synthesis and source checking, not independent
scientific validation of the existing simulation or inundation product.

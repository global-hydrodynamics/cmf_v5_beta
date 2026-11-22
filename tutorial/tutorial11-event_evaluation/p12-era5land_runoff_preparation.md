# p12 — ERA5-Land Hourly Runoff Preparation

## Workflow Summary

### Inputs
- Step 11 regional map: `map/Rhine_15min/`
- Step 2 domain and period context: `metadata/02_domain_selection.json`
- Existing ERA5-Land Product/Download/Convert workflow under `inp/download_ERA5-Land/`
- Event-specific Product Shell: `inp/download_ERA5-Land/tutorial11-Rhine_2021Jul.sh`
- Existing original and converted data under `inp/tutorial11-ERA5land-Rhine2021Jul/`, when available

### Tasks
- Check the selected runoff period and requested area against the event plan and regional map.
- Inspect existing source and converted NetCDF files and logs before deciding whether any processing is needed.
- Verify file sequence, time axis, grid coordinates, variable, units and missing-value metadata.
- Record the observed dataset contract, compatibility context and unresolved time semantics.
- Hand the forcing files and matching map-specific Input Matrix information to Step 13.

### Outputs
- Local original CDS files and converted hourly CaMa-Flood NetCDF, when already available or newly prepared
- `metadata/12_era5land_runoff.json`
- `AI_survey_report/12_era5land_runoff_preparation.md`
- `AI_work_report/12_era5land_runoff_preparation.md`

## Human Instructions

For Rhine 2021, the researcher has already run the event-specific Product Shell
and retained the original and converted data locally. Have the AI inspect those
outputs first. The data directory is ignored by Git; do not add the raw or
converted data to the repository. If the matching output files exist and are
readable, reuse them rather than downloading or converting them again.

For a new event or a missing dataset, review the target dates, region and
forcing resolution with the researcher, then copy or edit the appropriate
Product Shell settings. For this Rhine sample, the reproducible command is
`bash inp/download_ERA5-Land/tutorial11-Rhine_2021Jul.sh`; run it only when
matching outputs are absent or intentionally need regeneration. Preserve the
shared `s01-download.sh` and `s02-convert_CMF_nc.sh` processing behavior. Real
CDS downloads require user credentials and acceptance of the dataset terms. Human review of the analysis
is recommended but does not block later processing when required inputs are
present; missing or invalid data remain errors.

## Example AI Agent Prompt

```text
Prepare Step 12 ERA5-Land runoff for this flood-event evaluation.

Read the repository and Tutorial 11 instructions, the ERA5-Land workflow
README, KG-0019, the Step 2 domain metadata, the Step 11 regional-map report,
and the event-specific Product Shell. Inspect the local dataset directory,
original NetCDFs, converted NetCDFs, and available logs before running any
workflow. Do not overwrite or reacquire matching data unnecessarily.

For the Rhine 2021 sample, preserve the researcher-selected Product Shell
settings: dataset tutorial11-ERA5land-Rhine2021Jul; 2021-07-01 through
2021-07-20 inclusive; requested area 2.5–13.5°E and 44.5–53.5°N; hourly
TSTEP=1; daily download and output grouping; NetCDF; NCPUS=2. This area
intentionally extends 0.5° beyond each edge of the Step 11 map at 3–13°E,
45–53°N. Verify the actual coordinate centers and grid geometry from the
NetCDF; do not infer them only from the request.

1. Determine which source and converted files exist and whether the complete
   requested daily sequence is represented. Check timestamps for ordering,
   duplicates, gaps and expected hourly count.
2. Inspect source and converted variable names, dimensions, coordinates,
   coordinate order and spacing, units, fill/missing values, and relevant
   conversion logs. Distinguish source accumulated runoff from converted
   timestep runoff. Daily file grouping does not mean daily averaging.
3. Compare the actual 0.1° runoff grid geometry with the Step 11
   `diminfo_ERA5land_global.txt` / `inpmat_ERA5land_global.bin` pair. Do not
   regenerate the map or Input Matrix in this Step. State what metadata
   compatibility establishes and what it does not.
4. If matching converted data are absent and the researcher has authorized
   access/credentials, run the existing Product Shell; otherwise document the
   missing input without claiming it was prepared. Never change the conversion
   algorithm to resolve KG-0019.
5. Create/update `metadata/12_era5land_runoff.json`, the Step 12 Survey and
   Work Reports, and the event process references. Keep the runoff dataset
   out of Git and decide explicitly whether its event-specific nature warrants
   registry inclusion. Do not register it merely because files exist.
6. Hand off the converted-file pattern, time/grid/unit settings and matching
   Input Matrix to Step 13. Keep the event period, initial candidate analysis
   period, runoff acquisition period and eventual simulation/evaluation period
   distinct. July 1 start does not prove adequate spin-up; evaluation after
   July 20 requires extending the forcing.

Report the observed evidence, decisions, limitations and any checks not run.
Do not run CaMa-Flood, match gauges, or evaluate model skill in Step 12.
```

## Rhine 2021 reference settings

The Product Shell preserves these research-selected settings:

| Setting | Value |
| --- | --- |
| Product dataset | `tutorial11-ERA5land-Rhine2021Jul` |
| Inclusive runoff dates | 2021-07-01 to 2021-07-20 |
| Requested CDS bounds | 2.5–13.5°E, 44.5–53.5°N |
| Step 11 map outer bounds | 3–13°E, 45–53°N |
| Timestep | 1 hour |
| Download/output grouping | daily / daily |
| Format and concurrency | NetCDF / 2 jobs |

The July 1 start was selected to retain a pre-event preparation interval. It is
not a claim that a July 1 model start provides sufficient spin-up. The initial
candidate event-analysis window remains July 10–25; it is distinct from this
runoff acquisition period. A model simulation period is still a Step 13
decision. The selected runoff ends July 20, so later evaluation dates require
more forcing data.

## Scientific and technical interpretation

The source ERA5-Land runoff variable is `ro` in metres of accumulated runoff.
The existing converter writes `runoff` in millimetres accumulated over each
input timestep. For hourly data, the expected converted file has 24 hourly
records per daily file; `DOWNLOAD_UNIT` and `OUTPUT_UNIT` describe file
organization, not temporal averaging. The helper's CaMa-Flood settings report
`LINPCDF=.TRUE.`, `CROFFREQ="DAY"`, `CVNROF="runoff"`, `CVNTIME="time"`,
`IFRQ_INP=1`, and `DROFUNIT=3600000` for mm per one-hour timestep. Step 13
must check these against the actual run configuration and selected map/input
matrix.

KG-0019 remains open. ERA5-Land valid-time labels are retained; the 00 UTC
accumulation is documented as covering the preceding 24 hours. The converter's
within-day differencing and first-record treatment do not establish correct
physical attribution or complete period-boundary coverage. Do not silently
shift timestamps or change conversion behavior. A structurally complete file
sequence is not proof that accumulation timing is scientifically resolved.

## Expected outputs and handoff

The converted files use `runoff_YYYYMMDD.nc` with `runoff(time,lat,lon)`.
The raw files use `original/ERA5-Land_runoff_YYYYMMDD.nc`. Data and run logs
remain local and ignored. `metadata/12_era5land_runoff.json` is the compact
machine-readable record of observed properties and Step 13 input settings.
The event-specific dataset is not added to the shared runoff registry because
that registry documents reusable products and the Rhine data are local,
experiment-specific inputs.

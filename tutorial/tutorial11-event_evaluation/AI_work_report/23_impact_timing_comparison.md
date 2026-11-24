# Step 23 — Final-Allocation Rerun Work Report

## Execution and scope

On 2026-11-24, reran the existing Step23 workflow at starting revision
`ef487584` after the maintainer requested updated impact allocations. Used
`metadata/21_impact_location_allocation.csv` final river_model cells; did not
rerun Step21 or the model. No input data, event times, allocation choice,
peak-search rule, interpolation or aggregation was changed.

```sh
bash s23-impact_timing_comparison.sh
MPLCONFIGDIR=/tmp/cmf-mpl-cache bash f23-impact_timing_comparison.sh
```

Inputs: Step01 timing ledger, final Step21 impact CSV, and
`experiment/Rhine2021/o_outflwRhine2021Jul.nc`. Before/after SHA-256 equality
was checked for all three. The model is float32 outflw(time,lat,lon),
744 × 32 × 40, m³/s; search interval July12 inclusive to July19 exclusive
contains 168 consecutive hourly labels. Time is interpreted as UTC under the
retained CF convention. Step23 now propagates direct/proxy basis and appends
the missing-downstream-area caveat to proxy rows; plot notes identify proxies.
These are presentation/provenance changes, not changes to peak calculations.

## Outputs and focused validation

- Timeseries CSV: 1,680 rows, 10 distinct final model cells × 168 hours.
- Comparison CSV: 22 report rows with all report/location IDs and source UTC
  timing fields retained; Eupen has no cell/series.
- Fig23a and Fig23b regenerated and visually inspected; proxy, water-level,
  unknown-timezone and missing-time distinctions remain visible.
- 23_handoff_status.json now marks outputs current for recorded input hashes;
  includes search bounds, method/status counts and output hashes.
- All saved timeseries values round-trip exactly to the original float32
  model values at the selected cells/times. Every saved peak timestamp/value
  agrees with an independent maximum from the extracted samples; all maxima
  lie inside the search window. Each selected cell equals the final Step21
  selector result.
- No lag is populated for water-level peaks or unknown/unavailable times.
  The three provisional Ahr offsets are +6 h (Müsch), +2 h (Altenahr) and
  −0.5 h (Bad Bodendorf), all at the same model cell. Source labels and
  model-cell support limit interpretation; the proxy is not the exact reach.

Step21 summary/prose now points to fingerprint-based Step23 currency rather
than a fixed stale message. Old research/development records remain historical;
current reports supersede the earlier 12-cell/2,016-sample results.

## Remaining limitations

No independent river/timing revalidation, model run, broader performance score
or solution of forcing-time/cold-start questions. Kordel/Prüm peak observations
are water-level references, not discharge-peak scores. The half-hour Ahr offset
does not imply sub-hourly model accuracy. Figures and CSVs are reusable only
with the recorded allocation/timing/model fingerprints. Research validator
retains the 22 pre-existing unrelated errors, with no new errors from this task.

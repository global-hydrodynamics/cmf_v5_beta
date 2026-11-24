# Step24 — Preliminary inundation downscaling

## Workflow Summary

- Inputs: Step03 S1A orbit038784 acquisition inventory/footprints, Step02 satellite
  analysis domain, Step14 Rhine2021 hourly flddph, matching Rhine15min/1min maps.
- Tasks: group the five scenes as one acquisition; use exact envelope midpoint;
  verify model time convention; select nearest CF time with no interpolation;
  run the maintained tributary-aware depth downscaler at 1 arcmin; inspect output.
- Outputs: one simulated-depth NetCDF under ignored `out/`, `metadata/24_downscaling_verification.json`,
  `figure/f24-inundation_1min.png`, Survey and Work reports.

Run `s24-downscale_inundation.sh`, then `f24-inundation_1min.sh`. The latter only
reads the completed result. Preserve model/map/observation inputs and Steps01–23.
Record exact acquisition/model times and difference, source/map provenance,
units/masks/coordinates/options, focused checks and preliminary limitations.
No other acquisition, satellite comparison, metrics, new algorithm, model run,
finer-resolution downscaling or Gallery publication. See the
[execution report](AI_work_report/24_inundation_downscaling.md) for reproducibility.

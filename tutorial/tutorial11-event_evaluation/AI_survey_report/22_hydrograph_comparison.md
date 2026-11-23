# Step 22 — Model–Observation Hydrograph Comparison

## Scope and evidence

The exploratory comparison uses Step 21 allocated cells for Lobith (153), Speyer (63), and Maxau (28), the Step 14 `outflw` output, and the supplied ECMWF observation CSV. The current comparison window is July 10–31, 2021, with an exclusive end at August 1 00:00. It contains 528 hourly model records per gauge and 88 six-hour observation labels per gauge.

![Figure 22 — Provisional Rhine hydrograph overlay](../figure/f22-hydrograph_comparison.png)

*Figure 22. Hourly model outflow at the Step 21 grid cells and provider-supplied six-hour mean observations shown at their source timestamp labels. Model outflow is m³/s. The observation unit and timezone are not declared, so the numerical and timing overlay is provisional; no conversion, resampling, or interpolation was applied.*

## Preliminary visual findings

| Station | Model maximum (UTC) | Observation maximum (source label) |
| --- | --- | --- |
| Lobith (153) | 8,490.1 m³/s at Jul 18 17:00 | 6,684.7 (unit unspecified) at Jul 18 06:00 |
| Speyer (63) | 6,465.5 m³/s at Jul 18 02:00 | 3,957.5 (unit unspecified) at Jul 18 06:00 |
| Maxau (28) | 6,473.4 m³/s at Jul 17 09:00 | 4,214.6 (unit unspecified) at Jul 17 18:00 |

The hydrographs show a rise toward mid-July followed by a longer recession in the modeled series. The listed maxima occur around July 17–18 rather than at the end of the expanded window. The numeric magnitudes can be read from the plot, but an amplitude agreement claim is not supported because the observation unit has not been confirmed. The model is sampled hourly and the observations every six hours; no averaging, interpolation or clock shift was applied.

## Time, units and limitations

The model file records `time` as seconds since `2021-07-01 00:00` and `outflw` in `m3/s`, with `cell_methods="time: mean"`. The time string is interpreted using the CF time-coordinate convention, under which an omitted timezone defaults to UTC; the model file itself has no global `Conventions` attribute. The observation CSV timestamps have no timezone suffix, and the observation dataset metadata has no discharge unit. See the [CF Conventions, Time Coordinate](https://cfconventions.org/Data/cf-conventions/cf-conventions-1.11/cf-conventions.html) specification. Provider correspondence describes the observations as six-hour mean values with interval-end labels, but the source file does not encode interval bounds or `cell_methods`.

The Figure therefore uses UTC model timestamps and unmodified observation labels on the same nominal date/time axis. It is suitable for exploratory shape inspection only. Resolve the observation unit and time basis, and assess the Step 14 cold-start and simulation/observation temporal support before calculating metrics or making a skill claim.

## Handoff

The separate model and observation records and their provenance are in [`22_hydrograph_timeseries.csv`](../metadata/22_hydrograph_timeseries.csv) and [`22_hydrograph_comparison_summary.json`](../metadata/22_hydrograph_comparison_summary.json). No temporal pairs or performance scores were generated. Formal time/variable matching and metric selection remain for a later evaluation step.

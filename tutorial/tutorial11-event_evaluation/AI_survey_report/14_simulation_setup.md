# Simulation Setup and Execution — Survey Report

## Purpose and experiment

The Step 14 Rhine 2021 run demonstrates that the regional map, the Tutorial's
ERA5-Land hourly runoff and the Step 13 regional Input Matrix can be used
together by the current CaMa-Flood v5 executable. The researcher-specified
experiment runs continuously from **2021-07-01 00:00 to 2021-07-21 00:00
(exclusive)**, for 480 hourly steps. It starts from the model's standard state
without a Restart or spin-up.

The run used the `Rhine_15min` 40 × 32 map, 20 daily NetCDF runoff files
(`runoff_20210701.nc`–`runoff_20210720.nc`), and the regional
`ERA5land_Rhine2021Jul` Input Matrix. Individual NetCDF map products, hourly
NetCDF model outputs, and an end-of-run NetCDF Restart were configured.

## Operational result

CaMa-Flood completed all 480 steps with exit status 0. The log confirms that
the selected regional river network, NetCDF map fields, bifurcation table, and
Step 13 Input Matrix were read. Eight output files were created, each with 480
time records and 32 × 40 map cells. The output time coordinate spans offsets
3,600 to 1,728,000 seconds from 2021-07-01 00:00, and the Restart was written
at 2021-07-21 00:00. The hourly outputs plus Restart total 6,665,927 bytes.

The runtime files are in the Git-ignored `experiment/Rhine2021/` directory.
Settings and per-file dimensions/sizes are catalogued in
[`metadata/14_simulation_setup.json`](../metadata/14_simulation_setup.json).

## Interpretation and limits

This confirms **operational execution and file production**, not model skill or
the accuracy of the runoff forcing. No spin-up was used, so initial-state
effects may influence river storage and flood evolution. KG-0019 remains open:
ERA5-Land accumulation time attribution and the converter's first-record and
period-boundary handling were not changed or scientifically validated here.
The successful run does not settle that timing question, establish adequacy of
the initial conditions, or support a flood-reconstruction score.

The next work can inspect and visualize the output fields, then define their
spatial and temporal correspondence with discharge and satellite observations
before quantitative evaluation.

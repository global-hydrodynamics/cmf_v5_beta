# Tutorial 11 Observation Data

This directory contains the event's observation inputs. Machine-readable
station and dataset descriptions are in
[`metadata/04_discharge_inventory.csv`](../metadata/04_discharge_inventory.csv)
and [`metadata/04_discharge_dataset.json`](../metadata/04_discharge_dataset.json).
For preparation steps and limitations see the [p04 workflow](../p04-discharge_observations.md),
[Survey Report](../AI_survey_report/04_discharge_observations.md) and
[Work Report](../AI_work_report/04_discharge_observations.md).

## Directory contents

- `stations_data/` — original, read-only discharge observations and station metadata supplied by ECMWF's Cinzia Mazzetti.
- `GFM_extent/` — the Tutorial's prepared satellite flood-classification observation products; see the [Step 3c/3d documentation](../p03c-gfm_classification.md) for their scope and limitations.

## Supplied discharge files

The three original files are retained in `stations_data/` without modification:

| File | Contents |
| --- | --- |
| `allstations.csv` | Station names, river/country, station coordinates and supplied `Cama*` allocation fields. |
| `Qobs_06_2021_st153_63_28.csv` | Time series with timestamp and station-ID columns. |
| `Qobs_06_2021_st153_63_28.nc` | NetCDF4 representation of the time series and station coordinate. |

The actual series contain station IDs **153 Lobith**, **63 Speyer**, and **28
Maxau**, all labelled as Rhine stations. Bonn/6 is absent; Speyer is not a
substitute for Bonn. Station metadata must be joined by station ID because its
row order differs from time-series column order.

The series has 1,460 timestamps at six-hour intervals, from `2021-01-01 06:00`
through `2022-01-01 00:00` as supplied. `allstations.csv` has 27 fields for
three stations; the discharge CSV has one timestamp plus three station-ID
columns, and the NetCDF stores `discharge(time, station)` with separate time
and station coordinates. The station coordinates have a longitude/latitude
form, but their datum/CRS is not declared. Provider correspondence describes the
values as six-hour mean discharge with interval-end timestamps; this convention
is not encoded by explicit time bounds in the files. The original time zone is
not declared. Discharge and area units are also not declared. The NetCDF has a
NaN fill value but the inspected series contains no missing values; no quality
flags are supplied. These limitations must remain visible in plots and later
matching.

The maintainer confirmed that these files may be shared and redistributed in
this Tutorial. No formal open-license identifier is embedded or inferred; the
original observing agency is not identified in the files.

## Reproduction

From this Tutorial directory, run `./s04-prepare_discharge.sh` to inspect the
original data and refresh the Step 4 metadata, and `./f04-observed_discharge.sh`
to regenerate the July hydrograph. The scripts do not modify the source files.

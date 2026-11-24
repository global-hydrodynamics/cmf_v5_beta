#!/usr/bin/env bash
# Extract hourly model and supplied observation series at Step 21 gauge cells.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TUTORIAL_DIR="$(CDPATH= cd "$SCRIPT_DIR/.." && pwd -P)"
REPO_ROOT="$(cd "$TUTORIAL_DIR/../.." && pwd)"
# User settings
# ----------------------------------------------------------------------
PYTHON="${PYTHON:-$REPO_ROOT/.venv/bin/python}" # Python executable; existing env override supported.
MODEL_NETCDF="$TUTORIAL_DIR/experiment/Rhine2021/o_outflwRhine2021Jul.nc" # Hourly outflw NetCDF input [m3/s].
OBSERVATION_CSV="$TUTORIAL_DIR/observation/stations_data/Qobs_06_2021_st153_63_28.csv" # Unmodified observation CSV; no assumed units/timezone.
ALLOCATION_CSV="$TUTORIAL_DIR/metadata/21_gauge_allocation.csv" # Authoritative Step21 station-to-cell handoff.
DATASET_JSON="$TUTORIAL_DIR/metadata/04_discharge_dataset.json" # Authoritative Step04 provenance and observation conventions.
OUTPUT_CSV="$TUTORIAL_DIR/metadata/22_hydrograph_timeseries.csv" # Separate model/observation series CSV destination.
SUMMARY_JSON="$TUTORIAL_DIR/metadata/22_hydrograph_comparison_summary.json" # Comparison summary JSON destination.
START="2021-07-10T00:00:00" # Inclusive start [ISO model UTC; observations retain nominal labels].
END_EXCLUSIVE="2021-08-01T00:00:00" # Exclusive end [ISO nominal axis]; no observation timezone conversion.
# ----------------------------------------------------------------------
# User settings end here.
# ----------------------------------------------------------------------

"$PYTHON" "$TUTORIAL_DIR/script/s22-extract_hydrograph.py" \
  --tutorial-dir "$TUTORIAL_DIR" \
  --model-netcdf "$MODEL_NETCDF" \
  --observation-csv "$OBSERVATION_CSV" \
  --allocation-csv "$ALLOCATION_CSV" \
  --dataset-json "$DATASET_JSON" \
  --output-csv "$OUTPUT_CSV" \
  --summary-json "$SUMMARY_JSON" \
  --start "$START" \
  --end-exclusive "$END_EXCLUSIVE"

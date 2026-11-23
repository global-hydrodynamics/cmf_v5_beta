#!/usr/bin/env bash
# Extract hourly model and supplied observation series at Step 21 gauge cells.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
PYTHON="${PYTHON:-$REPO_ROOT/.venv/bin/python}"
MODEL_NETCDF="$SCRIPT_DIR/experiment/Rhine2021-nextxy/o_outflwRhine2021Jul.nc"
OBSERVATION_CSV="$SCRIPT_DIR/observation/stations_data/Qobs_06_2021_st153_63_28.csv"
ALLOCATION_CSV="$SCRIPT_DIR/metadata/21_gauge_allocation.csv"
DATASET_JSON="$SCRIPT_DIR/metadata/04_discharge_dataset.json"
OUTPUT_CSV="$SCRIPT_DIR/metadata/22_hydrograph_timeseries.csv"
SUMMARY_JSON="$SCRIPT_DIR/metadata/22_hydrograph_comparison_summary.json"
START="2021-07-12T00:00:00"
END_EXCLUSIVE="2021-07-17T00:00:00"

"$PYTHON" "$SCRIPT_DIR/script/s22-extract_hydrograph.py" \
  --tutorial-dir "$SCRIPT_DIR" \
  --model-netcdf "$MODEL_NETCDF" \
  --observation-csv "$OBSERVATION_CSV" \
  --allocation-csv "$ALLOCATION_CSV" \
  --dataset-json "$DATASET_JSON" \
  --output-csv "$OUTPUT_CSV" \
  --summary-json "$SUMMARY_JSON" \
  --start "$START" \
  --end-exclusive "$END_EXCLUSIVE"

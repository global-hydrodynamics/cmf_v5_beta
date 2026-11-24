#!/usr/bin/env bash
# Extract report-linked model hydrographs and evaluate source-supported timings.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
PYTHON="${PYTHON:-$REPO_ROOT/.venv/bin/python}"
MODEL_NETCDF="$SCRIPT_DIR/experiment/Rhine2021/o_outflwRhine2021Jul.nc"
TIMING_CSV="$SCRIPT_DIR/metadata/01_reported_flood_timing.csv"
ALLOCATION_CSV="$SCRIPT_DIR/metadata/21_impact_location_allocation.csv"
TIMESERIES_CSV="$SCRIPT_DIR/metadata/23_impact_model_timeseries.csv"
COMPARISON_CSV="$SCRIPT_DIR/metadata/23_impact_timing_comparison.csv"
SEARCH_START="2021-07-12T00:00:00Z"
SEARCH_END_EXCLUSIVE="2021-07-19T00:00:00Z"

"$PYTHON" "$SCRIPT_DIR/script/s23-impact_timing_comparison.py" \
  --tutorial-dir "$SCRIPT_DIR" \
  --model-netcdf "$MODEL_NETCDF" \
  --timing-csv "$TIMING_CSV" \
  --allocation-csv "$ALLOCATION_CSV" \
  --timeseries-output "$TIMESERIES_CSV" \
  --comparison-output "$COMPARISON_CSV" \
  --search-start "$SEARCH_START" \
  --search-end-exclusive "$SEARCH_END_EXCLUSIVE"

#!/usr/bin/env bash
# Extract report-linked model hydrographs and evaluate source-supported timings.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
# User settings
# ----------------------------------------------------------------------
PYTHON="${PYTHON:-$REPO_ROOT/.venv/bin/python}" # Python executable; existing env override supported.
MODEL_NETCDF="$SCRIPT_DIR/experiment/Rhine2021/o_outflwRhine2021Jul.nc" # Hourly outflw NetCDF input [m3/s].
TIMING_CSV="$SCRIPT_DIR/metadata/01_reported_flood_timing.csv" # Authoritative Step01 reported UTC/source-time ledger.
ALLOCATION_CSV="$SCRIPT_DIR/metadata/21_impact_location_allocation.csv" # Authoritative final Step21 direct/proxy model cells.
TIMESERIES_CSV="$SCRIPT_DIR/metadata/23_impact_model_timeseries.csv" # Extracted hourly model-series CSV destination.
COMPARISON_CSV="$SCRIPT_DIR/metadata/23_impact_timing_comparison.csv" # Report-linked comparison CSV destination.
SEARCH_START="2021-07-12T00:00:00Z" # Inclusive model-maximum search start [ISO UTC].
SEARCH_END_EXCLUSIVE="2021-07-19T00:00:00Z" # Exclusive model-maximum search end [ISO UTC]; not Figure display bounds.
# ----------------------------------------------------------------------
# User settings end here.
# ----------------------------------------------------------------------

"$PYTHON" "$SCRIPT_DIR/script/s23-impact_timing_comparison.py" \
  --tutorial-dir "$SCRIPT_DIR" \
  --model-netcdf "$MODEL_NETCDF" \
  --timing-csv "$TIMING_CSV" \
  --allocation-csv "$ALLOCATION_CSV" \
  --timeseries-output "$TIMESERIES_CSV" \
  --comparison-output "$COMPARISON_CSV" \
  --search-start "$SEARCH_START" \
  --search-end-exclusive "$SEARCH_END_EXCLUSIVE"

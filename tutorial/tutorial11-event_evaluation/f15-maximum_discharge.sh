#!/usr/bin/env bash
# Generate Tutorial 11 Figures 15a and 15b from the retained Step 14 outputs.
set -euo pipefail
export MPLBACKEND=Agg

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# User settings.
PYTHON="${PYTHON:-$REPO_ROOT/.venv/bin/python}"
STEP14_METADATA="$SCRIPT_DIR/metadata/14_simulation_setup.json"
DOMAIN_METADATA="$SCRIPT_DIR/metadata/02_domain_selection.json"
MAP_DIR="$REPO_ROOT/map/Rhine_15min"
ANALYSIS_FILE="$SCRIPT_DIR/experiment/Rhine2021/analysis/maximum_discharge_20210701-20210801.nc"
FIGURE_DIR="$SCRIPT_DIR/figure"
REGIONAL_FIGURE="$FIGURE_DIR/f15a-maximum_discharge-regional.png"
AOI_FIGURE="$FIGURE_DIR/f15b-maximum_discharge-aoi.png"
COLOR_LEVELS="-1500,-1000,-300,-100,-30,-10,0,10,30,100,300,1000,3000,8000,15000"
LINTHRESH="10"
LINEAR_FRAC="0.10"
DPI=200

printf '\n[STEP 1/2] Compute signed local peaks from Step 14 hourly outputs.\n'
"$PYTHON" "$SCRIPT_DIR/script/f15-maximum_discharge.py" \
    --step14-metadata "$STEP14_METADATA" \
    --domain-metadata "$DOMAIN_METADATA" \
    --map-dir "$MAP_DIR" \
    --tutorial-dir "$SCRIPT_DIR" \
    --analysis-file "$ANALYSIS_FILE" \
    --regional-figure "$REGIONAL_FIGURE" \
    --aoi-figure "$AOI_FIGURE" \
    --color-levels="$COLOR_LEVELS" \
    --linthresh "$LINTHRESH" \
    --linear-frac "$LINEAR_FRAC" \
    --dpi "$DPI"

printf '\n[STEP 2/2] Figures generated from the retained run; CaMa-Flood was not rerun.\n'
printf '\n[SUCCESS] Created Tutorial 11 Figures 15a and 15b.\n'
printf 'Regional: %s\nAOI: %s\nAnalysis data: %s\n' \
    "$REGIONAL_FIGURE" "$AOI_FIGURE" "$ANALYSIS_FILE"

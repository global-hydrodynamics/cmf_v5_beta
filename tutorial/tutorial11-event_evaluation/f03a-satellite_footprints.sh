#!/usr/bin/env bash
set -euo pipefail

# User settings
PYTHON_CMD="python3"

TUTORIAL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ATLANTIS_DIR="$TUTORIAL_DIR/Atlantis"

if [[ ! -s "$TUTORIAL_DIR/metadata/03a_satellite_pass_inventory.csv" || \
      ! -s "$TUTORIAL_DIR/metadata/03a_satellite_orbit_metadata.csv" || \
      ! -s "$TUTORIAL_DIR/metadata/03a_sentinel1_acquisition_footprints.geojson" ]]; then
    printf 'Step 3a metadata is missing. Run bash s03a-satellite_availability.sh first.\n' >&2
    exit 1
fi

export MPLCONFIGDIR="$ATLANTIS_DIR/logs/matplotlib"
"$PYTHON_CMD" "$TUTORIAL_DIR/script/gfm_availability.py" \
    --mode figure \
    --domain-config "$TUTORIAL_DIR/metadata/02_domain_selection.json" \
    --catalogue-root "$ATLANTIS_DIR/catalogue" \
    --inventory-output "$TUTORIAL_DIR/metadata/03a_satellite_pass_inventory.csv" \
    --orbit-metadata "$TUTORIAL_DIR/metadata/03a_satellite_orbit_metadata.csv" \
    --acquisition-footprints "$TUTORIAL_DIR/metadata/03a_sentinel1_acquisition_footprints.geojson" \
    --map-dir "$(cd "$TUTORIAL_DIR/../.." && pwd)/map/glb_15min" \
    --tile-cache "$HOME/.cache/cmf_flood_osm_tiles" \
    --figure-dir "$TUTORIAL_DIR/figure"

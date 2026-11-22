#!/usr/bin/env bash
set -euo pipefail

# User settings
PYTHON_CMD="${PYTHON_CMD:-python3}"
WORKERS=2
DOWNLOAD_OFFLINE="${DOWNLOAD_OFFLINE:-0}"
REUSE_DATA_DIR="${REUSE_DATA_DIR:-$HOME/work/Atlantis/data/Rhine_2021_3sec}"

TUTORIAL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ATLANTIS_DIR="$TUTORIAL_DIR/Atlantis"
SELECTION_JSON="$TUTORIAL_DIR/metadata/03a_selected_passes.json"
DOMAIN_CONFIG="$TUTORIAL_DIR/metadata/02_domain_selection.json"
DOWNLOAD_ARGS=(
    --selection-json "$SELECTION_JSON"
    --domain-config "$DOMAIN_CONFIG"
    --catalogue-root "$ATLANTIS_DIR/catalogue"
    --run-root "$ATLANTIS_DIR/runs"
    --reuse-data-dir "$REUSE_DATA_DIR"
    --workers "$WORKERS"
)

if [[ "$DOWNLOAD_OFFLINE" == "1" ]]; then
    DOWNLOAD_ARGS+=(--offline)
fi

echo "Read selected pass(es), date(s), layers and analysis bbox from metadata JSON."
echo "Save native GFM COGs and run logs under $ATLANTIS_DIR."
DOWNLOAD_STATUS=0
if "$PYTHON_CMD" "$TUTORIAL_DIR/script/event_gfm_download.py" "${DOWNLOAD_ARGS[@]}"; then
    DOWNLOAD_STATUS=0
else
    DOWNLOAD_STATUS=$?
fi

MANIFEST_STATUS=0
if "$PYTHON_CMD" -B "$TUTORIAL_DIR/script/s03b-build_download_manifest.py" \
    --selection-json "$SELECTION_JSON" \
    --catalogue-root "$ATLANTIS_DIR/catalogue" \
    --atlantis-root "$ATLANTIS_DIR"; then
    MANIFEST_STATUS=0
else
    MANIFEST_STATUS=$?
fi

if (( DOWNLOAD_STATUS != 0 )); then
    exit "$DOWNLOAD_STATUS"
fi
if (( MANIFEST_STATUS != 0 )); then
    exit "$MANIFEST_STATUS"
fi

echo "Native GFM acquisition and p03c handover complete. No reprojection, mosaic conversion or classification was run."

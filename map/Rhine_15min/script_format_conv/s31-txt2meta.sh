#!/bin/sh
# Convert legacy map TXT metadata to standard v5 Namelist/CSV metadata.
set -eu

if [ "$#" -ne 0 ]; then
    echo "Usage: ./s31-txt2meta.sh" >&2
    exit 2
fi

# CaMa-Flood general setting (check CMF root, import CMF common shell functions)
PYTHON_CMD="python3"
: "${CMF_V50_ROOT:?CMF_V50_ROOT is not set. Run s00-configure_cama_root.sh first.}"
. "$CMF_V50_ROOT/tools/cmf_shell_functions.sh"

CODE_DIR="$CMF_V50_ROOT/map/tools/code"

cmf_check_init "Convert legacy map TXT metadata to standard formats"

cmf_check_step 1 1 "Validate and convert metadata in the parent map directory"
"$PYTHON_CMD" "$CODE_DIR/convert_map_metadata.py" txt2meta ..

cmf_check_success

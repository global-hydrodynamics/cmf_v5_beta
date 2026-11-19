#!/bin/bash
# Import additional data into this development checkout as editable local files.
set -eu
SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd -P)
exec python3 "$SCRIPT_DIR/package_data.py" install "$@"

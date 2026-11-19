#!/bin/bash
# Compare authoritative additional data with local data without changing either.
set -eu
SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd -P)
exec python3 "$SCRIPT_DIR/package_data.py" diff "$@"

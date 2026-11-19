#!/usr/bin/env bash
# Assemble an existing clean source tree and catalog-selected additional data.
set -euo pipefail

# ============================================================
# User settings
# ============================================================

VER="v5b01_20261119"

# Relative to the package/ directory; absolute paths are also permitted.
PACKAGE_DATA_DIR="../../cmf_v5_package_data"

# ============================================================
# User settings end here
# ============================================================

# CDPATH= prevents shell search settings from changing the script-directory base.
SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd -P)
# Dry-run must not create import bytecode caches.
export PYTHONDONTWRITEBYTECODE=1
exec python3 "$SCRIPT_DIR/make_package.py" --version "$VER" --package-data "$PACKAGE_DATA_DIR" "$@"

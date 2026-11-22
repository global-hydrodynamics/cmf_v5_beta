#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TUTORIAL_DIR="$SCRIPT_DIR"
if [[ -z "${PYTHON:-}" ]]; then
  PYTHON="$SCRIPT_DIR/../../.venv/bin/python"
  if [[ ! -x "$PYTHON" ]]; then
    PYTHON="python3"
  fi
fi

"$PYTHON" "$TUTORIAL_DIR/script/s04-inspect_discharge.py" --tutorial-dir "$TUTORIAL_DIR"

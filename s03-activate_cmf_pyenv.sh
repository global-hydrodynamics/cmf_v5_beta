#!/usr/bin/env bash
# Register the cmfpy alias in the user's interactive Bash or Zsh configuration.
set -eu

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
VENV_ACTIVATE="$SCRIPT_DIR/.venv/bin/activate"

manual_activation() {
    printf '\nManual activation command:\n\n    source %q\n' "$VENV_ACTIVATE" >&2
}

if [[ ! -f "$VENV_ACTIVATE" ]]; then
    printf '[ERROR] Repository-local Python environment was not found: %s\n' "$SCRIPT_DIR/.venv" >&2
    printf 'Run ./s02-python_setup.sh first.\n' >&2
    exit 1
fi

if [[ -z "${HOME:-}" ]]; then
    printf '[ERROR] HOME is not set; cannot select a shell configuration file.\n' >&2
    manual_activation
    exit 1
fi

LOGIN_SHELL="${SHELL:-}"
if [[ -z "$LOGIN_SHELL" ]]; then
    case "$(uname -s 2>/dev/null || true)" in
        Darwin)
            LOGIN_SHELL="$(dscl . -read "/Users/${USER:-$(id -un)}" UserShell 2>/dev/null | awk '{print $2}' || true)"
            ;;
        *)
            LOGIN_SHELL="$(getent passwd "${USER:-$(id -un)}" 2>/dev/null | awk -F: '{print $7}' || true)"
            ;;
    esac
fi

case "${LOGIN_SHELL##*/}" in
    zsh)
        CONFIG_FILE="${HOME:?HOME is not set}/.zshrc"
        CONFIG_DISPLAY="~/.zshrc"
        ;;
    bash)
        if [[ "$(uname -s 2>/dev/null || true)" == "Darwin" ]]; then
            # Preserve whichever login startup file Bash already reads first.
            CONFIG_FILE="${HOME}/.bash_profile"
            CONFIG_DISPLAY="~/.bash_profile"
            for startup_file in .bash_profile .bash_login .profile; do
                if [[ -f "$HOME/$startup_file" ]]; then
                    CONFIG_FILE="$HOME/$startup_file"
                    CONFIG_DISPLAY="~/$startup_file"
                    break
                fi
            done
        else
            CONFIG_FILE="${HOME:?HOME is not set}/.bashrc"
            CONFIG_DISPLAY="~/.bashrc"
        fi
        ;;
    *)
        printf '[ERROR] Login shell must be Bash or Zsh; detected: %s\n' "${LOGIN_SHELL:-unknown}" >&2
        manual_activation
        exit 1
        ;;
esac

if ! command -v python3 >/dev/null 2>&1; then
    printf '[ERROR] python3 is required to safely update the shell configuration.\n' >&2
    manual_activation
    exit 1
fi

printf 'Login shell: %s\n' "${LOGIN_SHELL##*/}"
printf 'Shell configuration: %s\n' "$CONFIG_DISPLAY"

if REGISTRATION_STATUS_TEXT=$(python3 - "$CONFIG_FILE" "$VENV_ACTIVATE" <<'PY'
import os
import re
import stat
import sys
import tempfile
from pathlib import Path

config_path = Path(sys.argv[1])
activate_path = os.path.abspath(sys.argv[2])
start_marker = "# >>> CaMa-Flood v5 Python environment >>>"
end_marker = "# <<< CaMa-Flood v5 Python environment <<<"
legacy_marker = "# CaMa-Flood v5 Python environment"
alias_pattern = re.compile(
    r"^\s*(?:alias(?:\s+-[A-Za-z]+)*\s+cmfpy(?:\s*=|\s|$)|"
    r"function\s+cmfpy(?:\s|\(|$)|cmfpy\s*\(\s*\))"
)


def shell_quote(value: str) -> str:
    return "'" + value.replace("'", "'\\''") + "'"


def fail(message: str, status: int) -> None:
    print(message, file=sys.stderr)
    raise SystemExit(status)


try:
    resolved_config = config_path.resolve()
    if resolved_config.exists():
        with resolved_config.open("r", encoding="utf-8", errors="surrogateescape", newline="") as stream:
            original = stream.read()
        mode = stat.S_IMODE(resolved_config.stat().st_mode)
    else:
        original = ""
        mode = 0o600
except OSError as error:
    fail(f"[ERROR] Cannot read shell configuration: {error}", 3)

newline = "\r\n" if "\r\n" in original else "\n"
body = (
    f"{start_marker}{newline}"
    f"# Activates the repository-local .venv.{newline}"
    f"alias cmfpy={shell_quote('source ' + shell_quote(activate_path))}{newline}"
    f"{end_marker}{newline}"
)
lines = original.splitlines(keepends=True)
start_indexes = [i for i, line in enumerate(lines) if line.rstrip("\r\n") == start_marker]
end_indexes = [i for i, line in enumerate(lines) if line.rstrip("\r\n") == end_marker]

if len(start_indexes) != len(end_indexes) or len(start_indexes) > 1:
    fail("[ERROR] Shell configuration contains incomplete or duplicate CaMa-Flood alias markers; no changes were made.", 3)

managed_range = None
if start_indexes:
    start = start_indexes[0]
    end = end_indexes[0]
    if end <= start:
        fail("[ERROR] Shell configuration has reversed CaMa-Flood alias markers; no changes were made.", 3)
    managed_range = (start, end)

unmanaged_aliases = []
for index, line in enumerate(lines):
    if not alias_pattern.match(line):
        continue
    if managed_range and managed_range[0] < index < managed_range[1]:
        continue
    if index > 0 and lines[index - 1].rstrip("\r\n") == legacy_marker:
        if index - 1 == 0 or lines[index - 2].rstrip("\r\n") not in (start_marker,):
            managed_range = (index - 1, index)
            continue
    unmanaged_aliases.append(index)

if unmanaged_aliases:
    fail("[CONFLICT] An unrelated cmfpy alias or function already exists in this shell configuration; it was preserved.", 2)

if managed_range:
    start, end = managed_range
    updated_lines = lines[:start] + [body] + lines[end + 1 :]
    updated = "".join(updated_lines)
else:
    updated = original
    if updated and not updated.endswith(("\n", "\r")):
        updated += newline
    if updated and not updated.endswith(newline * 2):
        updated += newline
    updated += body

if updated == original:
    print("already")
    raise SystemExit(0)

try:
    resolved_config.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary_name = tempfile.mkstemp(prefix=f".{resolved_config.name}.", dir=resolved_config.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", errors="surrogateescape", newline="") as stream:
            stream.write(updated)
        os.chmod(temporary_name, mode)
        os.replace(temporary_name, resolved_config)
    except BaseException:
        try:
            os.unlink(temporary_name)
        except OSError:
            pass
        raise
except OSError as error:
    fail(f"[ERROR] Cannot update shell configuration: {error}", 3)

print("registered")
PY
); then
    case "$REGISTRATION_STATUS_TEXT" in
        registered)
            printf '[OK] cmfpy alias registered in %s.\n' "$CONFIG_DISPLAY"
            ;;
        already)
            printf '[OK] cmfpy alias is already registered in %s.\n' "$CONFIG_DISPLAY"
            ;;
        *)
            printf '[ERROR] Alias registration returned an unexpected result.\n' >&2
            manual_activation
            exit 3
            ;;
    esac
else
    REGISTRATION_ERROR=$?
    if [[ "$REGISTRATION_ERROR" -eq 2 ]]; then
        printf '\n[ERROR] Alias registration was not changed because of the conflict above.\n' >&2
    else
        printf '\n[ERROR] Alias registration failed; no successful registration is claimed.\n' >&2
    fi
    manual_activation
    exit "$REGISTRATION_ERROR"
fi

printf '\n==================================================\n'
printf 'CaMa-Flood Python Environment\n'
printf '==================================================\n\n'
printf '[OK] Python environment: cmf50\n'
printf '[OK] Activation alias: cmfpy\n'
printf '[OK] Registered in: %s\n\n' "$CONFIG_DISPLAY"
printf 'To activate the environment:\n\n    cmfpy\n\n'
printf 'Your prompt will change to:\n\n    (cmf50) $\n\n'
printf 'To deactivate:\n\n    deactivate\n\n'
printf 'Open a new terminal, or reload your shell configuration\nbefore using the alias.\n'
printf '==================================================\n'

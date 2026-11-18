#!/bin/sh
# Called by the Windows wrapper with already converted Linux paths.
set -eu
app_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
repo_dir=$(CDPATH= cd -- "$app_dir/../.." && pwd)
map_dir=$1
explicit_python=$2
windows_powershell=$3
probe='import sys; assert sys.platform == "linux" and sys.version_info >= (3,10), "Requires Linux Python >=3.10"'
if [ "$explicit_python" != '-' ]; then
    if ! "$explicit_python" -c "$probe"; then
        echo '[ERROR] CMF_WSL_PYTHON must name a working Linux Python >=3.10.' >&2
        exit 1
    fi
    exec "$explicit_python" "$app_dir/code/launch_desktop.py" "$map_dir" --windows-browser "$windows_powershell" --no-setup
fi
# Probe executability/platform: a macOS or Windows .venv is never reused.
for candidate in "$repo_dir/.venv/bin/python" "$app_dir/.venv/bin/python" python3; do
    if "$candidate" -c "$probe" >/dev/null 2>&1; then
        exec "$candidate" "$app_dir/code/launch_desktop.py" "$map_dir" --windows-browser "$windows_powershell" --no-setup
    fi
done
echo '[ERROR] No Linux Python >=3.10. Install Python in WSL or set CMF_WSL_PYTHON; see README.' >&2
exit 1

"""Choose a map and start the local GUI from a desktop launcher."""
from __future__ import annotations

import argparse
import importlib.util
from pathlib import Path
import socket
import sys


def choose_map(default):
    """Use the system folder dialog when Tk is available; retain a console fallback."""
    try:
        import tkinter as tk
        from tkinter import filedialog
        window = tk.Tk()
        window.withdraw()
        try:
            folder = filedialog.askdirectory(
                title="CaMa-Flood: select a map folder containing params.txt",
                initialdir=str(default if default.is_dir() else default.parent),
                mustexist=True,
            )
        finally:
            window.destroy()
        return Path(folder) if folder else None
    except (ImportError, RuntimeError) as exc:
        print(f"Folder dialog unavailable: {exc}")
    except Exception as exc:
        # TclError can occur on a machine without a desktop/Tk runtime.
        # Do not hide other application errors: this fallback covers only dialog setup.
        if type(exc).__name__ != "TclError":
            raise
        print(f"Folder dialog unavailable: {exc}")
    print(f"Default map: {default}")
    value = input("Map folder path (Enter = default; q = cancel): ").strip()
    if value.lower() == "q":
        return None
    return Path(value.strip('"')) if value else default


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("map_dir", nargs="?", type=Path,
                        help="Optional map path; otherwise choose a folder")
    parser.add_argument("--port", type=int, default=0,
                        help="Local port; 0 chooses an available port")
    parser.add_argument("--no-browser", action="store_true")
    args = parser.parse_args()
    directory = Path(__file__).resolve().parent
    missing = [name for name in ("numpy", "netCDF4", "matplotlib", "panel", "bokeh")
               if importlib.util.find_spec(name) is None]
    if missing:
        print("Missing dependencies: " + ", ".join(missing), file=sys.stderr)
        print(f"Python: {sys.executable}\nSee installation steps in {directory / 'README.md'}", file=sys.stderr)
        return 1
    selected = args.map_dir or choose_map(directory.parents[1]/"map"/"mekong_15min")
    if selected is None:
        print("Launch cancelled.")
        return 0
    selected = selected.expanduser().resolve()
    if not (selected/"params.txt").is_file():
        print(f"Not a CaMa-Flood map folder (params.txt missing): {selected}", file=sys.stderr)
        return 2
    if not 0 <= args.port <= 65535:
        print("Port must be between 0 and 65535.", file=sys.stderr)
        return 2
    port = args.port
    if not port:
        # The server is loopback-only. There is a small bind race after release;
        # if another process takes this port, report the startup error normally.
        with socket.socket() as listener:
            listener.bind(("127.0.0.1", 0))
            port = listener.getsockname()[1]
    sys.argv = [str(directory/"app.py"), str(selected), "--port", str(port)]
    if args.no_browser:
        sys.argv.append("--no-browser")
    print("Keep this terminal open while using Map Explorer. Ctrl-C stops it.", flush=True)
    from app import main as run_app
    run_app()
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        print("\nMap Explorer stopped.")

"""Start the bundled Mekong map or an explicit map in the local desktop GUI."""
from __future__ import annotations

import argparse
import importlib.util
from pathlib import Path
import socket
import subprocess
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


def prepare_environment(directory, argv, missing):
    """Install only after explicit terminal consent, in the Explorer-local venv.

    Keep Conda, system Python and the repository's shared environment unchanged.
    Re-launch with the original arguments so folder selection/server startup use
    the newly installed runtime rather than this process's import state.
    """
    environment = directory / ".venv"
    python = environment / ("Scripts/python.exe" if sys.platform == "win32" else "bin/python")
    print("Missing dependencies: " + ", ".join(missing), file=sys.stderr)
    print(f"Selected Python: {sys.executable}", file=sys.stderr)
    print(f"Explorer environment to create/update: {environment}", flush=True)
    print("Required packages will be downloaded and installed there; other environments are unchanged.", flush=True)
    if not sys.stdin.isatty():
        print(f"[INFO] No interactive terminal; no changes made. See {directory / 'README.md'}", file=sys.stderr)
        return 1
    try:
        answer = input("Prepare this environment and launch Map Explorer? [y/N] ").strip().lower()
    except EOFError:
        answer = ""
    if answer not in ("y", "yes"):
        print("[INFO] Setup cancelled; no environment changes made.")
        return 0

    try:
        if environment.is_symlink():
            raise OSError(f"Refusing to install into a linked environment: {environment}")
        if not python.is_file() or not (environment / "pyvenv.cfg").is_file():
            print(f"[STEP] Creating {environment}", flush=True)
            subprocess.run([sys.executable, "-m", "venv", str(environment)], check=True)
        # A stale or malformed .venv must not redirect pip into Conda/system Python.
        subprocess.run([str(python), "-c",
                        "import sys; from pathlib import Path; "
                        "assert sys.prefix != sys.base_prefix and "
                        "Path(sys.prefix).resolve() == Path(sys.argv[1]).resolve(), 'Not the requested isolated venv'",
                        str(environment)], check=True)
        print("[STEP] Installing Map Explorer requirements", flush=True)
        subprocess.run([str(python), "-m", "pip", "install", "-r", str(directory / "requirements.txt")], check=True)
        subprocess.run([str(python), "-c", "import numpy, netCDF4, matplotlib, panel, bokeh"], check=True)
    except (OSError, subprocess.CalledProcessError) as exc:
        print(f"[ERROR] Environment setup failed: {exc}", file=sys.stderr)
        print("Existing data and other environments were not changed. Re-run the launcher to retry.", file=sys.stderr)
        return 1
    print("[SUCCESS] Explorer environment ready; launching.", flush=True)
    return subprocess.run([str(python), str(directory / "launch_desktop.py"), *argv]).returncode


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("map_dir", nargs="?", type=Path,
                        help="Optional map path; default: bundled Mekong (no folder dialog)")
    parser.add_argument("--port", type=int, default=0,
                        help="Local port; 0 chooses an available port")
    parser.add_argument("--no-browser", action="store_true")
    parser.add_argument("--no-setup", action="store_true", help="Report missing packages without installation")
    parser.add_argument("--windows-browser", type=Path, help="WSL Windows PowerShell executable for browser interop")
    argv = sys.argv[1:] if argv is None else argv
    args = parser.parse_args(argv)
    directory = Path(__file__).resolve().parent
    missing = [name for name in ("numpy", "netCDF4", "matplotlib", "panel", "bokeh")
               if importlib.util.find_spec(name) is None]
    if missing and args.no_setup:
        print("[ERROR] Missing WSL Python packages: " + ", ".join(missing), file=sys.stderr)
        print("Create a Linux venv and install requirements manually; see README Windows Launcher (WSL).", file=sys.stderr)
        return 1
    if missing:
        return prepare_environment(directory, argv, missing)
    from map_datasets import resolve_map
    selected = resolve_map(args.map_dir)
    if selected is None:
        print("Launch cancelled.")
        return 0
    if not (selected/"params.txt").is_file():
        print(f"Not a CaMa-Flood map folder (params.txt missing): {selected}", file=sys.stderr)
        return 2
    if not 0 <= args.port <= 65535:
        print("Port must be between 0 and 65535.", file=sys.stderr)
        return 2
    port = args.port
    if port:
        try:
            with socket.socket() as listener:
                listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                listener.bind(("127.0.0.1", port))
        except OSError as exc:
            print(f"[ERROR] Port {port} unavailable: {exc}. Choose another port; no process was stopped.", file=sys.stderr)
            return 2
    if not port:
        # The server is loopback-only. There is a small bind race after release;
        # if another process takes this port, report the startup error normally.
        with socket.socket() as listener:
            listener.bind(("127.0.0.1", 0))
            port = listener.getsockname()[1]
    sys.argv = [str(directory/"app.py"), str(selected), "--port", str(port)]
    if args.windows_browser:
        from map_reader import Geometry
        try:
            Geometry.read(selected / "params.txt")
        except ValueError as exc:
            print(f"[ERROR] Invalid map: {exc}", file=sys.stderr)
            return 2
    if args.no_browser or args.windows_browser:
        sys.argv.append("--no-browser")
    print("Keep this terminal open while using Map Explorer. Ctrl-C stops it.", flush=True)
    from app import main as run_app
    browser = None
    if args.windows_browser and not args.no_browser:
        from wsl_browser import start_browser
        browser = start_browser(args.windows_browser, port)
    try:
        run_app()
    finally:
        if browser is not None:
            browser[0].set()
            browser[1].join(timeout=1)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        print("\nMap Explorer stopped.")

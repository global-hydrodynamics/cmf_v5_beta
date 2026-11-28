"""Start the bundled Mekong map or an explicit map in the local desktop GUI."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
from pathlib import Path
import shutil
import socket
import subprocess
import sys
import tempfile


def choose_map(default):
    """Use the system folder dialog when Tk is available; retain a console fallback."""
    try:
        import tkinter as tk
        from tkinter import filedialog
        window = tk.Tk()
        window.withdraw()
        try:
            folder = filedialog.askdirectory(
                title="CaMa-Flood: select a map folder containing params.nml",
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


PROFILES = ("standard", "2024", "2022")
PROFILE_PYTHON = {
    "standard": ((3, 10), (3, 13)),
    "2024": ((3, 10), (3, 12)),
    "2022": ((3, 10), (3, 10)),
}
PACKAGE_IMPORTS = """
import sys
assert sys.version_info >= (3, 10), 'Map Explorer requires Python 3.10 or later'
import numpy, netCDF4, matplotlib, panel, bokeh, rasterio, param
from PIL import Image
from bokeh.document import Document
panel.extension()
root = panel.pane.Markdown('Map Explorer dependency check').get_root(Document())
assert root is not None
import app
"""
APP_INITIALIZATION = PACKAGE_IMPORTS + """
import sys
assert sys.version_info >= (3, 10), 'Map Explorer requires Python 3.10 or later'
import tempfile
from pathlib import Path
import numpy as np
from app import Explorer
with tempfile.TemporaryDirectory(prefix='cmf-explorer-check-') as temporary:
    root = Path(temporary)
    map_dir = root / 'map'
    map_dir.mkdir()
    (map_dir / 'params.txt').write_text('4 NX\\n3 NY\\n1 NLFP\\n1 spacing\\n10 west\\n14 east\\n20 south\\n23 north\\n')
    np.arange(1, 13, dtype='<f4').tofile(map_dir / 'uparea.bin')
    explorer = Explorer(map_dir, output_dir=root / 'output')
    try:
        assert explorer.reader.sources
        assert explorer.layer is not None
    finally:
        explorer.close()
"""


def macos_setup_error(info):
    """Return a diagnostic for interpreter/OS combinations without supported wheels."""
    version = info["macos"]
    try:
        major = int(version.split(".")[0])
    except ValueError:
        major = 0
    python = tuple(info["python"][:2])
    if (info["implementation"] != "CPython" or
            not (3, 10) <= python <= (3, 13) or
            major < 11 or info["machine"] not in ("arm64", "x86_64")):
        return ("Automatic macOS setup requires CPython 3.10–3.13 on macOS 11+ "
                "(arm64 or x86_64). Install a matching Python from python.org, "
                "then retry. Homebrew/GDAL are not required. "
                "The selected interpreter determines the wheel architecture.")
    if major < 14 and python >= (3, 13):
        return ("macOS 11–13 automatic setup requires CPython 3.10–3.12; "
                "CPython 3.13 needs macOS 14+ dependency wheels. "
                "Install Python 3.12 from python.org and retry; no GDAL installation is needed.")
    return None


def setup_environment(environment, macos):
    """Isolate package installation from ambient Python and pip target overrides."""
    env = {key: value for key, value in os.environ.items()
           if key not in ("PYTHONPATH", "PYTHONHOME", "PYTHONUSERBASE",
                          "PIP_TARGET", "PIP_PREFIX", "PIP_USER", "VIRTUAL_ENV")}
    if macos:
        env = {key: value for key, value in env.items() if not key.startswith("PIP_")}
        env["PIP_CONFIG_FILE"] = os.devnull
    env["VIRTUAL_ENV"] = str(environment)
    return env


def platform_environment_tag():
    if sys.platform == "darwin":
        return "macos"
    if sys.platform == "win32":
        return "windows"
    if sys.platform.startswith("linux"):
        release = Path("/proc/sys/kernel/osrelease")
        is_wsl = "WSL_DISTRO_NAME" in os.environ or (
            release.is_file() and "microsoft" in release.read_text(errors="ignore").lower()
        )
        return "wsl" if is_wsl else "linux"
    return sys.platform.replace("/", "-")


def environment_root(directory):
    """Keep WSL venvs on the Linux filesystem, distinct from Windows and macOS."""
    if platform_environment_tag() == "wsl":
        identity = hashlib.sha256(str(directory.resolve()).encode()).hexdigest()[:16]
        return Path.home() / ".cache" / "cmf-map-explorer" / identity
    return directory


def profile_environment(directory, profile):
    return environment_root(directory) / f".venv-{platform_environment_tag()}-{profile}"


def python_candidates():
    """Return safe interpreter command candidates, preferring the selected runtime."""
    commands = [[sys.executable]]
    if sys.platform == "win32":
        launcher = shutil.which("py")
        if launcher:
            commands.extend([[launcher, f"-3.{minor}"] for minor in (13, 12, 11, 10)])
    else:
        commands.extend([[path] for name in ("python3.13", "python3.12", "python3.11", "python3.10")
                         if (path := shutil.which(name))])

    found = []
    seen = set()
    probe = ("import json,platform,sys; "
             "print(json.dumps({'python':list(sys.version_info[:3]),"
             "'implementation':platform.python_implementation(),"
             "'macos':platform.mac_ver()[0],'machine':platform.machine()}))")
    for command in commands:
        try:
            result = subprocess.run(command + ["-c", probe], check=True, capture_output=True,
                                    text=True, timeout=10)
            info = json.loads(result.stdout.strip().splitlines()[-1])
        except (OSError, subprocess.SubprocessError, ValueError, IndexError):
            continue
        key = (tuple(info["python"][:2]), info["implementation"], info["machine"])
        if key not in seen:
            seen.add(key)
            found.append((command, info))
    return found


def profile_compatible(profile, info):
    low, high = PROFILE_PYTHON[profile]
    version = tuple(info["python"][:2])
    return info["implementation"] == "CPython" and low <= version <= high


def requirements_for(directory, profile, macos):
    if profile == "standard":
        return directory / ("requirements-macos.txt" if macos else "requirements.txt")
    return directory / "config" / f"requirements_{profile}.txt"


def validate_environment(python, code_dir, expected_prefix=None, *, initialize_app=False, env=None):
    """Check pip consistency, compiled imports, Panel/Bokeh model creation and optional app init."""
    options = {"capture_output": True, "text": True, "timeout": 180}
    if env is not None:
        options["env"] = env
    if expected_prefix is not None:
        prefix_check = subprocess.run(
            [str(python), "-c",
             "import sys; from pathlib import Path; "
             "assert sys.prefix != sys.base_prefix and "
             "Path(sys.prefix).resolve() == Path(sys.argv[1]).resolve(), 'Not the requested isolated venv'",
             str(expected_prefix)], **options)
        if prefix_check.returncode:
            return False, prefix_check.stderr.strip() or prefix_check.stdout.strip() or "venv isolation check failed"
    checked = subprocess.run([str(python), "-m", "pip", "check"], **options)
    if checked.returncode:
        return False, checked.stdout.strip() or checked.stderr.strip() or "pip check failed"
    script = APP_INITIALIZATION if initialize_app else PACKAGE_IMPORTS
    smoke = subprocess.run([str(python), "-c", script], cwd=code_dir, **options)
    if smoke.returncode:
        return False, smoke.stderr.strip() or smoke.stdout.strip() or "GUI/API initialization failed"
    return True, "pip check, compiled imports and Panel/Bokeh APIs passed" + (
        "; bundled-map app initialization passed" if initialize_app else ""
    )


def short_diagnostic(result):
    text = (result.stderr or "") + "\n" + (result.stdout or "")
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    return " | ".join(lines[-6:]) or f"process exited with status {result.returncode}"


def network_failure(result):
    text = ((result.stderr or "") + "\n" + (result.stdout or "")).lower()
    return any(term in text for term in (
        "temporary failure in name resolution", "name or service not known", "connection refused",
        "connection reset", "network is unreachable", "connection timed out", "read timed out",
        "ssl: certificate_verify_failed", "no space left on device", "permission denied",
    ))


def build_profile(directory, profile, interpreter):
    """Build, validate, and adopt one profile without editing another venv."""
    command, python_info = interpreter
    macos = sys.platform == "darwin"
    if not profile_compatible(profile, python_info):
        return None, f"Python {'.'.join(map(str, python_info['python'][:2]))} is incompatible with {profile}", False
    if macos and (error := macos_setup_error(python_info)):
        return None, error, False

    root = environment_root(directory)
    target = profile_environment(directory, profile)
    if target.is_symlink():
        return None, f"Refusing linked profile environment: {target}", True
    try:
        root.mkdir(parents=True, exist_ok=True)
        work = Path(tempfile.mkdtemp(prefix=f".map-explorer-{profile}-", dir=root))
    except OSError as exc:
        return None, f"Cannot create isolated environment staging directory: {exc}", True
    candidate = work / "venv"
    python = candidate / ("Scripts/python.exe" if sys.platform == "win32" else "bin/python")
    env = setup_environment(candidate, macos)
    print(f"[TRY] {profile.capitalize()} requirements with Python {'.'.join(map(str, python_info['python'][:3]))}", flush=True)
    try:
        created = subprocess.run(command + ["-m", "venv", str(candidate)], capture_output=True, text=True,
                                 timeout=180, env=env)
        if created.returncode:
            return None, short_diagnostic(created), True
        install = [str(python), "-m", "pip", "install", "--no-user"]
        if macos:
            install.append("--only-binary=:all:")
        install += ["-r", str(requirements_for(directory, profile, macos))]
        installed = subprocess.run(install, capture_output=True, text=True, timeout=1800, env=env)
        if installed.returncode:
            return None, short_diagnostic(installed), network_failure(installed)
        valid, reason = validate_environment(python, directory / "code", candidate,
                                             initialize_app=True, env=env)
        if not valid:
            return None, reason, False

        backup = None
        if target.exists():
            from datetime import datetime
            backup = target.with_name(target.name + ".previous-" + datetime.now().strftime("%Y%m%d-%H%M%S"))
            os.replace(target, backup)
        try:
            os.replace(candidate, target)
            target_python = target / ("Scripts/python.exe" if sys.platform == "win32" else "bin/python")
            final_env = setup_environment(target, macos)
            valid, reason = validate_environment(target_python, directory / "code", target,
                                                 initialize_app=True, env=final_env)
            if not valid:
                raise RuntimeError(f"adopted environment validation failed: {reason}")
        except Exception:
            if target.exists():
                shutil.rmtree(target, ignore_errors=True)
            if backup is not None and backup.exists():
                os.replace(backup, target)
            raise
        print(f"[PASS] {profile.capitalize()} installation and GUI validation", flush=True)
        if backup:
            print(f"[INFO] Previous profile preserved at {backup}", flush=True)
        return (target, target_python), reason, False
    except (OSError, subprocess.SubprocessError, RuntimeError) as exc:
        return None, str(exc), True
    finally:
        shutil.rmtree(work, ignore_errors=True)


def prepare_environment(directory, argv, missing, *, test_profile=None):
    """Ask once, then prepare the first clean, fully validated platform profile."""
    if sys.platform == "darwin":
        print(f"Runtime: Python {platform.python_version()} ({platform.python_implementation()}); "
              f"macOS {platform.mac_ver()[0]}; CPU {platform.machine()}", flush=True)
    print("[INFO] Preparing Map Explorer environment", flush=True)
    if missing:
        print("[INFO] Environment check: " + "; ".join(missing), file=sys.stderr)
    print("Missing dependencies: " + ", ".join(missing), file=sys.stderr)
    print(f"Selected Python: {sys.executable}", file=sys.stderr)
    print("A separate platform/profile environment will be prepared; existing environments are preserved.", flush=True)
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
    runtimes = python_candidates()
    profiles = (test_profile,) if test_profile else PROFILES
    failures = []
    stop_fallback = False
    for profile in profiles:
        compatible = [(cmd, info) for cmd, info in runtimes if profile_compatible(profile, info)]
        if not compatible:
            failures.append(f"{profile}: no compatible CPython interpreter found")
            print(f"[SKIP] {profile.capitalize()} profile: no compatible CPython interpreter found", flush=True)
            continue
        for interpreter in compatible:
            environment, reason, fatal = build_profile(directory, profile, interpreter)
            if environment:
                target, python = environment
                print("[SUCCESS] Map Explorer environment ready", flush=True)
                child_argv = list(argv)
                if test_profile:
                    index = child_argv.index("--test-setup-profile")
                    del child_argv[index:index + 2]
                return subprocess.run([str(python), str(directory / "code" / "launch_desktop.py"), *child_argv],
                                      env=setup_environment(target, sys.platform == "darwin")).returncode
            failures.append(f"{profile}/Python {'.'.join(map(str, interpreter[1]['python'][:2]))}: {reason}")
            print(f"[WARN] {profile.capitalize()} profile failed: {reason}", flush=True)
            if fatal:
                print("[ERROR] Environment setup infrastructure failed; later profiles were not attempted.",
                      file=sys.stderr)
                stop_fallback = True
                break
        if stop_fallback:
            break
    print("[ERROR] No available Map Explorer profile passed validation.", file=sys.stderr)
    for failure in failures:
        print(f"  - {failure}", file=sys.stderr)
    print("Check the interpreter, internet access to PyPI, and the reported package error; "
          "then retry. Existing Python environments were preserved.", file=sys.stderr)
    return 1


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("map_dir", nargs="?", type=Path,
                        help="Optional map path; default: bundled Mekong (no folder dialog)")
    parser.add_argument("--port", type=int, default=0,
                        help="Local port; 0 chooses an available port")
    parser.add_argument("--no-browser", action="store_true")
    parser.add_argument("--no-setup", action="store_true", help="Report missing packages without installation")
    parser.add_argument("--test-setup-profile", choices=("2024", "2022"), help=argparse.SUPPRESS)
    parser.add_argument("--windows-browser", type=Path, help="WSL Windows PowerShell executable for browser interop")
    argv = sys.argv[1:] if argv is None else argv
    args = parser.parse_args(argv)
    directory = Path(__file__).resolve().parent.parent
    code_dir = directory / "code"
    if args.test_setup_profile:
        return prepare_environment(directory, argv, ["forced profile test"],
                                   test_profile=args.test_setup_profile)

    current_is_valid, reason = validate_environment(
        Path(sys.executable), code_dir, os.environ.get("VIRTUAL_ENV")
    )
    if not current_is_valid:
        print(f"[WARN] Selected Python environment is not ready: {reason}", file=sys.stderr)

    # Reuse a previously validated profile for this OS without touching a venv
    # belonging to another platform or profile.
    if not current_is_valid:
        for profile in PROFILES:
            candidate = profile_environment(directory, profile)
            python = candidate / ("Scripts/python.exe" if sys.platform == "win32" else "bin/python")
            if not python.is_file():
                continue
            valid, profile_reason = validate_environment(python, code_dir, candidate)
            if valid:
                print(f"[INFO] Using existing {profile} Map Explorer environment: {candidate}")
                return subprocess.run(
                    [str(python), str(Path(__file__).resolve()), *argv],
                    env=setup_environment(candidate, sys.platform == "darwin"),
                ).returncode
            print(f"[WARN] Existing {profile} profile is invalid: {profile_reason}", file=sys.stderr)

    if not current_is_valid:
        if args.no_setup:
            print("[ERROR] Dependency validation failed; setup is disabled by --no-setup.", file=sys.stderr)
            return 1
        return prepare_environment(directory, argv, [reason])
    from map_datasets import resolve_map
    selected = resolve_map(args.map_dir)
    if selected is None:
        print("Launch cancelled.")
        return 0
    from map_reader import Geometry
    try:
        Geometry.read(selected)
    except (OSError, ValueError) as exc:
        print(f"Not a CaMa-Flood map folder (invalid geometry metadata): {selected}: {exc}", file=sys.stderr)
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
    sys.argv = [str(directory/"code"/"app.py"), str(selected), "--port", str(port)]
    if args.windows_browser:
        try:
            Geometry.read(selected)
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

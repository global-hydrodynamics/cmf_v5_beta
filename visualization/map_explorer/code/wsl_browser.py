"""Readiness-gated Windows browser opening from the Linux server process."""

import base64
import subprocess
import threading
import time
from urllib.request import urlopen


def windows_command(executable, port):
    if not isinstance(port, int) or not 1 <= port <= 65535:
        raise ValueError("Invalid local server port")
    # Only a generated numeric loopback URL enters code, never user names/paths.
    url = f"http://127.0.0.1:{port}/"
    script = f"""$ErrorActionPreference='Stop'
$url='{url}'
$ready=$false
for($i=0; $i -lt 30; $i++) {{
 try {{ $null=Invoke-WebRequest -UseBasicParsing -Uri $url -TimeoutSec 2; $ready=$true; break }}
 catch {{ Start-Sleep -Milliseconds 500 }}
}}
if(-not $ready) {{ throw 'Windows cannot reach WSL localhost. Check WSL localhost forwarding; server remains available in WSL.' }}
Start-Process $url
"""
    encoded = base64.b64encode(script.encode("utf-16le")).decode("ascii")
    return [str(executable), "-NoProfile", "-NonInteractive", "-EncodedCommand", encoded]


def open_when_ready(executable, port, stop, timeout=120):
    url = f"http://127.0.0.1:{port}/"
    deadline = time.monotonic() + timeout
    while not stop.is_set() and time.monotonic() < deadline:
        try:
            with urlopen(url, timeout=1) as response:
                if response.status != 200:
                    raise OSError("Server not ready")
        except OSError:
            stop.wait(0.25)
            continue
        if stop.is_set():
            return
        try:
            result = subprocess.run(windows_command(executable, port), timeout=95, check=False)
            if result.returncode:
                print(
                    f"[ERROR] Windows browser/localhost forwarding failed. Try {url} in Windows; no network settings changed.",
                    flush=True,
                )
        except (OSError, subprocess.TimeoutExpired) as exc:
            print(f"[ERROR] Windows browser interop failed: {exc}. Open {url} manually in Windows.", flush=True)
        return
    if not stop.is_set():
        print(f"[ERROR] Server readiness timed out; browser was not opened. Check server output: {url}", flush=True)


def start_browser(executable, port):
    stop = threading.Event()
    worker = threading.Thread(target=open_when_ready, args=(executable, port, stop), daemon=True)
    worker.start()
    return stop, worker

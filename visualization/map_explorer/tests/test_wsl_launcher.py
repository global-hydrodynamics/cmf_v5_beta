"""Isolated WSL launch tests; real Windows execution requires a Windows host."""

import base64
from pathlib import Path
import socket
import subprocess
import threading
from types import SimpleNamespace
from unittest.mock import Mock

import pytest
import launch_desktop as desktop
import wsl_browser as browser

ROOT = Path(desktop.__file__).parent.parent


def test_windows_browser_command_uses_utf16_numeric_loopback_only():
    cmd = browser.windows_command("/mnt/d/Program Files/WindowsPowerShell/powershell.exe", 5010)
    assert cmd[0].endswith("powershell.exe") and cmd[-2] == "-EncodedCommand"
    source = base64.b64decode(cmd[-1]).decode("utf-16le")
    assert "http://127.0.0.1:5010/" in source
    assert source.index("Invoke-WebRequest") < source.index("Start-Process")
    for port in (0, 65536, "5010;evil"):
        with pytest.raises(ValueError):
            browser.windows_command("powershell.exe", port)


def test_browser_waits_for_http_and_can_cancel(monkeypatch):
    run = Mock()
    monkeypatch.setattr(browser.subprocess, "run", run)
    stop = threading.Event()
    stop.set()
    browser.open_when_ready("powershell.exe", 5001, stop)
    run.assert_not_called()
    stop.clear()
    response = Mock()
    response.__enter__ = Mock(return_value=SimpleNamespace(status=200))
    response.__exit__ = Mock()
    monkeypatch.setattr(browser, "urlopen", Mock(return_value=response))
    run.return_value = SimpleNamespace(returncode=0)
    browser.open_when_ready("powershell.exe", 5001, stop)
    assert run.call_count == 1
    run.reset_mock()
    monkeypatch.setattr(browser, "urlopen", Mock(side_effect=OSError("not ready")))
    browser.open_when_ready("powershell.exe", 5001, stop, timeout=0.01)
    run.assert_not_called()


def test_no_setup_reports_dependencies_without_pip(monkeypatch, capsys):
    monkeypatch.setattr(desktop.importlib.util, "find_spec", lambda name: None)
    prepare = Mock()
    monkeypatch.setattr(desktop, "prepare_environment", prepare)
    assert desktop.main(["--no-setup"]) == 1
    prepare.assert_not_called()
    assert "Missing WSL Python packages" in capsys.readouterr().err


def test_busy_port_does_not_stop_other_process(map_dir, monkeypatch, capsys):
    monkeypatch.setattr(desktop.importlib.util, "find_spec", lambda name: True)
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        listener.listen()
        assert desktop.main([str(map_dir), "--port", str(listener.getsockname()[1]), "--no-browser"]) == 2
        assert listener.fileno() != -1
    assert "no process was stopped" in capsys.readouterr().err


def test_shared_wsl_lifecycle_dynamic_port_and_stop(map_dir, monkeypatch):
    import app

    monkeypatch.setattr(desktop.importlib.util, "find_spec", lambda name: True)
    stop = Mock()
    worker = Mock()
    start = Mock(return_value=(stop, worker))
    monkeypatch.setattr(browser, "start_browser", start)

    def serve():
        assert "--no-browser" in desktop.sys.argv
        assert int(desktop.sys.argv[desktop.sys.argv.index("--port") + 1]) > 0
        raise KeyboardInterrupt()

    monkeypatch.setattr(app, "main", serve)
    with pytest.raises(KeyboardInterrupt):
        desktop.main([str(map_dir), "--windows-browser", "/mnt/d/Windows/powershell.exe", "--no-setup"])
    stop.set.assert_called_once()
    worker.join.assert_called_once()


def test_invalid_map_reports_before_browser(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(desktop.importlib.util, "find_spec", lambda name: True)
    (tmp_path / "params.txt").write_text("not a map")
    assert desktop.main([str(tmp_path), "--windows-browser", "/mnt/c/powershell.exe", "--no-setup"]) == 2
    assert "Invalid map" in capsys.readouterr().err


def test_linux_shell_handoff_paths_unicode_and_wrong_platform(tmp_path):
    repo = tmp_path / "repo 日本語"
    appdir = repo / "visualization/map_explorer"
    appdir.mkdir(parents=True)
    script = appdir / "launch_wsl.sh"
    script.write_text((ROOT / "launch_wsl.sh").read_text())
    runtime = repo / ".venv/bin/python"
    runtime.parent.mkdir(parents=True)
    log = tmp_path / "args"
    runtime.write_text('#!/bin/sh\nif [ "$1" = "-c" ]; then exit 0; fi\nprintf "%s\\n" "$@" > "$CMF_TEST_LOG"\n')
    runtime.chmod(0o755)
    import os

    env = dict(os.environ, CMF_TEST_LOG=str(log))
    result = subprocess.run(
        ["sh", str(script), "/mnt/d/map 日本語 with spaces", "-", "/mnt/d/Program Files/powershell.exe"],
        env=env,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    args = log.read_text().splitlines()
    assert args[1] == "/mnt/d/map 日本語 with spaces"
    assert args[-3:] == ["--windows-browser", "/mnt/d/Program Files/powershell.exe", "--no-setup"]
    bad = tmp_path / "windows python.exe"
    bad.write_text("#!/bin/sh\nexit 1\n")
    bad.chmod(0o755)
    result = subprocess.run(
        ["sh", str(script), "/map", str(bad), "powershell.exe"], env=env, capture_output=True, text=True
    )
    assert result.returncode != 0 and "CMF_WSL_PYTHON" in result.stderr


def test_windows_wrapper_static_contract():
    cmd = (ROOT / "launch_windows_wsl.cmd").read_text()
    ps = (ROOT / "launch_windows_wsl.ps1").read_text()
    assert "DisableDelayedExpansion" in cmd and "pause" in cmd
    assert "--list --quiet" in ps and "CMF_WSL_DISTRO" in ps
    assert "System.Text.UTF8Encoding" in ps and "[System.Text.Encoding]::Unicode" in ps
    assert "wslpath -u $absolute" in ps and "@prefix --exec sh $helper $map $python $powershell" in ps
    assert r"wsl\.localhost" in ps and "UNC path belongs" in ps
    assert "Set-ExecutionPolicy" not in ps and "--install" not in ps
    assert "Start-Process" not in ps  # only readiness-gated shared browser helper opens it


@pytest.mark.skip(reason="macOS host: real Windows + WSL double-click/browser/lifecycle QA requires Windows")
def test_real_windows_end_to_end():
    pass

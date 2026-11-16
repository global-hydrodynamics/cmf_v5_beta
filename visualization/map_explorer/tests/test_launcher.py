"""Consent, isolation and argument handoff checks; no packages or servers are started."""
import contextlib
import io
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import launch_desktop as launcher


class LauncherSetupTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="map explorer ")
        self.addCleanup(self.temp.cleanup)
        self.directory = Path(self.temp.name)
        self.python = self.directory / '.venv' / ('Scripts/python.exe' if sys.platform == 'win32' else 'bin/python')
        self.stdout = contextlib.redirect_stdout(io.StringIO())
        self.stderr = contextlib.redirect_stderr(io.StringIO())
        self.stdout.__enter__(); self.stderr.__enter__()
        self.addCleanup(self.stdout.__exit__, None, None, None)
        self.addCleanup(self.stderr.__exit__, None, None, None)

    def existing_environment(self):
        self.python.parent.mkdir(parents=True)
        self.python.touch()
        (self.directory / '.venv/pyvenv.cfg').write_text('test fixture')

    def test_default_no_and_explicit_no_do_not_modify_environment(self):
        for answer in ('', 'n', 'no'):
            with self.subTest(answer=answer), patch.object(launcher.sys.stdin, 'isatty', return_value=True), \
                 patch('builtins.input', return_value=answer) as prompt, patch.object(launcher.subprocess, 'run') as run:
                self.assertEqual(launcher.prepare_environment(self.directory, [], ['panel']), 0)
                self.assertIn('[y/N]', prompt.call_args.args[0])
                run.assert_not_called()
                self.assertFalse((self.directory / '.venv').exists())

    def test_noninteractive_does_not_prompt_install_or_create(self):
        with patch.object(launcher.sys.stdin, 'isatty', return_value=False), \
             patch('builtins.input') as prompt, patch.object(launcher.subprocess, 'run') as run:
            self.assertEqual(launcher.prepare_environment(self.directory, [], ['panel']), 1)
            prompt.assert_not_called(); run.assert_not_called()
            self.assertFalse((self.directory / '.venv').exists())

    def test_yes_creates_isolated_environment_and_preserves_launch_arguments(self):
        argv = ['/a map with spaces', '--port', '5009', '--no-browser']
        with patch.object(launcher.sys.stdin, 'isatty', return_value=True), \
             patch('builtins.input', return_value='Y'), \
             patch.object(launcher.subprocess, 'run', return_value=SimpleNamespace(returncode=7)) as run:
            self.assertEqual(launcher.prepare_environment(self.directory, argv, ['panel', 'bokeh']), 7)
        commands = [item.args[0] for item in run.call_args_list]
        self.assertEqual(commands[0], [sys.executable, '-m', 'venv', str(self.directory / '.venv')])
        self.assertEqual(commands[2], [str(self.python), '-m', 'pip', 'install', '-r', str(self.directory / 'requirements.txt')])
        self.assertEqual(commands[-1], [str(self.python), str(self.directory / 'launch_desktop.py'), *argv])
        self.assertTrue(all(c[0] == str(self.python) for c in commands[1:]))

    def test_existing_local_environment_is_updated_only_after_yes(self):
        self.existing_environment()
        with patch.object(launcher.sys.stdin, 'isatty', return_value=True), \
             patch('builtins.input', return_value='yes'), \
             patch.object(launcher.subprocess, 'run', return_value=SimpleNamespace(returncode=0)) as run:
            self.assertEqual(launcher.prepare_environment(self.directory, [], ['panel']), 0)
        self.assertFalse(any(item.args[0][1:3] == ['-m', 'venv'] for item in run.call_args_list))
        self.assertEqual(run.call_args_list[1].args[0][1:4], ['-m', 'pip', 'install'])

    def test_pip_failure_does_not_relaunch_or_touch_other_environments(self):
        self.existing_environment()
        failure = subprocess.CalledProcessError(1, 'pip')
        with patch.object(launcher.sys.stdin, 'isatty', return_value=True), \
             patch('builtins.input', return_value='y'), \
             patch.object(launcher.subprocess, 'run', side_effect=[SimpleNamespace(returncode=0), failure]) as run:
            self.assertEqual(launcher.prepare_environment(self.directory, [], ['panel']), 1)
        self.assertEqual(run.call_count, 2)
        self.assertTrue(all(item.args[0][0] == str(self.python) for item in run.call_args_list))
        self.assertTrue(self.python.exists())

    def test_wrong_prefix_stops_before_pip(self):
        self.existing_environment()
        with patch.object(launcher.sys.stdin, 'isatty', return_value=True), \
             patch('builtins.input', return_value='y'), \
             patch.object(launcher.subprocess, 'run', side_effect=subprocess.CalledProcessError(1, 'prefix check')) as run:
            self.assertEqual(launcher.prepare_environment(self.directory, [], ['panel']), 1)
        self.assertEqual(run.call_count, 1)
        self.assertNotIn('pip', run.call_args.args[0])

    def test_ready_runtime_does_not_enter_setup(self):
        with patch.object(launcher.importlib.util, 'find_spec', return_value=object()), \
             patch.object(launcher, 'prepare_environment') as setup, \
             patch.object(launcher, 'choose_map', return_value=None):
            self.assertEqual(launcher.main([]), 0)
            setup.assert_not_called()

    def test_missing_runtime_hands_original_arguments_to_setup(self):
        argv = ['my map', '--port', '5009', '--no-browser']
        with patch.object(launcher.importlib.util, 'find_spec', return_value=None), \
             patch.object(launcher, 'prepare_environment', return_value=3) as setup:
            self.assertEqual(launcher.main(argv), 3)
            self.assertEqual(setup.call_args.args[1], argv)
            self.assertIn('panel', setup.call_args.args[2])

    @unittest.skipIf(sys.platform == 'win32', 'POSIX wrapper check')
    def test_terminal_and_mac_wrappers_prefer_local_venv_and_delegate(self):
        tools = self.directory / 'visualization/map_explorer'
        tools.mkdir(parents=True)
        log = self.directory / 'arguments.txt'
        for base, tag in [(tools, 'local'), (self.directory, 'shared')]:
            python = base / '.venv/bin/python'
            python.parent.mkdir(parents=True)
            python.write_text('#!/bin/sh\nprintf "%s\\n" "'+tag+'" "$@" > "$LAUNCH_TEST_LOG"\n')
            python.chmod(0o755)
        map_dir = self.directory / 'test map'
        map_dir.mkdir()
        env = {k:v for k,v in os.environ.items() if k not in ('PYTHON', 'VIRTUAL_ENV')}
        env['LAUNCH_TEST_LOG'] = str(log)
        for name in ('run.sh', 'launch_mac.command'):
            shutil.copy2(ROOT / name, tools / name)
            result = subprocess.run(['bash', str(tools / name), str(map_dir), '--no-browser'], env=env, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            lines = log.read_text().splitlines()
            self.assertEqual(lines[0], 'local')
            self.assertEqual(lines[1], str(tools / 'launch_desktop.py'))
            self.assertIn(str(map_dir), lines)
            if name == 'run.sh':
                self.assertIn('5006', lines)


if __name__ == '__main__':
    unittest.main()

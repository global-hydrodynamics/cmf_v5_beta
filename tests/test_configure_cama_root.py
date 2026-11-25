import os
import pty
import select
import shutil
import subprocess
import tempfile
import time
import unittest
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "s00-configure_cama_root.sh"


class ConfigureRootTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="cama root tests ")
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.root = self.base / "install root '$special"
        for name in ("src_main", "map", "config"):
            (self.root / name).mkdir(parents=True, exist_ok=True)
        shutil.copy2(SCRIPT, self.root / SCRIPT.name)
        self.script = self.root / SCRIPT.name
        self.home = self.base / "test home"
        self.home.mkdir()
        self.cwd = self.base / "elsewhere"
        self.cwd.mkdir()
        self.fakebin = self.base / "bin"
        self.fakebin.mkdir()
        uname = self.fakebin / "uname"
        uname.write_text("#!/bin/sh\nprintf 'Linux\\n'\n")
        uname.chmod(0o755)

    def env(self, shell="/bin/bash"):
        env = os.environ.copy()
        env["HOME"] = str(self.home)
        env["SHELL"] = shell
        env["PATH"] = str(self.fakebin) + os.pathsep + env["PATH"]
        return env

    def run_script(self, *args, shell="/bin/bash", input_text=None):
        return subprocess.run(
            ["sh", str(self.script), *args],
            cwd=self.cwd,
            env=self.env(shell),
            input=input_text,
            text=True,
            capture_output=True,
            check=False,
        )

    def install(self, shell="/bin/bash", *args):
        return self.run_script("--yes", *args, shell=shell)

    def test_root_detected_from_other_working_directory_and_print_is_quoted(self):
        result = self.run_script("--print")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(
            result.stdout.strip(),
            "export CMF_V50_ROOT='" + str(self.root.resolve()).replace("'", "'\\''") + "'",
        )
        self.assertEqual(list(self.home.iterdir()), [])

    def test_shell_defaults_and_explicit_rc(self):
        bash = self.run_script("--show", shell="/bin/bash")
        self.assertIn(str(self.home / ".bashrc"), bash.stdout)
        zsh = self.run_script("--show", shell="/bin/zsh")
        self.assertIn(str(self.home / ".zshrc"), zsh.stdout)
        uname = self.fakebin / "uname"
        uname.write_text("#!/bin/sh\nprintf 'Darwin\\n'\n")
        mac_bash = self.run_script("--show", shell="/bin/bash")
        self.assertIn(str(self.home / ".bash_profile"), mac_bash.stdout)
        uname.write_text("#!/bin/sh\nprintf 'Linux\\n'\n")
        selected = self.run_script("--show", "--rc", str(self.home / "custom rc"))
        self.assertIn(str(self.home / "custom rc"), selected.stdout)
        tilde_selected = self.run_script("--show", "--rc", "~/custom rc")
        self.assertIn(str(self.home / "custom rc"), tilde_selected.stdout)
        self.assertEqual(list(self.home.iterdir()), [])

    def test_invocation_through_symlink_keeps_repository_root(self):
        launcher = self.base / "configure"
        launcher.symlink_to(self.script)
        result = subprocess.run(
            ["sh", str(launcher), "--print"], cwd=self.cwd, env=self.env(),
            text=True, capture_output=True, check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        direct = self.run_script("--print")
        self.assertEqual(result.stdout.strip(), direct.stdout.strip())

    def test_default_confirmation_is_no_without_a_terminal(self):
        result = self.run_script()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("No changes made", result.stdout)
        self.assertFalse((self.home / ".bashrc").exists())

    def test_first_install_and_repeat_are_idempotent(self):
        rc = self.home / ".bashrc"
        rc.write_text("# user setting\n")
        rc.chmod(0o640)
        first = self.install()
        self.assertEqual(first.returncode, 0, first.stderr)
        content = rc.read_text()
        shown = self.run_script("--show")
        self.assertIn("Current managed setting:", shown.stdout)
        self.assertIn(str(self.root.resolve()), shown.stdout)
        self.assertIn("# user setting\n", content)
        self.assertEqual(content.count("# >>> CaMa-Flood v5.0 configuration >>>"), 1)
        self.assertEqual(rc.stat().st_mode & 0o777, 0o640)
        backups = list(self.home.glob(".bashrc.cama-backup-*"))
        self.assertEqual(len(backups), 1)
        again = self.install()
        self.assertEqual(again.returncode, 0, again.stderr)
        self.assertIn("already configured", again.stdout)
        self.assertEqual(len(list(self.home.glob(".bashrc.cama-backup-*"))), 1)

    def test_existing_other_version_block_is_preserved(self):
        rc = self.home / ".bashrc"
        other = "# >>> CaMa-Flood v5.1 configuration >>>\nexport CMF_V51_ROOT='/other'\n# <<< CaMa-Flood v5.1 configuration <<<\n"
        rc.write_text("# start\n" + other)
        result = self.install()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn(other, rc.read_text())

    def test_update_requires_interactive_confirmation_and_creates_backup(self):
        rc = self.home / ".bashrc"
        old = self.base / "old root"
        old.mkdir()
        rc.write_text(
            "# >>> CaMa-Flood v5.0 configuration >>>\n"
            + "export CMF_V50_ROOT='" + str(old) + "'\n"
            + "# <<< CaMa-Flood v5.0 configuration <<<\n"
        )
        refused = self.run_script("--yes")
        self.assertNotEqual(refused.returncode, 0)
        self.assertIn("cannot authorize replacing", refused.stderr)
        self.assertIn(str(old), rc.read_text())

        master, slave = pty.openpty()
        proc = subprocess.Popen(
            ["sh", str(self.script)], cwd=self.cwd, env=self.env(),
            stdin=slave, stdout=slave, stderr=slave, close_fds=True,
        )
        os.close(slave)
        output = b""
        deadline = time.time() + 10
        while b"Update the managed configuration? [y/N]" not in output and time.time() < deadline:
            ready, _, _ = select.select([master], [], [], 0.25)
            if ready:
                try:
                    output += os.read(master, 65536)
                except OSError:
                    break
        os.write(master, b"y\n")
        code = proc.wait(timeout=10)
        try:
            output += os.read(master, 65536)
        except OSError:
            pass
        os.close(master)
        self.assertEqual(code, 0, output.decode(errors="replace"))
        expected = "export CMF_V50_ROOT='" + str(self.root.resolve()).replace("'", "'\\''") + "'"
        self.assertIn(expected, rc.read_text())
        self.assertEqual(len(list(self.home.glob(".bashrc.cama-backup-*"))), 1)

    def test_malformed_duplicate_and_unmanaged_definitions_stop(self):
        rc = self.home / ".bashrc"
        rc.write_text("# >>> CaMa-Flood v5.0 configuration >>>\n")
        result = self.install()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Malformed or duplicate", result.stderr)
        self.assertEqual(rc.read_text(), "# >>> CaMa-Flood v5.0 configuration >>>\n")

        rc.write_text("export CMF_V50_ROOT='/manual'\n")
        result = self.install()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("unmanaged", result.stderr)
        self.assertEqual(rc.read_text(), "export CMF_V50_ROOT='/manual'\n")

    def test_managed_block_with_unexpected_content_is_not_rewritten(self):
        rc = self.home / ".bashrc"
        block = "\\n".join([
            "# >>> CaMa-Flood v5.0 configuration >>>",
            "# unexpected line",
            "export CMF_V50_ROOT='/old'",
            "# <<< CaMa-Flood v5.0 configuration <<<",
            "",
        ])
        rc.write_text(block)
        result = self.install()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Malformed or duplicate", result.stderr)
        self.assertEqual(rc.read_text(), block)

    def test_duplicate_managed_blocks_stop_without_rewriting(self):
        rc = self.home / ".bashrc"
        block = (
            "# >>> CaMa-Flood v5.0 configuration >>>\\n"
            "export CMF_V50_ROOT='/old'\\n"
            "# <<< CaMa-Flood v5.0 configuration <<<\\n"
        )
        rc.write_text(block + block)
        result = self.install()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Malformed or duplicate", result.stderr)
        self.assertEqual(rc.read_text(), block + block)

    def test_startup_symlink_is_never_replaced(self):
        target = self.home / "real"
        target.write_text("# keep\n")
        (self.home / ".bashrc").symlink_to(target)
        result = self.install()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("symlink", result.stderr)
        self.assertTrue((self.home / ".bashrc").is_symlink())
        self.assertEqual(target.read_text(), "# keep\n")

    def test_unsupported_platform_does_not_select_or_edit_startup_file(self):
        uname = self.fakebin / "uname"
        uname.write_text("#!/bin/sh\\nprintf 'FreeBSD\\\\n'\\n")
        shown = self.run_script("--show")
        self.assertNotEqual(shown.returncode, 0)
        self.assertIn("supports Bash and zsh on macOS/Linux only", shown.stderr)
        self.assertEqual(list(self.home.iterdir()), [])

    def test_show_and_help_are_read_only_and_rc_override_works(self):
        show = self.run_script("--show")
        self.assertEqual(show.returncode, 0, show.stderr)
        self.assertIn("Proposed configuration", show.stdout)
        self.assertEqual(list(self.home.iterdir()), [])
        help_result = self.run_script("--help")
        self.assertEqual(help_result.returncode, 0)
        self.assertEqual(list(self.home.iterdir()), [])
        custom = self.home / "custom rc"
        configured = self.install("/bin/zsh", "--rc", str(custom))
        self.assertEqual(configured.returncode, 0, configured.stderr)
        self.assertTrue(custom.exists())
        self.assertFalse((self.home / ".zshrc").exists())

    def test_unsupported_shell_prints_manual_setting_without_editing(self):
        shown = self.run_script("--show", shell="/bin/fish")
        self.assertEqual(shown.returncode, 0, shown.stderr)
        self.assertIn("Manual setting", shown.stdout)
        attempted = self.run_script("--yes", shell="/bin/fish")
        self.assertNotEqual(attempted.returncode, 0)
        self.assertEqual(list(self.home.iterdir()), [])

    def test_export_sources_exact_special_path(self):
        result = self.run_script("--yes", "--rc", str(self.home / "special rc"))
        self.assertEqual(result.returncode, 0, result.stderr)
        source_command = '. "$1"; printf "%s" "$CMF_V50_ROOT"'
        for shell_name in ("sh", "bash", "zsh"):
            shell_path = shutil.which(shell_name)
            if shell_path is None:
                continue
            sourced = subprocess.run(
                [shell_path, "-c", source_command, shell_name,
                 str(self.home / "special rc")],
                text=True, capture_output=True, check=False,
            )
            self.assertEqual(sourced.returncode, 0, sourced.stderr)
            self.assertEqual(sourced.stdout, str(self.root.resolve()))


if __name__ == "__main__":
    unittest.main()

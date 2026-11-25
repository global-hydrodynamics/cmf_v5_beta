"""Exercise the shared POSIX Shell error-reporting contract."""
from __future__ import annotations

import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
LIBRARY = ROOT / "tools" / "code" / "cmf_check_shell_error.sh"


def run_shell(body: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["/bin/sh", "-c", f'. "{LIBRARY}"\n{body}'],
        text=True, capture_output=True, check=False, timeout=5,
    )


class SharedShellErrorTests(unittest.TestCase):
    def test_sourcing_defines_functions_without_changing_traps_or_options(self) -> None:
        result = subprocess.run(
            ["/bin/sh", "-c",
             f'before_options=$-; before_traps=$(trap); . "{LIBRARY}"; '
             'after_options=$-; after_traps=$(trap); '
             '[ "$before_options" = "$after_options" ] && '
             '[ "$before_traps" = "$after_traps" ] && '
             'command -v cmf_check_init >/dev/null && printf unchanged'],
            text=True, capture_output=True, check=False, timeout=5,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, "unchanged")

    def test_normal_execution_reports_steps_and_success_without_error_banner(self) -> None:
        result = run_shell(
            'set -eu\ncmf_check_init "Test workflow"\n'
            'cmf_check_step 1 2 "Read data"\ncmf_check_step 2 2 "Write output"\n'
            'cmf_check_success\n'
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("[STEP 1/2] Read data", result.stdout)
        self.assertIn("[STEP 2/2] Write output", result.stdout)
        self.assertIn("[SUCCESS] sh", result.stdout)
        self.assertNotIn("ERROR:", result.stderr)

    def test_failure_reports_last_step_and_preserves_original_status(self) -> None:
        result = run_shell(
            'set -eu\ncmf_check_init "Test workflow"\n'
            'cmf_check_step 2 3 "Estimate channel parameters"\n(exit 23)\n'
        )
        self.assertEqual(result.returncode, 23)
        self.assertIn("ERROR: sh FAILED", result.stderr)
        self.assertIn("Step: Estimate channel parameters", result.stderr)
        self.assertIn("Exit status: 23", result.stderr)
        self.assertEqual(result.stderr.count("ERROR:"), 1)

    def test_signal_exit_conventions(self) -> None:
        for signal_name, expected_status in (("HUP", 129), ("INT", 130), ("TERM", 143)):
            with self.subTest(signal=signal_name):
                result = run_shell(
                    'set -eu\ncmf_check_init "Test workflow"\n'
                    'cmf_check_step 3 3 "Wait for completion"\n'
                    f'kill -{signal_name} "$$"\n'
                )
                self.assertEqual(result.returncode, expected_status, result.stderr)
                self.assertIn(f"Exit status: {expected_status}", result.stderr)


if __name__ == "__main__":
    unittest.main(verbosity=2)

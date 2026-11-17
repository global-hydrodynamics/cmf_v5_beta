"""Isolated shell workflow checks; no model or scientific input is executed."""
import os
from pathlib import Path
import re
import subprocess
import tempfile
import unittest

REPO = Path(__file__).resolve().parents[2]
SCRIPTS = ('mek01-default_run.sh', 'mek02-2year_netcdf.sh')

class MekMaintenance(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='cmf mek maintenance ')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        for folder in ('gosh_test', 'src_main', 'tools', 'inp/repo-mek_1deg'):
            (self.root/folder).mkdir(parents=True)
        for year in (2000, 2001):
            (self.root/f'inp/repo-mek_1deg/runoff{year}.nc').touch()
        model = self.root/'src_main/MAIN_cmf'
        model.write_text('#!/bin/sh\ncp input_cmf.nam "captured_$(sed -n \'s/^COUTTAG *= *"\\([^"]*\\)".*/\\1/p\' input_cmf.nam).nam"\nprintf "stub model\\n" > log_CaMa.txt\n')
        model.chmod(0o755)
        for tool in ('generate_output_ctl.py', 'generate_restart_ctl.py'):
            (self.root/'tools'/tool).write_text('# isolated no-op CTL stub\n')

    def run_script(self, script, source, cwd):
        path = self.root/'gosh_test'/script
        path.write_text(source)
        env = dict(os.environ, RUNDIR=str(self.root/'output'), PROJ='isolated-test', CDPATH='/nonexistent')
        result = subprocess.run(['sh', str(path)], cwd=cwd, env=env, text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn(f'CMF_BASE = {self.root}', result.stdout)
        return {p.name: p.read_bytes() for p in (self.root/'output').glob('captured_*.nam')}

    def test_shell_syntax(self):
        for script in SCRIPTS:
            subprocess.run(['sh', '-n', str(REPO/'gosh_test'/script)], check=True)

    def test_paths_and_preserved_network_choices(self):
        for script in SCRIPTS:
            with self.subTest(script=script):
                after = (REPO/'gosh_test'/script).read_text()
                baseline = self.run_script(script, after, self.root/'gosh_test')
                self.assertEqual(self.run_script(script, after, self.root/'gosh_test'), baseline)
                self.assertEqual(self.run_script(script, after, self.root), baseline)
                self.assertEqual(self.run_script(script, after, self.root/'src_main'), baseline)
                text = b'\n'.join(baseline.values()).decode()
                suffix = 'nextxy_noedge.bin' if script.startswith('mek01') else 'netcdf/nextxy.nc'
                self.assertIn(f'{self.root}/map/mekong_15min/{suffix}', text)
                self.assertIn('diminfo_repo-mek_1deg.txt', text)
                self.assertIn('inpmat_repo-mek_1deg.bin', text)

    def test_cleanup_exact_current_and_added_variables(self):
        source = (REPO/'gosh_test'/SCRIPTS[1]).read_text()
        variables = re.search(r'^CVARSOUT="([^"]+)"', source, re.M)[1].split(',')
        self.assertEqual(variables, ['outflw', 'pthflw', 'storge', 'sfcelv', 'rivdph', 'flddph', 'fldfrc', 'fldare'])
        for extra in (False, True):
            with self.subTest(future_variable=extra):
                current = source.replace('CVARSOUT="outflw,', 'CVARSOUT="rivvel,outflw,') if extra else source
                names = variables + (['rivvel'] if extra else [])
                out = self.root/'output'
                out.mkdir(exist_ok=True)
                removed = [f'o_{v}{year}.nc' for v in names for year in (2000, 2001)]
                removed += ['restart2001010100.nc', 'restart2001010100.bin.pth', 'console_old.log', 'log_CaMa_old.txt', 'run_time_old.log', 'input_cmf_old.nam', 'year2000.complete', 'signature_old.tmp', 'summary.tsv']
                kept = ['o_outflw_notes.nc', 'o_outflw2000.nc.backup', 'o_outflw1999.nc', 'o_outflw2002.nc', 'o_unknown2000.nc', 'notes.txt']
                for name in removed + kept:
                    (out/name).write_text('sentinel')
                sibling = self.root/'other-project'
                sibling.mkdir(exist_ok=True)
                (sibling/'o_outflw2000.nc').write_text('sibling')
                self.run_script(SCRIPTS[1], current, self.root)
                self.assertTrue(all(not (out/name).exists() for name in removed))
                self.assertTrue(all((out/name).read_text() == 'sentinel' for name in kept))
                self.assertEqual((sibling/'o_outflw2000.nc').read_text(), 'sibling')

if __name__ == '__main__':
    unittest.main(verbosity=2)

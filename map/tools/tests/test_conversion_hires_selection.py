"""Focused source-discovery, terminal selection and wrapper argument checks."""
import json
import os
from pathlib import Path
import pty
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[3]


class ConversionSelectionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.map = Path(self.temp.name)/"arbitrary_map"
        self.cwd = self.map/"script_format_conv"
        self.cwd.mkdir(parents=True)
        self.env = dict(os.environ, CMF_V50_ROOT=str(ROOT))

    def source(self, tag, extension, standard=False, product="catmxy"):
        directory = self.map/"binary"/tag if standard else self.map/tag
        directory.mkdir(parents=True, exist_ok=True)
        if extension == "nc":
            (directory/"location.csv").write_text(
                "iarea,carea,west,east,south,north,nx,ny,csize\n1,tile,0,1,0,1,1,1,1\n"
            )
        else:
            (directory/"location.txt").touch()
        (directory/f"tile.{product}.{extension}").touch()
        return directory

    def execute(self, command, answers=None):
        if answers is None:
            return subprocess.run(command,cwd=self.cwd,env=self.env,stdin=subprocess.DEVNULL,
                                  capture_output=True,text=True,timeout=5)
        master,slave=pty.openpty()
        try:
            process=subprocess.Popen(command,cwd=self.cwd,env=self.env,stdin=slave,
                                     stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
            os.close(slave);slave=None
            os.write(master,answers.encode())
            try:
                stdout,stderr=process.communicate(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill();process.communicate();raise
            return subprocess.CompletedProcess(command,process.returncode,stdout,stderr)
        finally:
            os.close(master)
            if slave is not None:os.close(slave)

    def select(self,direction="nc2bin",configured="",answers=None):
        return self.execute(["sh","-c",'. "$CMF_V50_ROOT/tools/cmf_shell_functions.sh"; '
                             'cmf_select_hires_for_conversion "$1" "$2"',
                             "test",direction,configured],answers)

    def test_empty_noninteractive_requires_configuration(self):
        result=self.select()
        self.assertNotEqual(result.returncode,0)
        self.assertIn("explicit HIRES",result.stderr)
        self.assertNotIn("Proceed",result.stderr)

    def test_enter_chooses_coarsest_actual_source(self):
        for tag in ("3sec","1min","15sec"):self.source(tag,"nc")
        result=self.select(answers="\n\n")
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertEqual(result.stdout,"1min\n")
        self.assertIn("1min 15sec 3sec",result.stderr)

    def test_multiple_all_and_duplicate_order(self):
        for tag in ("3sec","1min","15sec"):self.source(tag,"nc")
        for answer,expected in [("1min 3sec","1min 3sec"),("all","1min 15sec 3sec"),
                                ("3sec 1min 3sec","1min 3sec")]:
            with self.subTest(answer=answer):
                result=self.select(answers=answer+"\n\n")
                self.assertEqual(result.stdout,expected+"\n",result.stderr)
                self.assertEqual(result.stderr.count("Proceed with conversion?"),1)

    def test_invalid_selection_retries(self):
        self.source("1min","nc");self.source("3sec","nc")
        result=self.select(answers="invalid\n1min 3sec\ny\n")
        self.assertEqual(result.stdout,"1min 3sec\n",result.stderr)
        self.assertIn("Choose one or more",result.stderr)

    def test_explicit_tags_noninteractive_and_interactive(self):
        for tag in ("1min","15sec","3sec"):self.source(tag,"nc")
        result=self.select(configured="15sec 3sec")
        self.assertEqual(result.stdout,"15sec 3sec\n",result.stderr)
        self.assertNotIn("Proceed",result.stderr)
        result=self.select(configured="15sec 3sec",answers="\n")
        self.assertEqual(result.stdout,"15sec 3sec\n",result.stderr)
        self.assertNotIn("Select resolutions",result.stderr)
        self.assertIn("Proceed",result.stderr)

    def test_cancel_has_no_selected_stdout(self):
        self.source("1min","nc")
        result=self.select(answers="\nn\n")
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertEqual(result.stdout,"")
        self.assertIn("cancelled",result.stderr)

    def test_direction_and_registered_product_discovery(self):
        self.source("1min","nc")
        self.source("15sec","bin",standard=True)
        self.source("3sec","bin")
        self.source("5sec","nc",product="unregistered")
        (self.map/"30sec").mkdir()
        self.assertEqual(self.select(configured="1min").stdout,"1min\n")
        result=self.select("bin2nc","15sec 3sec")
        self.assertEqual(result.stdout,"15sec 3sec\n",result.stderr)
        self.assertNotIn("1min",result.stderr)
        self.assertNotIn("5sec",result.stderr.split())
        self.assertNotEqual(self.select(configured="5sec").returncode,0)
        self.assertNotEqual(self.select("bin2nc","1min").returncode,0)

    def test_standard_binary_directory_shadows_legacy_as_python_does(self):
        self.source("3sec","bin")
        (self.map/"binary/3sec").mkdir(parents=True)
        result=self.select("bin2nc","3sec")
        self.assertNotEqual(result.returncode,0)
        self.assertIn("No registered",result.stderr)

    def test_no_source_products_not_offered(self):
        self.source("1min","nc",product="unregistered")
        result=self.select(configured="1min")
        self.assertNotEqual(result.returncode,0)
        self.assertIn("No registered",result.stderr)

    def test_wrappers_pass_one_multi_tag_call_and_cancel_before_call(self):
        stubdir=Path(self.temp.name)/"bin";stubdir.mkdir()
        log=Path(self.temp.name)/"calls.jsonl"
        stub=stubdir/"python3"
        stub.write_text('#!'+sys.executable+'\nimport json,os,sys\n'
                        'with open(os.environ["CALL_LOG"],"a") as f: f.write(json.dumps(sys.argv[1:])+"\\n")\n')
        stub.chmod(0o755)
        self.env.update(PATH=str(stubdir)+os.pathsep+self.env["PATH"],CALL_LOG=str(log))
        for base in ("tools","mekong_15min","Rhine_15min"):
            for name,extension in [("s03-nc2bin_highres.sh","nc"),("s13-bin2nc_highres.sh","bin")]:
                for tag in ("1min","3sec"):self.source(tag,extension)
                text=(ROOT/"map"/base/"script_format_conv"/name).read_text()
                script=self.cwd/name
                script.write_text(text.replace('HIRES=""','HIRES="3sec 1min 3sec"'))
                result=self.execute(["sh",str(script),"--no-overwrite"])
                self.assertEqual(result.returncode,0,result.stderr)
                calls=log.read_text().splitlines();self.assertEqual(len(calls),1)
                args=json.loads(calls[0])
                self.assertEqual(args[args.index("--hires")+1],"1min 3sec")
                self.assertEqual(args[args.index("--jobs")+1],"8")
                self.assertEqual(args[args.index("--variables")+1],"all")
                self.assertIn("--no-overwrite",args)
                if extension=="bin":self.assertEqual(args[args.index("--compression-level")+1],"3")
                log.unlink()
                script.write_text(text)
                result=self.execute(["sh",str(script)],answers="\nn\n")
                self.assertEqual(result.returncode,0,result.stderr)
                self.assertFalse(log.exists())


if __name__=="__main__":unittest.main()

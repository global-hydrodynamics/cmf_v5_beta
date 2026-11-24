"""Focused scientific contracts for the experimental parallel Python map tools.

The opt-in benchmark covers the 23 CLI pairs. These small tests isolate native
masking, branching, mixed-precision fallbacks and binary layout edge cases.
"""
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from types import SimpleNamespace

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
CODE = ROOT/'map/tools/code'
sys.path.insert(0, str(CODE))

from analysis_upbasin import upstream_mask
from mod_map_color import color_map
from mod_map_io import Grid, write_raster
from param_channel_calc_outclm import local_runoff, route
from param_mpi_set_region import assign_regions
from region_combine_hires import translated
from region_set_map import derive, heap_order
import test_prmwat as water_fixtures


class ScientificContractTests(unittest.TestCase):
    def test_upstream_branched_network_terminals_and_outside(self):
        xy = np.array([[[2,3,-10,-9,-9999]], [[1,1,-10,-9,-9999]]],dtype='i4')
        np.testing.assert_array_equal(upstream_mask(xy,2,1), [[1,1,0,0,-9999]])
        self.assertIsNone(upstream_mask(xy,5,1))

    def test_assignment_shift_and_legacy_branch_special_codes(self):
        assignments = np.array([[[2,4,-9,-9999]], [[3,5,-9,-9999]]], dtype='i2')
        expected = np.array([[[1,-999,-9,-9999]], [[1,-999,-9,-9999]]],dtype='i2')
        np.testing.assert_array_equal(translated(assignments,1,2,2,2), expected)
        expected[:,0,2] = -999
        np.testing.assert_array_equal(translated(assignments,1,2,2,2,True), expected)

    def test_mpi_ties_choose_first_partition_without_size_sorting(self):
        regions, loads = assign_regions(np.array([[1,2,2,3,-9999]],dtype='i4'),2)
        np.testing.assert_array_equal(regions, [[1,2,2,1,-9999]])
        np.testing.assert_array_equal(loads,[2,2])

    def test_upstream_area_and_counts_have_independent_known_sums(self):
        grid = Grid(3,1,1,*[np.float32(0)]*5)
        xy = np.array([[[3,3,-9]],[[1,1,-9]]],dtype='i4')
        sequence, area, count, basin = derive(grid,xy,np.array([[2,3,7]],dtype='f4'))
        np.testing.assert_array_equal(sequence,[[1,1,2]])
        np.testing.assert_array_equal(area,[[2,3,12]])
        np.testing.assert_array_equal(count,[[1,1,3]])
        np.testing.assert_array_equal(basin,[[1,1,1]])

    def test_local_runoff_units_missing_and_negative_mask(self):
        xy = np.array([[[3,3,-9]],[[1,1,-9]]],dtype='i4')
        source = np.array([[.001,-1,1e20]],dtype='f4')
        matrix = (np.array([[[1,2,3]]]), np.ones((1,1,3),dtype='i4'), np.full((1,1,3),1e6,dtype='f4'))
        local = local_runoff(xy[0], np.ones((1,3),dtype='f4'),source,matrix)
        np.testing.assert_allclose(local,[[1,0,0]],rtol=2*np.finfo('f4').eps)
        np.testing.assert_allclose(route(xy,local),[[1,0,1]],rtol=2*np.finfo('f4').eps)

    def test_binary_records_orientation_and_no_overwrite(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary)/'pair.bin'
            values = np.arange(12,dtype='i4').reshape(2,2,3)
            write_raster(path,values,'<i4')
            grid = Grid(3,2,1,*[np.float32(0)]*5)
            np.testing.assert_array_equal(grid.raster(path,'<i4',2),values)
            with self.assertRaises(FileExistsError):write_raster(path,values,'<i4')

    def test_colors_keep_singletons_missing_and_longitude_wrap(self):
        basin=np.array([[1,2,1,-9999]],dtype='i4')
        colors=color_map(basin,-180,180)
        self.assertEqual(colors[0,3],-9999)
        self.assertEqual(colors[0,1],1)
        self.assertEqual(colors[0,0],colors[0,2])

    def test_heap_reference_equal_children_are_deterministic(self):
        self.assertEqual(heap_order([1,1,1]),[2,3,1])
        self.assertEqual(heap_order([4,1,3,2]),[2,4,3,1])


@unittest.skipUnless(shutil.which('gfortran'),'Fortran reference unavailable')
class FallbackParityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory(prefix='cmf-port-unit-')
        cls.root = Path(cls.temp.name)
        cls.executables = {}
        for name in ('param_water_calc_prmwat','param_inpmat_generate','region_default_inpmat','region_combine_hires'):
            destination = cls.root/name
            subprocess.run(['gfortran','-O3','-cpp','-ffree-line-length-none',str(CODE/(name+'.F90')),'-o',str(destination)],check=True,capture_output=True)
            cls.executables[name]=destination

        objects = []
        for module in ('mod_map_color', 'mod_bifprm_csv'):
            obj = cls.root/(module+'.o')
            subprocess.run(['gfortran','-O3','-ffree-line-length-none','-J',str(cls.root),'-c',str(CODE/(module+'.F90')),'-o',str(obj)],cwd=cls.root,check=True,capture_output=True)
            objects.append(str(obj))
        destination = cls.root/'param_mpi_set_basin'
        subprocess.run(['gfortran','-O3','-ffree-line-length-none','-I',str(cls.root),str(CODE/'param_mpi_set_basin.F90'),*objects,'-o',str(destination)],cwd=cls.root,check=True,capture_output=True)
        cls.executables['param_mpi_set_basin'] = destination

    @classmethod
    def tearDownClass(cls):cls.temp.cleanup()

    def test_area_fallbacks_and_selected_missing_height(self):
        for name in ('param_water_calc_prmwat','param_inpmat_generate','region_default_inpmat'):
            with self.subTest(program=name), tempfile.TemporaryDirectory(prefix='cmf-port-fixture-') as temp:
                root = Path(temp); source=root/'source'; source.mkdir(); work=source/'work'; work.mkdir(); out=root/'out';out.mkdir()
                water_fixtures.PermanentWaterTests.make_inputs(SimpleNamespace(map_root=source))
                np.full((2,2),1e10,dtype='<f4').tofile(source/'ctmare.bin')
                args=['1min'];cwd=source
                product='prmwat.bin'
                if name=='param_inpmat_generate':
                    args += ['1','-180','180','90','-90','NtoS','diminfo_trial.txt','inpmat_trial.bin'];product='inpmat_trial.bin'
                elif name=='region_default_inpmat':cwd=work;product='inpmat_test-1deg.bin'
                a=subprocess.run([str(self.executables[name]),*args],cwd=cwd,capture_output=True,text=True)
                b=subprocess.run([sys.executable,str(CODE/(name+'.py')),*args,'--map-dir',str(source),'--output-dir',str(out)],cwd=root,capture_output=True,text=True)
                self.assertEqual(a.returncode,0,a.stdout+a.stderr)
                self.assertEqual(b.returncode,0,b.stdout+b.stderr)
                reference=np.fromfile(source/product,dtype='<f4');actual=np.fromfile(out/product,dtype='<f4')
                np.testing.assert_allclose(actual,reference,rtol=8*np.finfo('f4').eps,atol=0)
                if name=='param_water_calc_prmwat':
                    self.assertIn('flddif=-9999',b.stdout)
                    self.assertEqual(actual[1],0)

    def test_invalid_mixed_assignment_rejected_by_both(self):
        with tempfile.TemporaryDirectory(prefix='cmf-invalid-assignment-') as temp:
            root = Path(temp)
            water_fixtures.PermanentWaterTests.make_inputs(SimpleNamespace(map_root=root), grdare=[.1]*4)
            path = root/'1min/area.catmxy.bin'
            values = np.fromfile(path,dtype='<i2').reshape(2,2,2)
            values[1,0,0] = -9
            values.tofile(path)
            a = subprocess.run([str(self.executables['param_water_calc_prmwat']),'1min'],cwd=root,capture_output=True)
            b = subprocess.run([sys.executable,str(CODE/'param_water_calc_prmwat.py'),'1min','--map-dir',str(root),'--output-dir',str(root/'out')],capture_output=True)
            self.assertNotEqual(a.returncode,0)
            self.assertNotEqual(b.returncode,0)
            self.assertFalse((root/'prmwat.bin').exists())
            self.assertFalse((root/'out/prmwat.bin').exists())

    def test_overlapping_hires_first_assignment_last_auxiliary(self):
        with tempfile.TemporaryDirectory(prefix='cmf-overlap-') as temp:
            root = Path(temp)
            source = root/'source';source.mkdir()
            hires = source/'1min';hires.mkdir()
            extent = 1/30
            (hires/'location.txt').write_text('2 narea\niarea carea west east south north nx ny csize\n'
                + ''.join(f'{i} {name} 0 {extent} 0 {extent} 2 2 {1/60}\n' for i,name in enumerate(('one','two'),1)))
            np.array([[[-9999,1],[3,-9]],[[-9999,1],[2,-9]]],dtype='<i2').tofile(hires/'one.catmxy.bin')
            np.full((2,2,2),2,dtype='<i2').tofile(hires/'two.catmxy.bin')
            for index,name in enumerate(('one','two')):
                (np.arange(4,dtype='i1').reshape(2,2)+index*10).tofile(hires/(name+'.catmzz.bin'))
                np.full((2,2),index+1,dtype='i1').tofile(hires/(name+'.visual.bin'))
            f = root/'f';f.mkdir();(f/'1min').mkdir();work=f/'work';work.mkdir();out=root/'out'
            change=work/'dim_change.txt'
            change.write_text('\n'.join([str(source)+'/', '3','2',str(1/60),'0',str(extent),'0',str(extent),'../','2','2','1','0','0',str(extent),'0',str(extent)])+'\n')
            a=subprocess.run([str(self.executables['region_combine_hires']),'1min'],cwd=work,capture_output=True,text=True)
            b=subprocess.run([sys.executable,str(CODE/'region_combine_hires.py'),'1min','--map-dir',str(f),'--output-dir',str(out),'--change-info',str(change)],cwd=root,capture_output=True,text=True)
            self.assertEqual(a.returncode,0,a.stdout+a.stderr)
            self.assertEqual(b.returncode,0,b.stdout+b.stderr)
            for reference in (f/'1min').glob('*.bin'):
                self.assertEqual(reference.read_bytes(),(out/'1min'/reference.name).read_bytes(),reference.name)
            np.testing.assert_array_equal(np.fromfile(out/'1min/1min.catmxy.bin',dtype='<i2').reshape(2,2,2)[0],[[1,-999],[2,-9]])
            np.testing.assert_array_equal(np.fromfile(out/'1min/1min.catmzz.bin',dtype='i1'),[10,1,2,3])
            np.testing.assert_array_equal(np.fromfile(out/'1min/1min.visual.bin',dtype='i1'),[2,2,2,2])

    def test_mpi_modes_and_diagnostic_integer_records(self):
        sample = ROOT/'map/mekong_15min'
        for mode in ('normal','MaxMPI'):
            with self.subTest(mode=mode), tempfile.TemporaryDirectory(prefix='cmf-mpi-port-') as temp:
                root=Path(temp);work=root/'work';work.mkdir();out=root/'out'
                for name in ('params.txt','basin.bin','nextxy.bin','bifprm.csv'):
                    shutil.copyfile(sample/name,root/name)
                a=subprocess.run([str(self.executables['param_mpi_set_basin']),mode,'check_map'],cwd=work,capture_output=True,text=True)
                b=subprocess.run([sys.executable,str(CODE/'param_mpi_set_basin.py'),mode,'check_map','--map-dir',str(root),'--output-dir',str(out)],cwd=work,capture_output=True,text=True)
                self.assertEqual(a.returncode,0,a.stdout+a.stderr)
                self.assertEqual(b.returncode,0,b.stdout+b.stderr)
                for name in ('bifcol_mpi.bin','bifbsn_mpi.tmp','check_bif_bsnmod_mpi.bin'):
                    self.assertEqual((root/name).read_bytes(),(out/name).read_bytes(),name)

    def test_half_degree_south_to_north_input_indices(self):
        sample = ROOT/'map/mekong_15min'
        with tempfile.TemporaryDirectory(prefix='cmf-inpmat-port-') as temp:
            root=Path(temp);out=root/'out'
            shutil.copyfile(sample/'params.txt',root/'params.txt')
            (root/'1min').symlink_to(sample/'1min')
            options=['1min','.5','-180','180','90','-90','StoN','diminfo_trial.txt','inpmat_trial.bin']
            a=subprocess.run([str(self.executables['param_inpmat_generate']),*options],cwd=root,capture_output=True,text=True)
            b=subprocess.run([sys.executable,str(CODE/'param_inpmat_generate.py'),*options,'--map-dir',str(root),'--output-dir',str(out)],cwd=root,capture_output=True,text=True)
            self.assertEqual(a.returncode,0,a.stdout+a.stderr)
            self.assertEqual(b.returncode,0,b.stdout+b.stderr)
            self.assertEqual((root/'inpmat_trial.bin').read_bytes(),(out/'inpmat_trial.bin').read_bytes())
            self.assertEqual((root/'diminfo_trial.txt').read_bytes(),(out/'diminfo_trial.txt').read_bytes())


if __name__=='__main__':unittest.main(verbosity=2)

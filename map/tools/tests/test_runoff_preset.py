"""CaMa-Flood-specific climatology, daily coastal-minimum and Binary contracts."""
from datetime import datetime, timedelta
from pathlib import Path
import shutil
import struct
import subprocess
import sys
import tempfile
import unittest

from netCDF4 import Dataset
import numpy as np

CODE = Path(__file__).resolve().parents[1] / 'code'
sys.path.insert(0, str(CODE))
import runoff_calc_climatology as calc
from runoff_modify_coastal import neighbor_plan, modify_day, modify


class ClimatologyTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def input_year(self, year, value, *, missing_date=None, units='mm day-1', calendar=None):
        n = 365 if calendar == 'noleap' else (datetime(year+1,1,1)-datetime(year,1,1)).days
        with Dataset(self.root/f'runoff{year}.nc', 'w') as ds:
            for name,size in [('time',n),('latitude',2),('longitude',3),('bounds',2)]:
                ds.createDimension(name,size)
            ds.createVariable('latitude','f4',('latitude',))[:] = [30,-30]
            ds.createVariable('longitude','f4',('longitude',))[:] = [-120,0,120]
            ds['latitude'].units='degrees_north';ds['longitude'].units='degrees_east'
            t=ds.createVariable('time','f8',('time',));t.units=f'days since {year}-01-01';t.bounds='time_bounds'
            if calendar: t.calendar=calendar
            t[:]=np.arange(n)+.5
            ds.createVariable('time_bounds','f8',('time','bounds'))[:] = np.column_stack((np.arange(n),np.arange(1,n+1)))
            v=ds.createVariable('runoff','f4',('time','latitude','longitude'),fill_value=-999);v.units=units
            a=np.full((n,2,3),value,dtype='f4')
            if year%4==0 and calendar is None:a[59]=999  # February 29 must not contaminate March or annual means.
            if missing_date is not None:a[missing_date,0,0]=-999
            v[:]=a

    def args(self, *more):
        args = calc.parser().parse_args(['calculate','--input-dir',str(self.root),'--start-year','2000',
            '--end-year','2001',*more])
        args.output_dir = self.root/'out'  # Unit tests own isolated temporary output, not production CLI paths.
        return args

    def test_same_calendar_day_leap_exclusion_mean_and_counts(self):
        self.input_year(2000,1);self.input_year(2001,3)
        grid,daily,counts=calc.climatology(self.args())
        np.testing.assert_array_equal(daily,np.full((365,2,3),2,dtype='f4'))
        np.testing.assert_array_equal(counts,2)
        np.testing.assert_array_equal(grid.latitude,[30,-30])
        np.testing.assert_allclose(calc.annual_mean(daily),np.float32(2/86400),rtol=0,atol=0)

    def test_noleap_calendar_crosses_february_in_gregorian_leap_year(self):
        self.input_year(2000,2,calendar='noleap')
        _,daily,_=calc.climatology(self.args('--end-year','2000'))
        np.testing.assert_array_equal(daily,2)

    def test_all_three_stages_share_source_contract_and_preserve_raw_input(self):
        import hashlib
        self.input_year(2001,1)
        source=self.root/'runoff2001.nc'
        with Dataset(source,'a') as ds:ds['runoff'][:,0,0]=0
        digest=hashlib.sha256(source.read_bytes()).hexdigest()
        args=self.args('--start-year','2001');args.longitude_boundary='auto'
        calc.calculate(args)
        modify(args)
        calc.export(args)
        np.testing.assert_array_equal(np.fromfile(calc.product_paths(args)['binary'],dtype='<f4'),np.float32(1/86400))
        self.assertEqual(hashlib.sha256(source.read_bytes()).hexdigest(),digest)

    def test_missing_years_are_counted_and_annual_requires_all_days(self):
        self.input_year(2000,1,missing_date=0);self.input_year(2001,3,missing_date=1)
        _,daily,counts=calc.climatology(self.args())
        self.assertEqual(daily[0,0,0],3);self.assertEqual(counts[0,0,0],1)
        self.assertEqual(daily[1,0,0],1)
        daily[2,0,0]=np.nan
        self.assertTrue(np.isnan(calc.annual_mean(daily)[0,0]))

    def test_missing_dates_and_unknown_units_are_errors(self):
        self.input_year(2000,1)
        with self.assertRaisesRegex(ValueError,'Incomplete years'):
            calc.climatology(self.args())
        with self.assertRaisesRegex(ValueError,'Unknown runoff units'):
            calc.daily_depth(np.ones((2,3)),'unknown',86400)

    def test_interval_depth_and_rate_conversion_and_missing(self):
        np.testing.assert_array_equal(calc.daily_depth(np.array([.001]),'m',3600),np.array([1],dtype='f4'))
        np.testing.assert_array_equal(calc.daily_depth(np.array([24]),'mm day-1',3600),np.array([1],dtype='f4'))
        np.testing.assert_array_equal(calc.daily_depth(np.array([1]),'mm s-1',3600),np.array([3600],dtype='f4'))
        self.assertTrue(np.isnan(calc.daily_depth(np.ma.array([1],mask=[True]),'mm',3600))[0])
        self.assertTrue(np.isnan(calc.daily_depth(np.array([-1]),'mm',3600))[0])

    def test_subdaily_time_weighting_and_incomplete_day(self):
        self.input_year(2001,24)
        path=self.root/'runoff2001.nc'
        # Four 6-hour intervals per day; time bounds rather than file grouping define durations.
        path.unlink()
        with Dataset(path,'w') as ds:
            for name,size in [('time',1460),('latitude',2),('longitude',3),('bounds',2)]:ds.createDimension(name,size)
            ds.createVariable('latitude','f4',('latitude',))[:]=[30,-30]
            ds.createVariable('longitude','f4',('longitude',))[:]=[-120,0,120]
            ds['latitude'].units='degrees_north';ds['longitude'].units='degrees_east'
            t=ds.createVariable('time','f8',('time',));t.units='hours since 2001-01-01';t.bounds='time_bounds';t[:]=np.arange(1460)*6+3
            ds.createVariable('time_bounds','f8',('time','bounds'))[:]=np.column_stack((np.arange(1460)*6,np.arange(1,1461)*6))
            v=ds.createVariable('runoff','f4',('time','latitude','longitude'));v.units='mm day-1';v[:]=24
        args=self.args('--start-year','2001')
        _,daily,_=calc.climatology(args)
        np.testing.assert_array_equal(daily,24)
        with Dataset(path,'a') as ds:ds['time_bounds'][1,0]=7
        with self.assertRaisesRegex(ValueError,'Incomplete/overlapping'):
            calc.climatology(args)

    def test_binary_netcdf_identity_preserves_coordinates_missing_and_overwrite(self):
        args=self.args('--coast-modification','no')
        grid=calc.Grid(np.array([120,0,-120],dtype='f8'),np.array([-30,30],dtype='f4'),'longitude','latitude')
        mean=np.array([[0,1,np.nan],[2,3,4]],dtype='f4')
        paths=calc.product_paths(args)
        calc.save_netcdf(paths['mean_before'],grid,mean,'mm s-1',calc.metadata(args))
        calc.export(args)
        with Dataset(paths['nc']) as ds:
            ds['runoff'].set_auto_mask(False)
            np.testing.assert_array_equal(np.fromfile(paths['binary'],dtype='<f4').reshape(2,3),ds['runoff'][:])
            np.testing.assert_array_equal(ds['longitude'][:],grid.longitude)
            self.assertEqual(ds['runoff'].filters()['complevel'],3)
        with self.assertRaises(FileExistsError):calc.export(args)
        args.overwrite=True;calc.export(args)


class CoastalTests(unittest.TestCase):
    def setUp(self):
        self.grid=calc.Grid(np.array([-120,0,120]),np.array([60,0,-60]),'longitude','latitude')

    def test_daily_minimum_not_minimum_of_mean_and_no_propagation(self):
        mean=np.array([[2,0,4],[0,0,0],[0,0,0]],dtype='f4')
        plan=neighbor_plan(mean,self.grid,'regional')
        first=np.array([[1,0,7],[0,0,0],[0,0,0]],dtype='f4')
        second=np.array([[3,0,1],[0,0,0],[0,0,0]],dtype='f4')
        a,_=modify_day(first,plan);b,_=modify_day(second,plan)
        self.assertEqual((a[0,1]+b[0,1])/2,1)  # min(mean donors) would be 2.
        self.assertEqual(a[2,1],0)  # Newly filled pixels never become donors.

    def test_periodic_global_regional_and_nonperiodic_latitude(self):
        mean=np.zeros((3,3),dtype='f4');mean[0,0]=2
        daily=mean.copy()
        a,_=modify_day(daily,neighbor_plan(mean,self.grid,'auto'))
        b,_=modify_day(daily,neighbor_plan(mean,self.grid,'regional'))
        self.assertEqual(a[0,2],2);self.assertEqual(b[0,2],0)
        self.assertEqual(a[2,0],0)
        regional=calc.Grid(np.array([10,11,12]),self.grid.latitude,'longitude','latitude')
        self.assertFalse(neighbor_plan(mean,regional)[3])
        with self.assertRaises(ValueError):neighbor_plan(mean,regional,'periodic')

    def test_missing_target_zero_daily_donor_and_no_candidate(self):
        mean=np.zeros((3,3),dtype='f4');mean[0,0]=2;mean[0,1]=np.nan
        day=mean.copy();day[0,0]=0
        a,_=modify_day(day,neighbor_plan(mean,self.grid,'regional'))
        self.assertEqual(a[0,1],0)  # Old code permits zero daily values from mean-positive donors.
        day[0,0]=np.nan
        a,_=modify_day(day,neighbor_plan(mean,self.grid,'regional'))
        self.assertTrue(np.isnan(a[0,1]))

    @unittest.skipUnless(shutil.which('gfortran'),'gfortran is required')
    def test_old_fortran_minimum_matches_when_mask_matches_and_differs_when_restricted(self):
        root=CODE.parents[2]
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp);exe=p/'legacy'
            subprocess.run(['gfortran','-O0','-fcheck=all','-ffree-line-length-none',
                str(root/'etc/runoff_preset/src/mod_runoff.F90'),'-o',str(exe)],check=True)
            mean=np.zeros((3,3),dtype='f4');mean[0,0]=2;mean[0,2]=4
            day=np.array([[1,0,7],[0,0,0],[0,0,0]],dtype='f4')
            day.astype('<f4').tofile(p/'day');mean.astype('<f4').tofile(p/'mean')
            # A tiny all-cell matrix reproduces only the old routine's mask; production never uses it.
            (p/'dims').write_text('3\n3\n1\n3\n3\n1\nunused\n-180\n180\n90\n-90\n')
            xx,yy=np.meshgrid(np.arange(1,4),np.arange(1,4))
            for restricted in [False,True]:
                x=xx.copy();y=yy.copy()
                if restricted:x[0,1]=-9999;y[0,1]=-9999
                np.concatenate([x.ravel(),y.ravel()]).astype('<i4').tofile(p/'matrix')
                subprocess.run([str(exe),str(p/'day'),str(p/'out'),str(p/'dims'),str(p/'matrix'),str(p/'mean')],
                               check=True,capture_output=True)
                actual,_=modify_day(day,neighbor_plan(mean,self.grid))
                legacy=np.fromfile(p/'out',dtype='<f4').reshape(3,3)
                if not restricted:self.assertEqual(actual.tobytes(),legacy.tobytes())
                else:self.assertEqual(legacy[0,1],0);self.assertEqual(actual[0,1],1)


if __name__=='__main__':unittest.main()

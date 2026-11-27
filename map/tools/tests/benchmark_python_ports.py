"""Sequential Fortran/Python comparison on existing Mekong and small fixtures.

Compile references into --work, copy base inputs and link only read-only
high-resolution inputs. Never run Fortran in an active map. Measure subprocess
wall time (including Python startup) and Darwin peak RSS, then compare outputs.
Run: python3 benchmark_python_ports.py --work /tmp/cmf-python-bench --repeats 3
"""
from __future__ import annotations

import argparse
import csv
import json
import platform
from pathlib import Path
import re
import shutil
import statistics
import subprocess
import sys
import time

import numpy as np

REPO = Path(__file__).resolve().parents[3]
CODE = REPO/'map/tools/code'
SAMPLE = REPO/'map/mekong_15min'
FLAGS = ['-O3', '-cpp', '-ffree-line-length-none', '-fimplicit-none']
# A few float32 rounding units cover different libm and reduction orders;
# integer/categorical outputs are exact. All observed errors are reported.
FLOAT_RTOL = 8*np.finfo('f4').eps


def compile_references(work):
    build = work/'bin'
    build.mkdir(parents=True, exist_ok=True)
    objects = {}
    for stem, module in [('mod_map_color', 'map_color'), ('mod_bifprm_csv', 'bifprm_csv'),
                         ('mod_allocation_map_io', 'allocation_map_io')]:
        obj = build/(stem+'.o')
        subprocess.run(['gfortran', *FLAGS, '-J', str(build), '-I', str(build), '-c', str(CODE/(stem+'.F90')), '-o', str(obj)],
                       cwd=build, check=True, capture_output=True)
        objects[re.search(r'^module\s+(\w+)', (CODE/(stem+'.F90')).read_text(), re.M|re.I)[1].lower()] = obj
    for source in sorted(CODE.glob('*.F90')):
        if source.stem.startswith('mod_'):
            continue
        text = source.read_text()
        deps = [str(obj) for name, obj in objects.items() if re.search(r'\buse\s+'+name+r'\b', text, re.I)]
        subprocess.run(['gfortran', *FLAGS, '-J', str(build), '-I', str(build), str(source), *deps, '-o', str(build/source.stem)],
                       cwd=build, check=True, capture_output=True)
    return build


def timed(command, cwd, log):
    start = time.perf_counter()
    darwin = platform.system() == 'Darwin'
    wrapped = ['/usr/bin/time', '-l', *command] if darwin else command
    result = subprocess.run(wrapped, cwd=cwd, capture_output=True, text=True, errors='replace', timeout=3600)
    elapsed = time.perf_counter()-start
    log.write_text(result.stdout+'\nSTDERR\n'+result.stderr)
    match = re.search(r'(\d+)\s+maximum resident set size', result.stderr)
    return result, elapsed, int(match[1]) if match else None


def compare_file(reference, actual, integer=False):
    if not reference.is_file() or not actual.is_file():
        return {'equivalent': False, 'reason': 'missing output'}
    if reference.read_bytes() == actual.read_bytes():
        return {'equivalent': True, 'bitwise': True, 'max_abs': 0., 'max_rel': 0.}
    if reference.name.startswith('inpmat') and reference.suffix == '.bin':
        a = np.fromfile(reference, dtype='<i4')
        b = np.fromfile(actual, dtype='<i4')
        if a.shape != b.shape or len(a) % 3:
            return {'equivalent': False, 'reason': 'mixed INPMAT shape mismatch'}
        split = 2*(len(a)//3)
        indices_equal = np.array_equal(a[:split], b[:split])
        aa, bb = a[split:].view('<f4'), b[split:].view('<f4')
        finite = np.isfinite(aa) & np.isfinite(bb)
        delta = abs(aa[finite].astype('f8')-bb[finite])
        relative = delta/np.maximum(abs(aa[finite]), np.finfo('f4').tiny)
        return {'equivalent': bool(indices_equal and np.allclose(aa,bb,rtol=FLOAT_RTOL,atol=0,equal_nan=True)),
                'integer_indices_exact': bool(indices_equal), 'bitwise': False,
                'max_abs': float(delta.max(initial=0)), 'max_rel': float(relative.max(initial=0))}
    if reference.suffix in ('.bin', '.tmp'):
        a = np.fromfile(reference, dtype='<i4' if integer else '<f4')
        b = np.fromfile(actual, dtype=a.dtype)
        if a.shape != b.shape:
            return {'equivalent': False, 'reason': 'shape mismatch'}
        if integer:
            return {'equivalent': False, 'reason': f'{np.count_nonzero(a!=b)} different integers'}
        if not np.array_equal(a == -9999, b == -9999) or not np.array_equal(np.isfinite(a), np.isfinite(b)):
            return {'equivalent': False, 'reason': 'missing/nonfinite mismatch'}
        finite = np.isfinite(a) & np.isfinite(b)
        difference = abs(a[finite].astype('f8')-b[finite])
        relative = difference/np.maximum(abs(a[finite]), np.finfo('f4').tiny)
        return {'equivalent': bool(np.allclose(a, b, rtol=FLOAT_RTOL, atol=0, equal_nan=True)),
                'bitwise': False, 'max_abs': float(difference.max(initial=0)), 'max_rel': float(relative.max(initial=0))}
    # CSV and fixed-width allocation tables: compare named fields and ignore
    # padding while preserving record order and source precision.
    def table_rows(path):
        lines = path.read_text(encoding='utf-8-sig').splitlines()
        if path.suffix == '.csv':
            with path.open(encoding='utf-8-sig', newline='') as stream:
                rows = list(csv.reader(stream))
            return rows[0], rows[1:]
        header = lines[0].split()
        rows = []
        for line in lines[1:]:
            if not line.strip():
                continue
            if len(header) == 13:
                row = line[:112].split()
                row.extend((line[114:144].strip(), line[146:].rstrip()))
                rows.append(row)
            else:
                rows.append(line.split())
        return header, rows

    left_header, left_rows = table_rows(reference)
    right_header, right_rows = table_rows(actual)
    if left_header != right_header:
        return {'equivalent': False, 'reason': 'table header mismatch'}
    if len(left_rows) != len(right_rows):
        return {'equivalent': False, 'reason': f'row count {len(left_rows)} vs {len(right_rows)}'}
    differences = []
    for row_number, (ax, by) in enumerate(zip(left_rows, right_rows), start=1):
        if len(ax) != len(by):
            return {'equivalent': False, 'reason': f'row {row_number} field count {len(ax)} vs {len(by)}'}
        for a, b in zip(ax, by):
            if a.strip() == b.strip():
                continue
            try:
                aa, bb = float(a), float(b)
            except ValueError:
                if a.strip() != b.strip():
                    differences.append([a, b])
                continue
            if re.fullmatch(r'[+-]?\d+', a.strip()) and re.fullmatch(r'[+-]?\d+', b.strip()):
                okay = int(a) == int(b)
            else:
                # Tables round to decimal precision; permit one printed last digit.
                precision = min(10.**(-len(s.split('.')[1].split('e')[0].split('E')[0]))
                                for s in (a.strip(), b.strip()) if '.' in s) if '.' in a or '.' in b else 0.
                okay = abs(aa-bb) <= max(precision, abs(aa)*FLOAT_RTOL)
            if not okay:
                differences.append([a, b])
    return {'equivalent': not differences, 'bitwise': False, 'examples': differences[:5]}


def base_copy(destination, excluded):
    destination.mkdir(parents=True)
    for path in SAMPLE.iterdir():
        if path.is_file() and path.name not in excluded:
            shutil.copyfile(path, destination/path.name)
    if '1min' not in excluded:
        (destination/'1min').symlink_to(SAMPLE/'1min', target_is_directory=True)
    (destination/'work').mkdir()


def station_list(source, target):
    with source.open(encoding='utf-8-sig') as stream:
        rows = list(csv.reader(stream))
    with target.open('w', newline='') as stream:
        writer = csv.writer(stream, lineterminator='\n')
        writer.writerow(rows[0])
        for row in rows[1:]:
            try:
                lat, lon = map(float, row[1:3])
            except (ValueError, IndexError):
                continue
            if 90 <= lon <= 110 and 5 <= lat <= 35:
                writer.writerow(row)


def prepare(case, name):
    products = {
        'analysis_upbasin': ['analysis_upbasin_62_93.bin'],
        'analysis_subbasin': ['analysis_subbsn_30000_5000.bin', 'analysis_subcol_30000_5000.bin'],
        'analysis_mpi_region_color': ['bsncol_mpi-4.bin'],
        'analysis_check_mpi_bifurcation': ['dropped.csv'],
        'param_mpi_set_region': ['mpireg-4.bin'],
        'param_mpi_set_basin': ['bifcol_mpi.bin', 'bifbsn_mpi.tmp'],
        'param_bif_set_basin': ['bifbsn.bin', 'bifcol.bin', 'check_bif_bsnmod.bin'],
        'param_bif_set_params': ['trial.csv', 'check_bif_dphwth.bin'],
        'param_channel_set_merit_width': ['rivwth_merit.bin'],
        'param_channel_calc_rivwth': ['rivwth.bin', 'rivhgt.bin', 'rivman.bin', 'rivhgt_inf.bin'],
        'param_channel_calc_outclm': ['outclm.bin'],
        'param_inpmat_generate': ['diminfo_trial.txt', 'inpmat_trial.bin'],
        'region_default_inpmat': ['diminfo_test-1deg.txt', 'inpmat_test-1deg.bin'],
        'param_water_calc_prmwat': ['prmwat.bin'],
        'region_set_map': ['rivseq.bin', 'uparea_grid.bin', 'upgrid.bin', 'basin.bin', 'bsncol.bin', 'nxtdst_grid.bin', 'rivlen_grid.bin'],
        'region_combine_hires': ['1min'],
        'region_cut_domain': ['params.txt', 'nextxy.bin', 'downxy.bin', 'elevtn.bin', 'fldhgt.bin', 'ctmare.bin', 'grdare.bin', 'uparea.bin', 'lonlat.bin', 'nxtdst.bin', 'rivlen.bin', 'width.bin', 'lsmask.bin', 'nextxy_noedge.bin', 'catmpx.bin', 'class.bin'],
        'region_cut_bifway': ['bifori.txt'],
        'allocate_flow_gauge': ['gauge_alloc.txt'], 'allocate_level_gauge': ['gauge_alloc.txt'],
        'allocate_dam': ['dam_alloc_river.txt', 'dam_alloc_small.txt', 'dam_alloc_error.txt'],
    }.get(name, [])
    f, p = case/'f', case/'p'
    base_copy(f, products)
    p.mkdir()
    work = f/'work'
    fcwd = work
    args = []
    if name == 'analysis_upbasin': args = ['62', '93']
    elif name == 'analysis_subbasin': args = ['30000', '5000']
    elif name == 'param_mpi_set_region':
        args = ['4']; shutil.copyfile(f/'basin.bin', f/'bifbsn_mpi.tmp')
    elif name == 'analysis_mpi_region_color': args = [str(f/'mpireg-4.bin')]; fcwd = f
    elif name == 'analysis_river_node_latlon': args = ['90', '110', '5', '35']
    elif name == 'analysis_river_point_info': args = ['xy', '62', '93']
    elif name == 'param_channel_set_merit_width': args = [str(f/'diminfo_test-1deg.txt')]; fcwd = f
    elif name == 'param_bif_set_basin': args = ['--check-map']
    elif name == 'param_bif_set_params':
        args = [str(f/'rivhgt.bin'), 'trial.csv', '10', str(f/'diminfo_test-1deg.txt'), '--check-map']; fcwd = f
    elif name == 'analysis_check_mpi_bifurcation': args = [str(f/'mpireg-4.bin'), '--csv', 'dropped.csv']; fcwd = f
    elif name == 'param_channel_calc_rivwth':
        args = [str(f/'diminfo_test-1deg.txt'), '.1', '.5', '0', '1', '.4', '.75', '0', '10', '--map-binary']; fcwd = f
    elif name == 'param_channel_calc_outclm':
        np.full((180, 360), .001, dtype='<f4').tofile(f/'trial_runoff.bin')
        args = [str(f/'diminfo_test-1deg.txt'), str(f/'trial_runoff.bin'), '--runoff-binary', '--map-binary']; fcwd = f
    elif name == 'param_inpmat_generate':
        args = ['1min', '1', '-180', '180', '90', '-90', 'NtoS', 'diminfo_trial.txt', 'inpmat_trial.bin']; fcwd = f
    elif name in ('region_default_inpmat', 'region_combine_hires', 'param_water_calc_prmwat'):
        args = ['1min']
        if name == 'param_water_calc_prmwat': fcwd = f
        if name == 'region_combine_hires':
            (f/'1min').mkdir()
            values = (SAMPLE/'params.txt').read_text().splitlines()
            change = [str(SAMPLE)+'/', *[v.split()[0] for v in values[:2]], values[3].split()[0],
                      *[values[i].split()[0] for i in (4,5,6,7)], '../', '24', '40', '40', '60', '100', '106', '10', '20']
            (work/'dim_change.txt').write_text('\n'.join(change)+'\n')
            products = ['1min/'+item.name.replace('1min.', '1min.') for item in (SAMPLE/'1min').glob('*.bin')]
            # Reference emits defaults for missing optional fields too.
            products = ['1min/1min.'+v+'.bin' for v in ('catmxy','catmzz','catmz100','flddif','grdare','hand','elevtn','uparea','rivwth','visual','downxy','flwdir')]+['1min/location.txt']
    elif name == 'region_cut_domain':
        (work/'region_info.txt').write_text(str(SAMPLE)+'/\n100\n106\n10\n20\n')
        products = [file for file in products if file not in ('catmpx.bin','class.bin') or (SAMPLE/file).exists()]
    elif name == 'region_cut_bifway':
        values = (SAMPLE/'params.txt').read_text().splitlines()
        change = [str(SAMPLE)+'/', *[v.split()[0] for v in values[:2]], values[3].split()[0],
                  *[values[i].split()[0] for i in (4,5,6,7)], '../', '80', '120', '0', '0', '90', '110', '5', '35']
        (work/'dim_change.txt').write_text('\n'.join(change)+'\n')
    elif name.startswith('allocate_'):
        listing = case/'stations.csv'
        if name == 'allocate_level_gauge':
            shutil.copyfile(REPO/'map/tools/tests/data/allocation/level_synthetic_mekong.csv', listing)
        else:
            station_list(REPO/'map/data'/('GRanD_allocated.csv' if name == 'allocate_dam' else 'GRDC_allocated.csv'), listing)
        args = [str(listing), *(['multi'] if name == 'allocate_flow_gauge' else []), '1min']
        # Allocation lists are written in CWD, unlike map products.
    return f, p, fcwd, args, products


def python_product(name, fortran_product):
    outputs = {
        'allocate_flow_gauge': 'GRDC_alloc.csv',
        'allocate_level_gauge': 'MLIT_levelgauge.csv',
        'allocate_dam': {
            'dam_alloc_river.txt': 'GRanD_river.csv',
            'dam_alloc_small.txt': 'GRanD_small.csv',
            'dam_alloc_error.txt': 'GRanD_error.csv',
        },
    }
    output = outputs.get(name)
    return output.get(fortran_product, fortran_product) if isinstance(output, dict) else output or fortran_product


def compare_bifori_tables(legacy_path, csv_path):
    """Compare legacy formatted rows with named CSV output at file precision."""
    with legacy_path.open(encoding='utf-8') as stream:
        lines = stream.read().splitlines()
    try:
        expected_count, width_count = (int(value) for value in lines[0].split()[:2])
        expected_rows = [[float(value) for value in line.split()] for line in lines[1:]]
        with csv_path.open(newline='', encoding='utf-8') as stream:
            reader = csv.DictReader(stream, skipinitialspace=True)
            reader.fieldnames = [name.strip() for name in (reader.fieldnames or [])]
            actual_rows = list(reader)
        actual_values = []
        for row in actual_rows:
            widths = [row['riv_width']]
            widths.extend(row[f'ovl_width_{index}'] for index in range(1, width_count))
            actual_values.append([row['ix'], row['iy'], row['jx'], row['jy'], row['length'],
                                  row['elevtn'], *widths, row['start_lat'], row['start_lon']])
        actual_rows_as_values = [[float(value) for value in row] for row in actual_values]
        equivalent = (len(expected_rows) == len(actual_rows_as_values) == expected_count
                      and all(len(row) == 6 + width_count + 2 for row in expected_rows)
                      and all(np.allclose(reference, actual, rtol=5e-7, atol=0.0051)
                              for reference, actual in zip(expected_rows, actual_rows_as_values)))
    except (OSError, ValueError, KeyError, IndexError):
        equivalent = False
    return {'equivalent': equivalent}


def run_case(index, name, work, build, repeats):
    case = work/f'c{index:02d}'
    case.mkdir()
    f, p, fcwd, args, products = prepare(case, name)
    ftimes, ptimes, fmem, pmem = [], [], [], []
    checks = {}
    for repetition in range(repeats):
        for product in products:
            location = fcwd/product if name.startswith('allocate_') else f/product
            if repetition:
                if location.is_dir(): shutil.rmtree(location)
                else: location.unlink(missing_ok=True)
            destination = p/python_product(name, product)
            if destination.is_dir(): shutil.rmtree(destination)
            else: destination.unlink(missing_ok=True)
        if name == 'region_combine_hires': (f/'1min').mkdir(exist_ok=True)
        if name == 'region_cut_domain' and repetition:
            (fcwd/'dim_change.txt').unlink(missing_ok=True)
        a, elapsed, rss = timed([str(build/name), *args], fcwd, case/f'f{repetition}.log')
        ftimes.append(elapsed); fmem.append(rss)
        pargs = args.copy()
        if name == 'analysis_check_mpi_bifurcation': pargs[-1] = str(p/'dropped.csv')
        extra = ['--map-dir', str(f), '--output-dir', str(p)]
        if name == 'region_cut_domain': extra += ['--region-info', str(fcwd/'region_info.txt'), '--change-info', str(p/'dim_change.txt')]
        if name in ('region_combine_hires','region_cut_bifway'): extra += ['--change-info', str(fcwd/'dim_change.txt')]
        if name == 'region_cut_domain': (p/'dim_change.txt').unlink(missing_ok=True)
        python_name = 'analysis_mpi_dropped_bifurcation' if name == 'analysis_check_mpi_bifurcation' else name
        b, elapsed, rss = timed([sys.executable, str(CODE/(python_name+'.py')), *pargs, *extra], case, case/f'p{repetition}.log')
        ptimes.append(elapsed); pmem.append(rss)
        if a.returncode or b.returncode:
            return {'program': name, 'status': 'FAIL', 'reason': f'Fortran={a.returncode}, Python={b.returncode}; see c{index:02d} logs'}
        checks = {}
        for product in products:
            location = fcwd/product if name.startswith('allocate_') else f/product
            integer = ('analysis_' in name and 'point' not in name) or product in ('mpireg-4.bin','bifcol_mpi.bin','bifbsn_mpi.tmp','bifbsn.bin','bifcol.bin','check_bif_bsnmod.bin','nextxy.bin','nextxy_noedge.bin','downxy.bin','lsmask.bin','catmpx.bin','class.bin','rivseq.bin','upgrid.bin','basin.bin','bsncol.bin')
            if '1min/' in product:
                # int8/int16 binary products can be compared as raw bytes first.
                integer = any(k in product for k in ('catm','downxy','flwdir','visual'))
            if name == 'region_cut_bifway':
                checks[product] = compare_bifori_tables(location, p/'bifori.csv')
            else:
                checks[product] = compare_file(location, p/python_product(name, product), integer)
        if not products:
            if name == 'analysis_river_node_latlon':
                checks['stdout'] = {'equivalent': a.stdout.strip().splitlines() == b.stdout.strip().splitlines()}
            else:
                # Point inspector output has extra Fortran banners; compare every labelled row.
                reference = [line.strip() for line in a.stdout.split('Point Information', 1)[-1].splitlines() if ':' in line]
                actual = [line.strip() for line in b.stdout.splitlines() if ':' in line]
                checks['stdout'] = {'equivalent': len(reference) == len(actual) and all(
                    x.split(':')[0].strip() == y.split(':')[0].strip() and
                    np.allclose([float(v) for v in x.split(':')[-1].split()], [float(v) for v in y.split(':')[-1].split()], rtol=FLOAT_RTOL)
                    for x,y in zip(reference,actual))}
    return {'program': name, 'status': 'PASS' if all(v['equivalent'] for v in checks.values()) else 'DIFFER',
            'dataset': 'Mekong 80x120; native 1min 1200x1800 where used', 'repeats': repeats,
            'fortran_seconds': statistics.median(ftimes), 'python_seconds': statistics.median(ptimes),
            'ratio': statistics.median(ptimes)/statistics.median(ftimes),
            'fortran_peak_bytes': max((v for v in fmem if v is not None),default=None),
            'python_peak_bytes': max((v for v in pmem if v is not None),default=None), 'outputs': checks}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--work', type=Path, required=True, help='New isolated benchmark directory; must not exist')
    parser.add_argument('--repeats', type=int, default=3)
    parser.add_argument('--program', action='append', help='Optional targeted rerun')
    args = parser.parse_args()
    args.work.mkdir(parents=True, exist_ok=False)
    build = compile_references(args.work)
    names = args.program or [p.stem for p in sorted(CODE.glob('*.F90')) if not p.stem.startswith('mod_')]
    results = []
    for i, name in enumerate(names):
        try:
            result = run_case(i, name, args.work, build, args.repeats)
        except Exception as exc:
            result = {'program': name, 'status': 'FAIL', 'reason': str(exc)}
        results.append(result)
        print(name, result['status'], result.get('reason', ''), flush=True)
        (args.work/'results.json').write_text(json.dumps(results, indent=2))
    environment = {'platform': platform.platform(), 'python': sys.version, 'numpy': np.__version__,
                   'compiler': subprocess.check_output(['gfortran','--version'],text=True).splitlines()[0],
                   'compiler_flags': FLAGS, 'float_rtol': FLOAT_RTOL, 'float_atol': 0,
                   'rss': 'Darwin maximum resident set size (bytes)' if platform.system()=='Darwin' else 'unavailable'}
    (args.work/'environment.json').write_text(json.dumps(environment, indent=2))


if __name__ == '__main__':
    main()

# Parallel map-tools performance comparison

Date: 2026-11-25 · DT-0184 · [scope/usage/status](python_migration_status.md)
· [all machine-readable cases](python_migration_benchmark.csv).

## Method and environment

Apple M1 Ultra, 20 physical/logical CPUs, 128 GiB RAM; macOS 13.7.8 arm64.
Python 3.12.3, NumPy 1.26.4; GNU Fortran 15.2.0 (Homebrew GCC 15.2.0_1).
Reference sources are unchanged at base `fab6e4fabae6ce46376ed225eb2b459b5a994a20`.
Flags: `-O3 -cpp -ffree-line-length-none -fimplicit-none`. The optional NetCDF
comparison also defines `UseCDF_CMF` and uses `nf-config`/`nc-config` include/link
flags. NetCDF4 1.6.5/cftime 1.6.6.1 are installed only in a temporary virtual
environment; existing Python environments and repository requirements are unchanged.

Wall time covers a fresh CLI process, including startup/imports and the timing
wrapper; compilation, fixture generation and output comparison are excluded.
`/usr/bin/time -l` supplies peak process RSS in bytes. These are process measurements,
not total driver memory. Benchmarks run sequentially, with no concurrent benchmark
jobs; OS caches are not flushed. Short cases use three repetitions and report the
median; whole-tile copy uses one run because each pair writes/compares about 9 GB.
RSS is the largest repeated measurement. Results do not predict cold storage or
full-global runtime. Python startup dominates many small Mekong cases.

Integers, masks and record layouts are exact. Floating-point screening uses
`rtol = 8 * float32 epsilon = 9.536743e-7`, `atol = 0`; missing/nonfinite masks
are checked independently. This approximately-one-ppm screening criterion is not
a universal scientific accuracy requirement. Actual differences are reported
below; the criterion was not increased to make a failed case pass. The maintainer
explicitly permits calculation-order rounding. INPMAT integer records are exact;
text tables compare values at their printed precision, allowing whitespace and
numeric spelling differences. NetCDF comparison checks dimensions, dtype,
attributes and raw values with automatic scaling/masking disabled.

## All standalone programs: real Mekong inputs

Mekong base map: 80 × 120; native 1min: 1200 × 1800. `calc_outclm` additionally
uses synthetic uniform runoff on the real map/matrix. Level allocation uses the
existing synthetic station fixture on the real map. MPI partitioning uses a copy
of base basin IDs as its temporary input, not an asserted end-to-end MPI workflow.
Combined native cropping produces 360 × 600 pixels over 100–106°E, 10–20°N.
All **23 pairs PASS**, with **68 output/labelled-stdout checks per repetition**.
Times are seconds; RSS columns are MiB.

| Program | Fortran s | Python s | P/F | F RSS | P RSS | Class |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| `allocate_dam` | 0.0253 | 0.3855 | 15.23 | 27.6 | 79.0 | A |
| `allocate_flow_gauge` | 0.0238 | 0.2661 | 11.19 | 27.5 | 88.0 | A |
| `allocate_level_gauge` | 0.0228 | 0.2275 | 9.98 | 35.9 | 72.8 | A |
| `analysis_check_mpi_bifurcation` | 0.0185 | 0.2526 | 13.63 | 2.8 | 32.4 | A |
| `analysis_mpi_region_color` | 0.0109 | 0.1468 | 13.49 | 1.6 | 31.9 | A |
| `analysis_river_node_latlon` | 0.0266 | 0.2305 | 8.68 | 1.8 | 31.9 | A |
| `analysis_river_point_info` | 0.0115 | 0.1674 | 14.59 | 1.9 | 31.6 | A |
| `analysis_subbasin` | 0.0119 | 0.2085 | 17.59 | 1.8 | 32.1 | A |
| `analysis_upbasin` | 0.0120 | 0.1625 | 13.59 | 1.8 | 31.6 | A |
| `param_bif_set_basin` | 0.0194 | 0.1606 | 8.29 | 3.0 | 32.8 | A |
| `param_bif_set_params` | 0.0223 | 0.1638 | 7.34 | 2.0 | 32.4 | A |
| `param_channel_calc_outclm` | 0.0117 | 0.1692 | 14.40 | 2.9 | 32.9 | A |
| `param_channel_calc_rivwth` | 0.0127 | 0.1472 | 11.56 | 1.9 | 31.4 | A |
| `param_channel_set_merit_width` | 0.0114 | 0.1526 | 13.40 | 1.7 | 31.2 | A |
| `param_inpmat_generate` | 0.0454 | 0.2976 | 6.56 | 30.0 | 90.1 | A |
| `param_mpi_set_basin` | 0.0167 | 0.1562 | 9.35 | 3.3 | 32.5 | A |
| `param_mpi_set_region` | 0.0117 | 0.1473 | 12.64 | 1.6 | 31.8 | A |
| `param_water_calc_prmwat` | 0.1349 | 0.1955 | 1.45 | 35.0 | 69.4 | A |
| `region_combine_hires` | 0.0472 | 0.3558 | 7.53 | 83.9 | 38.7 | B |
| `region_cut_bifway` | 0.0183 | 0.1614 | 8.82 | 1.6 | 32.3 | A |
| `region_cut_domain` | 0.0191 | 0.2278 | 11.91 | 2.9 | 32.3 | B |
| `region_default_inpmat` | 0.0451 | 0.2972 | 6.59 | 29.2 | 88.6 | A |
| `region_set_map` | 0.0169 | 0.1586 | 9.40 | 2.1 | 33.5 | A |

## Larger / additional cases

Synthetic rasters are labelled explicitly; they do not reproduce real global
river geometry. The 12000² source has native 3sec spacing over a 10° square,
int16 assignments and float32 layers. The regional crop is 2400² (2° square).
The whole-tile test requests a 20° × 10° region with **one available 10° tile**;
the absent adjacent tile is skipped exactly as in Fortran. It tests the >16000
pixel extent branch, not a complete two-tile dataset. All compared native Binary
outputs in these cases are bitwise identical.

| Case / program | Repeats | Fortran s | Python s | P/F | F RSS MiB | P RSS MiB |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| coarse / `region_cut_domain` | 3 | 0.0335 | 0.5484 | 16.37 | 26.3 | 40.4 |
| coarse / `region_set_map` | 3 | 0.0421 | 0.2038 | 4.84 | 10.7 | 78.3 |
| small_3sec / `region_combine_hires` | 3 | 0.0716 | 0.5007 | 6.99 | 100.9 | 53.2 |
| small_3sec / `param_water_calc_prmwat` | 3 | 0.1375 | 0.2194 | 1.60 | 23.7 | 69.4 |
| large_3sec / `region_combine_hires` | 3 | 1.2143 | 1.2987 | 1.07 | 5143.8 | 188.9 |
| large_3sec / `param_water_calc_prmwat` | 3 | 11.9949 | 6.5172 | 0.54 | 2199.2 | 2415.9 |
| whole_3sec / `region_combine_hires` | 1 | 2.7968 | 7.0407 | 2.52 | 4396.4 | 1234.6 |
| netcdf / `param_channel_calc_outclm` | 3 | 0.0260 | 0.1882 | 7.23 | 10.2 | 40.1 |
| netcdf / `param_channel_calc_rivwth` | 3 | 0.0280 | 0.1835 | 6.54 | 8.8 | 38.2 |

The larger coarse case is a 720 × 360 synthetic south-flowing network (259,200
cells); `cut_domain` extracts 480 × 240. The NetCDF test contains two deliberately
different time records and verifies that both implementations select the first;
`rivpar.nc` coordinates, data and attributes match exactly.

## Observed numerical differences

Most Binary products match bitwise. The nonzero errors below are from final
Mekong comparisons, in the indicated field's physical units:

| Product | Maximum absolute difference | Maximum relative difference |
| --- | ---: | ---: |
| Bifurcation depth diagnostic [m] | 2.38e-7 | 4.71e-7 |
| Annual mean discharge [m3/s] | 0.015625 | 2.13e-7 |
| Permanent-water area [m2] | 176 | 7.85e-7 |
| Upstream grid area [m2] | 655,360 | 8.40e-7 |

These small relative differences are consistent with float32 arithmetic/reduction
implementations; the larger absolute upstream-area difference is about 0.655 km2
on a large basin. No integer basin, MPI assignment, native assignment, missing
mask, or scientific threshold was relaxed. CSV exponent spelling and padding can
differ while values agree. Successful reference matching establishes tested-case
compatibility, not independent scientific validity of the legacy criteria.

## Profiling and focused optimization

- Regional network: profiling the initial 259,200-cell implementation attributed
  about 0.81 s to per-cell `derive` work and 0.12 s to adjacency color generation.
  NumPy topological fronts plus encoded int64 neighbor pairs reduced end-to-end
  Python time from about 0.99 s to 0.20 s; integer results remain exact.
- Native crop/combine: profiling found repeated assignment translation; it was
  removed. Source pixels are memory-mapped and only selected rows/columns are
  copied. The 12000²-to-2400² crop stays close to Fortran runtime while reducing
  RSS from about 5.0 GiB to about 0.18 GiB.
- Whole-tile copy initially took about 23.4 s. Profiling attributed ~10.4 s to
  generic indexed placement, ~6.1 s to memmap indexing, ~5.2 s to assignment
  translation and ~1.4 s to explicit flushes. Contiguous block copying, with only
  catmxy transformed and no extra synchronous flush, reduces it to about 7.0 s.
  It remains slower than Fortran (~2.8 s), with lower RSS (~1.2 versus 4.3 GiB).
- `cut_domain` profiling attributes about 0.35 s of ~0.55 s to legacy edge-connected
  tracing. The implementation remains explicit and compatible; optimizing that
  traversal is deferred. No new mandatory JIT/runtime dependency is imposed.
- On the large synthetic water aggregation case Python is about 0.54 times the
  Fortran runtime. Native memory mapping does not bound RSS to one block: touched
  input pages remain resident, and measured RSS is about 2.4 GiB. Do not confuse
  bounded working arrays with guaranteed bounded resident memory.

## Migration interpretation

**A (21 programs):** functionally compatible and practical for the tested small /
regional workloads. Simple analysis utilities, width combination, and parameter
formulas are the clearest candidates for a later controlled switch. Small CLI
ratios often reflect ~0.1–0.2 s startup/import overhead rather than a costly kernel.
`region_set_map` benefits from the measured vectorization; larger/global cases
still need workload-specific checks. No production default is switched here.

**B (2 programs):** `region_cut_domain` retains a slow Python edge traversal;
`region_combine_hires` trades substantial memory savings for slower whole-tile
copies. Prefer the current Fortran workflow for throughput-sensitive bulk work
until a deliberate memory/throughput decision is made. The Python crop path can
already be useful in constrained-memory experiments.

**C/D:** no standalone pair lacks a runnable representative comparison. This does
not certify every option, map or platform. Remaining scientific/format questions
are listed in the [migration status](python_migration_status.md).

Future global 30sec risks are the inherited int16 catmxy capacity, full-map arrays
and per-basin tables, graph/merge cost and memory-mapped page residency.
The current INPMAT construction reserves 100 slots for each of three four-byte
arrays per coarse cell: about 1.0 TiB at 43200 × 21600, before bookkeeping.
That inherited allocation needs a sparse/blocked redesign before that scale. No global
runtime, portability, scientific accuracy or production-readiness guarantee is
extrapolated from synthetic cases. Real 3sec data were unavailable locally.

## Reproduction

Run from the repository root. Each `--work` must be a new temporary directory.
The first command needs NumPy and gfortran; optional NetCDF additionally needs
NetCDF4 in the chosen Python and NetCDF-Fortran build tools.

```bash
python3 map/tools/tests/test_python_parallel.py
python3 map/tools/tests/benchmark_python_ports.py --work /tmp/cmf-bench-mekong --repeats 3
python3 map/tools/tests/benchmark_coarse_ports.py --work /tmp/cmf-bench-coarse --repeats 3
python3 map/tools/tests/benchmark_highres_ports.py --work /tmp/cmf-bench-small --pixels 1200 --repeats 3
python3 map/tools/tests/benchmark_highres_ports.py --work /tmp/cmf-bench-large --pixels 12000 --repeats 3
python3 map/tools/tests/benchmark_highres_ports.py --work /tmp/cmf-bench-whole \
  --pixels 12000 --repeats 1 --source /tmp/cmf-bench-large/source --whole-tile
python3 map/tools/tests/benchmark_cdf_ports.py --work /tmp/cmf-bench-netcdf --repeats 3
```

The large synthetic generator writes several GB and the whole-tile comparison
writes about 9 GB of outputs. Work directories contain results JSON, program logs
and generated data; retain compact results/logs as needed, not large fixtures in
Git. The committed CSV records **32 final cases**. Earlier harness/format/header
failures and a development-time help-string syntax error were corrected and are
not counted as successful measurements. macOS sandbox restrictions prevented RSS
measurement on the first attempt; the recorded measurements used permitted process
information access. Shared environments and scientific inputs were preserved.

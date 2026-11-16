# ERA5-Land global two-day repository sample

This is the **converted CaMa-Flood input product**, renamed from
`ERA5land-glb_2day` to `repo-ERA5land-glb_2day`. The existing NetCDF was retained
without conversion or content changes. Run the
[Product Shell](../download_ERA5-Land/sample-global_2day.sh) to download and
convert; use its `--dry-run` to inspect plans without contacting CDS.

| Item | Observed converted file / standard settings |
| --- | --- |
| File | `runoff_200001.nc`, 8,154,888 bytes (about 7.78 MiB) |
| Period | 2000-01-01 and 2000-01-02, labels at 00 UTC |
| Variable | float32 `runoff(time,lat,lon)`, units `mm` per 24-hour timestep |
| Grid | 3600 × 1801; longitude centers -180..179.9, latitude 90..-90; 0.1 degree |
| Grid edges | west -180.05, east 179.95, north 90.05, south -90.05 |
| File grouping | `DOWNLOAD_UNIT=monthly`, `OUTPUT_UNIT=monthly`, `CROFFREQ=MON` |
| Timestep | `TSTEP=24`, `IFRQ_INP=24`, `DROFUNIT=86400000` |
| Encoding | NetCDF-4, fill `1e20`, deflate level 3, shuffle |

Use `CVNROF=runoff`, `CVNTIME=time`, latitude N-to-S and an Input Matrix matching
the actual grid. A monthly file contains two daily records, not a monthly mean.
Normally the model reads this converted file, not
`original/ERA5-Land_runoff_200001.nc`. See the
[standard and advanced workflow](../download_ERA5-Land/README.md).

## Evidence and limits

This task inspected the existing file's header, coordinates and time axis;
it did not generate data, compare runoff values, or test model ingestion.
[KG-0019](../../research/records/knowledge_gaps/KG-0019.md) remains unresolved:
physical attribution of 00 UTC accumulations and period boundaries is not
established by format compatibility. Matching input-matrix/model integration
must be checked separately.

Source: ECMWF / Copernicus Climate Change Service (C3S),
[ERA5-Land hourly data, DOI:10.24381/cds.e2161bac](https://doi.org/10.24381/cds.e2161bac).
Conversion differences accumulated metres into timestep millimetres and
reorganizes dimensions/metadata; scientific time attribution is unchanged.
The [Japan sample's source-terms record](../repo-ERA5land-jpn_hourly/README.md#source-redistribution-and-git-policy)
records the catalogue's CC-BY-4.0 designation. Before publishing these particular
files, review applicable download-time terms/notices and retain attribution,
licence link, retrieval/source edition and identification of changes.

Only this README and converted `runoff_YYYYMM.nc` are eligible for Git tracking.
`original/`, `logs/` and `runoff_info_CaMaFlood.txt` are ignored. The retained
information report may still contain the former directory name; it was not
rewritten during the rename. No data were staged or pushed by this task.

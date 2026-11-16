# CaMa-Flood Interactive Map Explorer

A standalone, read-only browser for coarse CaMa-Flood river maps. Explore
rasters, stored downstream connectivity and individual cells without editing
plotting scripts, running a Fortran program, or providing model output.

## Install and launch

Python 3.10+ with NumPy, netCDF4, Matplotlib, Panel and Bokeh is required.
Activate the usual CaMa-Flood Python environment if it already contains them.
The launcher never installs packages or modifies the shared environment.
An independent installation, run from the repository root, is:

```sh
python3 -m venv visualization/map_explorer/.venv
visualization/map_explorer/.venv/bin/python -m pip install -r visualization/map_explorer/requirements.txt
./visualization/map_explorer/run.sh map/mekong_15min
```

If dependencies are already in the active environment:

```sh
./visualization/map_explorer/run.sh map/mekong_15min
./visualization/map_explorer/run.sh "/path/to/custom_map"
```

MAP_DIR resolves relative to the caller first, then relative to this repository.
An absolute path also works from any current directory. The Python selection
order is explicit `PYTHON`, active `VIRTUAL_ENV`, repository `.venv`, app-local
`.venv`, `python3`. Set `PYTHON` to choose another interpreter explicitly.

The app opens a browser at **http://127.0.0.1:5006/**; the terminal also prints
the URL. Use `--no-browser` on a headless machine or `--port 5010` if occupied.
Stop with Ctrl-C. The service listens on loopback only. It uses local plotting
resources and needs no Internet connection after installation; no web basemap,
account, external backend or database is required.

### Double-click launchers

- **macOS:** double-click `launch_mac.command` in Finder.
- **Windows:** double-click `launch_windows.bat` in File Explorer.

A folder chooser asks for a map directory containing `params.txt`. Select the
map directory itself, not its `netcdf/` subdirectory. If Python's optional Tk
folder dialog is unavailable, the terminal asks for a path; press Enter to use
the bundled Mekong map or enter `q` to cancel. Closing the chooser cancels.
The launcher chooses an available local port and opens the browser. Keep the
terminal open; Ctrl-C stops the app. Startup errors remain visible in the
terminal. Existing running instances are not stopped or replaced.

Both launchers use an explicit `PYTHON` if supplied, then an active environment,
repository `.venv`, and app-local `.venv`. macOS also checks Homebrew locations;
Windows then tries `py -3` and `python`. Optional command-line map paths bypass
the folder chooser. A `PYTHON` override must name an executable, without flags.

The macOS app-local environment has been prepared on this workstation. A
Windows machine needs its own Windows Python environment (a macOS `.venv`
cannot be reused). From **Command Prompt** in the repository root:

```bat
py -3 -m venv visualization\map_explorer\.venv
visualization\map_explorer\.venv\Scripts\python.exe -m pip install -r visualization\map_explorer\requirements.txt
```

Dependencies are never installed by double-clicking. If executable permissions
were lost when copying the Mac launcher, restore them with
`chmod +x visualization/map_explorer/launch_mac.command`.
The Windows batch wrapper is supplied but has not been executed on Windows
in this macOS development session.

## Operation

1. Choose **Raster variable**. `uparea` defaults to log scale in km². Raw
   source values, including m² areas, remain unchanged in the inspector.
2. Choose **Stored network**: `nextxy`, optional `nextxy_noedge`, or `off`.
   The latter product suppresses regional edges and is not silently substituted
   for model connectivity. Dark links are local; orange links are Flexible
   Downstream by default. Both endpoints are actual cell centers.
3. In **Explore**, drag to pan, use the wheel or box-zoom tool, and use the
   toolbar Reset or **Display & export → Full map** to return to all cells.
   The pointer reports geographic degrees. Map aspect uses the viewport's
   midpoint latitude; this is a local equirectangular view, not a projection.
4. Click a cell. A pink ring identifies the source and a pink line its
   downstream link. Open **Cell inspector** for native attributes, 1-based
   Fortran `(ix,iy)`, cell-center coordinates, destination indices/coordinates
   and local/flexible/terminal status. Inspection also works with links hidden.
5. In **Display & export**, adjust continuous palette/scale/limits, link
   colors/width, and optional contributing-area styles. Area styles represent
   **contributing area, not discharge**. Color-by-area overrides link-type colors;
   its documented fixed log display range is 1–10⁶ km². Width styling alone
   retains local/flexible colors. Manual extent fields use west/east/south/north
   geographic degrees; confirm numeric edits with Enter, then press Apply
   extent. Layer changes preserve the view.
6. **Export current view · PNG** writes a Matplotlib/Agg rendering to local
   `output/`, preserving the current extent, scale, categories, palette, links,
   selected cell/link and a colorbar/legend. The status gives its full path.
   No Selenium or additional browser engine is needed. Bokeh's toolbar Save
   separately downloads the browser canvas; use the app export for labeled PNGs.
7. **Save settings · JSON** records the map path and display options in
   `output/`. Load it with the file chooser. Settings for another map are
   rejected: launch that map separately. Selection and window size are not saved.

On narrow screens the controls and inspector use tabs. The map frame adapts
to the available width, preserving local geographic aspect. Larger maps/views
can be tall; scroll the page to reach their southern edge.

## Supported data contracts

Only `MAP_DIR/params.txt` and at least one supported raster are required.
Files may be outside the repository. The runtime does not need the map-variable
registry or import any existing visualization or preprocessing module.

| Product | Meaning / display | Binary dtype | NetCDF variable |
| --- | --- | --- | --- |
| `uparea` | contributing drainage area, m² → km²; default log | Float32 | `uparea` |
| `basin` | original basin identity; discrete colors | Int32 | `basin` |
| `bsncol` | reusable display category, **not** basin identity | Int32 | `bsncol` |
| `elevtn` | channel-top elevation, m (EGM96) | Float32 | `elevtn` |
| `ctmare`, `grdare` | catchment / grid area, m² → km² | Float32 | matching name |
| `rivlen`, `rivwth`, `rivhgt` | channel length / width / depth parameter, m | Float32 | matching name |
| `nxtdst` | downstream catchment distance, m | Float32 | `nxtdst` |
| `rivman` | roughness; registry/source units unspecified, shown as such | Float32 | `rivman` |
| `nextxy`, `nextxy_noedge` | explicit downstream indices; two records | Int32 | `nextx`, `nexty` |

NetCDF files are preferred in `MAP_DIR/netcdf/NAME.nc`, then `MAP_DIR/NAME.nc`,
then `MAP_DIR/NAME.bin`. Invalid candidates are skipped with a diagnostic;
valid Binary fallback is allowed and the selected raster source is reported.
NetCDF must have named one-dimensional lon/lat axes matching params.txt centers,
32-bit fields of the declared type, and compatible units. Both axis directions
and both `(lat,lon)` / `(lon,lat)` orders are normalized. Missing units on
nextxy are accepted according to the explicit dimensionless index contract.
Packed, curvilinear, consolidated legacy containers and unknown layouts are
unsupported. The Binary contract is little-endian, X-fastest, north-to-south,
one record per scalar raster and two records (x then y) for nextxy.

Missing-value attributes and `-9999` are masked. There is no universal
nonpositive-value mask: zero/negative elevation and supplied category values
are retained. A log view hides nonpositive values **only in the image**.
Category colors may repeat; the colorbar samples at most 16 labels when there
are many IDs, and inspection always shows the native ID. Never infer basin
identity from bsncol or from a displayed color.

Connections use stored positive in-bounds destination pairs. Negative terminal
codes are reported verbatim, without inventing a physical subtype for -9/-10.
Mixed codes, out-of-map positive indices and self links are counted and excluded
from drawing. Flexible means an index displacement greater than one in either
direction; a full 360° map uses periodic x adjacency and split seam segments.
Links crossing the viewport are retained even with both endpoints outside.

## Tests and troubleshooting

```sh
# Install pytest into the chosen environment for development only.
python -m pip install pytest
python -m pytest visualization/map_explorer/tests -q
```

The integration test reads the existing Mekong sample if present; otherwise
it explicitly skips. Synthetic maps are generated in temporary directories.
See [DESIGN.md](DESIGN.md) and [validation evidence](../../research/records/validation_runs/VR-0151.md)
for scientific conventions, executed checks and limits.

- **Missing GUI dependencies**: check `PYTHON`; install requirements into a
  chosen virtual environment. Some systems need NetCDF-C/HDF5 headers if pip
  cannot obtain a netCDF4 wheel. The launcher performs no installation.
- **Cannot open map / no supported rasters**: check params.txt and the source
  diagnostics. A missing optional file is harmless; a known file with wrong
  geometry, units, type or record count is rejected, never guessed.
- **Blank log layer**: choose linear scale or valid positive color limits.
  Source values remain accessible through inspection.
- **Port in use**: choose another `--port`; the app prints its local URL.
- **Slow very large map**: use a regional map. Rasters load on demand with a
  four-field LRU cache and Binary memory mapping; uncached inspector values use
  scalar reads. Display crops and samples native cells (up to 1200 per axis;
  PNG 2400). Sampling does not average IDs and may omit tiny features when
  zoomed out. Network construction still reads complete coarse nextxy arrays.

Deferred: bifurcations, high-resolution `flddif`/elevation/catchments (different
geometry and sometimes different area units), basin tracing/filtering,
curvilinear grids and indexed/streamed global-scale rendering. No existing
Figure workflows, numerical model, map data or shared environment are changed.
Requirements are version ranges; full packaging and cross-platform dependency
certification remain future work.

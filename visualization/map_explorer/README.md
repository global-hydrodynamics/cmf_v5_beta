# CaMa-Flood Interactive Map Explorer v2

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

## Operation and independent layers

The app keeps navigation, native inspection and export while separating three
independent groups. Settings use tabs on narrow windows; the map frame adapts
on resize, with geographic aspect corrected at the viewport midpoint.

### Background

Choose a representation in **Background**:

- **None:** transparent/blank map background, independent of network/overlays.
- **Coarse raster:** the original scalar/categorical maps; `subcol` now also
  accepts the distributed `subcol-sample.bin` display categories.
- **Unit catchments:** each native high-resolution pixel inherits the selected
  coarse variable from its stored one-based `(catmx,catmy)` assignment. Default
  `uparea` is m² → km² with logarithmic green coloring. Basin/category fields
  remain discrete. Inherited width/depth values describe the assigned coarse
  river cell, not a measurement of every fine pixel. Gray is unassigned land
  (`catmxy=-999` in both records); other missing/background pixels are white.
- **High-resolution elevation**, **8-neighbor elevation difference**, and
  **Floodplain height:** native `elevtn`, max absolute valid eight-neighbor
  elevation difference, and `flddif`, all in metres. Elevation difference is
  **not dimensionless slope** and is not divided by horizontal distance.

Choose the **High-resolution source** from discovered `location.txt` records.
No `1min/` path or Mekong size is hardcoded. The MVP renders one selected tile;
select another source for another region. Automatic cross-tile mosaics are not
implemented. Views outside the selected tile remain blank with a diagnostic.

**Terrain palette** offers gray and Gallery-equivalent `pale_terrain`. Terrain
uses exact full-tile P2/P98 clipping and square-root stretch; pale terrain adds
Gallery's 0.4 display gamma. Limits are cached and do not change on pan/zoom.
Missing `flddif` with valid elevation receives a neutral display fill; missing
both stays white. The coarse variable/palette/limits controls apply to coarse
and inherited-catchment attributes; terrain uses its dedicated palette and
full-tile normalization instead. The displayed colorbar reports physical units.

Enable **Catchment Boundaries** for actual neighboring assignment-pair edges,
not contours of displayed values. Boundaries are omitted in sampled views
and above 100,000 visible edges; zoom in for native geometry. **Channel Pixels**
adds blue `visual=10` main-channel and lavender `visual=7` small-stream pixels,
only where assigned to valid river catchments. Other visual codes are not
reinterpreted. When a fine image is sampled, these colors refer to the sampled
native pixel, so small features can be omitted until zoomed in.

### River Network

Select stored `nextxy` or `nextxy_noedge` and choose **grid_center** or
**outlet_vector** representation. Off hides the main layer. Connectivity always
comes from explicit destination indices, including Flexible Downstream links.
Outlet vectors use stored `outlon/outlat`; straight segments are graphical
model connections, not observed centerlines or reconstructed high-resolution
river paths. Regional outlets can lie slightly outside the coarse-grid bounds;
their stored coordinates are preserved. Only a full 360° map uses periodic
longitude and split seam segments.

Color and width are independent. Choose uniform, connection-type or upstream-
area colors; choose uniform or upstream-area width. The source-cell area is
contributing drainage area, **not discharge**. Classification choices are:

| Mode | Full-network reference |
| --- | --- |
| `quartiles` | Four data-derived quartiles of positive log10 area, as p01-f03 |
| `six_log` | Six equal log intervals between full-network min/max, as p01-f02 |
| `continuous` | Continuous log min/max of the complete source-link population |
| `fixed` | Explicit legacy fixed log range 1–10⁶ km² |

Class boundaries stay fixed when navigating. Thinner main links are drawn
first; heavier main-channel links remain visible. Optional direction heads
follow the stored downstream direction and are omitted above 600 visible
segments; zoom in to enable them. **Legend & diagnostics** supplies colored
swatches, class ranges and omitted-feature messages.

### Overlays

Each overlay is independent of the background and main-network style:

- **Channel / Overland:** stored bifurcation pathways resolved to outlets.
  Positive first-layer width means channel; zero means overland. All widths
  must be finite and nonnegative. Channel defaults on when first selecting
  outlet-vector representation with an available table; overland defaults off.
  Colors and width are configurable; optional channel width quartiles use the
  full set of positive first-layer log widths. These widths are not discharge.
- **Outlets:** unobtrusive markers at stored outlet coordinates, not grid centers.
- **Headwater:** native unit-catchment pixel-centroid to outlet guides for cells
  without incoming regional main links. Regional boundary omissions can create
  candidates: these are **not confirmed physical headwaters**. The selected
  tile and uparea must be available. Periodic global headwater guides are
  explicitly unsupported until circular-longitude centroid handling is added.
- **Coarse Grid:** regular cell edges from `params.txt`, independent of the
  high-resolution catchment boundaries.

Bifurcations use the first valid record of each unique directed endpoint pair,
following Gallery f04. Reversed pairs remain distinct records. Invalid indices,
widths, outlets, duplicates and conflicting duplicate widths are reported.
No stored record is changed. Bifurcation link picking is deferred; rendering,
class distinctions, unique counts and error diagnostics are implemented.

### Navigation, native inspection and export

Use drag-pan, wheel zoom, box zoom, or Reset. In **View & export**, enter
west/east/south/north in degrees, confirm with Enter and Apply extent. Layer
changes retain the view. The viewport is taken from the browser's complete
range event, avoiding partially synchronized axis updates.

Click to select a native location. **Cell inspector** distinguishes coarse
indices/attributes, high-resolution indices, raw assignment codes/status,
assigned coarse-cell attributes, native elevation/flddif/visual, and the derived
elevation difference. For catchment backgrounds, pink highlights follow the
assigned coarse river cell and its selected network geometry. The clicked
coarse position is retained separately. Outlet representation adds the actual
source/destination outlet coordinates. The inspector never treats display
colors or sampled images as measurements. Missing values remain explicit.

**Export current view · PNG** uses the same scene, classifications, masks and
colors with Matplotlib/Agg, including selected source/link, bifurcations, other
enabled overlays and legends. It writes to ignored app-local `output/`; no
browser engine or source-map writes are needed. Browser and PNG typography/
arrow sizes can differ; their scientific data and classifications agree.

**Save settings · JSON** records v2 layers and styles in `output/`. Loading old
v1 files preserves coarse/grid behavior and legacy fixed area styling. Unknown
settings warn and are ignored; missing optional sources fall back with a
message. Map-path mismatch and unsupported versions are rejected. The file
chooser reload is covered programmatically; native browser file-chooser reload
was not part of the visual checks. Selection/window size are not saved.

## Gallery compatibility

These are control combinations, not copied Figure pipelines:

| Gallery method | Explorer combination |
| --- | --- |
| p01-f02c | Coarse/category or no background + grid-center network + area color/width + six log classes |
| p01-f03a | Coarse subcol + outlet vectors + area quartiles |
| p01-f03b | Outlet vectors + area quartiles + channel/overland + outlets/guides |
| p01-f04a | Unit catchments/uparea + outlet vectors + channel bifurcations |
| p01-f04b | f04a combination + channel pixels + optional assignment boundaries |
| p01-f05 | High-resolution elevation/difference/flddif + gray/pale terrain + independently styled network |

Explorer keeps scientific classes/definitions while allowing different palettes,
width scales, extents and layouts. Runtime imports no Gallery plotting module.
Tests alone load Gallery reference functions for numerical comparison. The
existing [visualization catalog](../visualization_catalog.csv) remains the
single Figure metadata registry; a future optional JSON-preset reference could
link these combinations there. No duplicate CSV/YAML or automatic synchronization
is introduced in v2.

## Supported data contracts

Only `MAP_DIR/params.txt` and at least one supported raster are required.
Files may be outside the repository. The runtime does not need the map-variable
registry or import any existing visualization or preprocessing module.

| Product | Meaning / display | Binary dtype | NetCDF variable |
| --- | --- | --- | --- |
| `uparea` | contributing drainage area, m² → km²; default log | Float32 | `uparea` |
| `basin` | original basin identity; discrete colors | Int32 | `basin` |
| `bsncol`, `subcol` | reusable display categories, **not** basin identity | Int32 | matching name |
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
See [DESIGN.md](DESIGN.md), [v1 evidence](../../research/records/validation_runs/VR-0151.md) and [v2 evidence](../../research/records/validation_runs/VR-0152.md)
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

Deferred: automatic multi-tile mosaics, bifurcation picking, basin tracing/
filtering, periodic global headwater guides, curvilinear grids and indexed/
streamed global-scale rendering. No existing
Figure workflows, numerical model, map data or shared environment are changed.
Requirements are version ranges; full packaging and cross-platform dependency
certification remain future work.

### High-resolution and vector input details

`location.txt` uses an area count, one header row, then records of area ID,
filename prefix, W/E/S/N, NX/NY and spacing in degrees. Each supported named
prefix may have `.catmxy.bin` (two little-endian Int16 assignment planes),
`.visual.bin` (one signed Int8 plane; missing -9), `.elevtn.bin` and `.flddif.bin`
(one little-endian Float32 plane each; missing -9999). All use X-fastest,
north-first layout. Sizes and geometry are validated without loading fields.

`lonlat.nc` contains aligned Float32 `outlon/outlat` with geographic-degree
units; `lonlat.bin` is also supported as two explicit Float32 planes. Bifurcation
support currently requires NetCDF integer `ix/iy/jx/jy` path arrays and
`width(layer,path)` in metres. Stored ending coordinates are checked when
present. CSV/TXT bifurcation parsing is deferred; a missing table does not
prevent unrelated layers from operating.

High-resolution rendering reads only sampled native pixels and actual neighbor
halos. Memory maps and statistics/centroid caches are reused. On first use,
exact terrain percentiles scan the selected full tile in bounded chunks using
roughly eight bytes per native pixel in temporary disk workspace; this can be
slow or disk-intensive for global tiles, but is not performed at startup.
Full-tile centroid calculation is likewise lazy and chunked. Browser raster
transfer is capped at 1200 pixels per axis (PNG 2400); no category averaging.
Full coarse nextxy topology still scales with the coarse grid. A single Mekong
integration is evidence for this sample, not a global performance guarantee.

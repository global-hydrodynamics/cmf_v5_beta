# CaMa-Flood Interactive Map Explorer v3

## Application layout

Top-level Shell/Windows launchers remain the user entry points. All Python
implementation files, including `launch_desktop.py`, are under `code/`.
`README.md`, `DESIGN.md`, `requirements.txt` and `presets.csv` remain at the
application root; tests remain in `tests/`. Existing `.venv/` and `output/`
locations and launcher arguments are unchanged. Launchers resolve the code
relative to their own location, independently of the current directory.


With no map argument, every launcher opens the repository's bundled
`map/mekong_15min/` without a folder dialog. Mekong retains the **p01-f04b**
startup display with Channel + Overland bifurcations and its compatible Gallery
extent. Every other map also applies **p01-f04b** on initial load and map switching
when its required products are available, retaining that map's full native extent
instead of the Mekong Gallery extent. If requirements are missing or invalid,
a supported coarse display remains usable and the preset status explains why. High-resolution
**COG is preferred** for high-resolution rasters in Mekong, TE-Japan and global maps.
Model-grid scientific attributes and topology continue to use NetCDF.
Missing/invalid COG fields have an explicit NetCDF/Binary display fallback;
Catchment interaction requires compatible native COG catmxy. The categorical
`visual.nc` uses CSV units `code`; Explorer accepts this canonical encoding and
legacy dimensionless `1` without changing classification values. If regenerated
products were rejected by an older running server, restart Explorer to load the
updated reader; no data conversion or units editing is needed.

The Gallery also includes **p01-f06 · OSM_background**, a static river-network
map with OSM Standard. Use `visualization/river_map/f06-OSM_background.sh` to
reproduce that two-layer figure. Explorer's online OSM remains a browser-only
context layer and is intentionally omitted from ordinary PNG exports.

A standalone, read-only browser for coarse CaMa-Flood river maps. Explore
rasters, stored downstream connectivity and individual cells without editing
plotting scripts, running a Fortran program, or providing model output.

## Stored terminal markers and Headwater Guides

When a river network is enabled and the view spans at most **60computational
coarse cells on each axis**, paired stored `nextx=-10,nexty=-10` endpoints
appear as **7px red diamonds** and paired `nextx=-9,nexty=-9` river mouths as
**6px muted blue circles** (70%opacity),with thin white borders. Both marker types
are hidden in wider views so the global overview stays readable. Outlet Vector places them at stored
outlon/outlat; Grid Center places them at computational centers. Missing outlet
coordinates are reported and omitted, never replaced silently. Network Off hides
these markers. Browser and PNG use the same points. A terminal has no downstream
vector; no artificial connection is added. The blue markers identify stored -9
codes,not an independently detected coastline. Missing and mixed pairs are excluded. The label is deliberately **terminal (-10)**: regional cutting can also
write this code for downstream-outside-domain cells, so it is not uniquely proof
of a physical inland river mouth.

**Overlays → Headwater** is restored for native COG views, including Global. It
draws the centroid of assigned native pixels in the **visible raster window** to
their stored coarse-cell outlet. The existing full-model-grid zero-incoming-link
criterion identifies candidates, including isolated positive-uparea cells; this
can exceed the number of headwaters among valid drawn river links. These are
advisory guides, not observed channel geometry or confirmed physical headwaters.

Only the bounded native window is read (≤2million pixels/tile); no global assignment
scan/index is built. The centroid is window-limited and may move when the window
clips a catchment or disconnected component; it is not advertised as the complete
catchment centroid. At native detail over the whole tile it agrees with the prior
regional centroid. Global longitudes use a circular mean and seam-split guides to
avoid artificial lines through Greenwich. Later tiles win overlaps as in the raster.
Eight recent guide windows and model-grid candidate masks are cached; closing or
switching maps releases them. Wide/downsampled views defer guides with a zoom-in
message, rather than estimate assignments from overviews. The native guide window
is independent of background colors and the ordinary catchment-boundary toggle.

## Automatic river detail for crowded views

**River → River detail → Auto (headwaters only)** is the new-session default.
Explorer marks native source cells that have **zero incoming valid nextxy links**
in the full map. If the number of these headwater cells among visible links is
strictly greater than **Headwater count threshold** (default5,000; range1,000–20,000),
it omits only the first link leaving each such cell. Every non-headwater link
remains, irrespective of upstream area. There is no area ranking or target for
remaining river-link count, and no recursive peeling of additional upstream rows.

Zooming in restores all links when the visible headwater count is below/equal to
the threshold. **All links** disables omission. Flags are internal cached topology
metadata, not extra plotted point markers. The panel and PNG disclose candidate,
headwater and retained counts. A source with upstream links outside the viewport
is not incorrectly relabeled as a headwater. Periodic seam pieces share one flag.
Bifurcation tables are not included in this primary-nextxy definition.

Scientific topology, Inspector, native selection and source products are unchanged.
Color/width classifications keep the full reference. Presets preserve the display
preference; JSON uses `layers.network_detail` (auto/all) and `network_budget`
(now the headwater count threshold). Earlier JSON without the keys restores All
links. Existing auto settings use the revised headwater-only policy. Other overlays
keep their own rules. Initial full-network construction still occurs.

## Map Dataset — load or switch maps

Click **Map dataset** next to **Settings panel** in the header to reveal the
map-switching controls; they are hidden initially. Choose an **Available Map** or
enter **Map Directory**, then press **Load Map**. Click **Map dataset** again to
hide the controls. This drawer is independent of Visualization/Inspector mode
and the Settings panel, and opening it preserves the plot, extent and selection.
Dropdown/path edits alone do not switch.
Candidate maps are immediate children of repository `map/`, with valid params.txt
and at least one supported readable core raster; tools/src, hidden/temporary and
invalid map directories are omitted. The name, native dimensions and spacing
come from metadata. The installed datasets currently include Mekong15min,
TE-Japan1min and global15min; the list is discovered, not hardcoded.

Custom server-side directories may be absolute or relative to the **repository
root**, independently of the terminal/browser working directory. Select the map
root containing params.txt, not its netcdf subdirectory. In WSL, custom GUI paths
are Linux paths such as `/mnt/d/maps/TE-Japan_01min`.

Loading shows status and disables repeated requests. A complete new Explorer is
prepared and rendered before replacing the old view on the same server/session.
Failure keeps the current plot, selection, Inspector and Pins operational and
reports the invalid path/metadata/product. Different browser sessions have their
own active map. A map change resets extent, visualization/Gallery state, selection,
Inspector, network/native caches and Pins; it preserves the application controls
and Visualization/Inspector mode. Ordinary settings changes still keep the plot
mounted; only an explicit successful map switch replaces it.

If Pins exist, a warning offers **Switch Map and Clear Pins** and **Cancel map
switch**. Export Pins/Comparison CSV in Inspector first if needed. Nothing is
cleared on cancellation or load failure, and exported CSV files are never deleted.
Settings JSON from a different map is rejected with a message: load that map
explicitly through Map Dataset, then reload the JSON. Existing same-map v1/v2
settings and legacy tile IDs remain compatible; JSON never implicitly switches maps.
PNG/JSON filenames identify the active map and remain outside its scientific input
directory. No source data are written, restored or converted when switching.

### High-resolution COG and performance

Existing numeric `MAP_DIR/COG/RESOLUTION/AREA.FIELD.tif` files supply both display
and native inspection. Discovery validates COG layout, EPSG:4326, native dimensions,
pixel edges, signed dtype, band variable names, units and source filename.
Compatible COGs are preferred regardless of the associated NetCDF's modification
time, which can change during data copying. These compatibility checks do not
prove content equivalence. Compatible COGs prevent opening that field's high-res
NetCDF; only filesystem metadata may be checked. No conversion runs in Explorer.
Missing/incompatible COGs show diagnostics and preserve the existing NetCDF/Binary
fallback display; fallback does not enable native Catchment interaction.

The frame's actual CSS dimensions × device-pixel ratio determine sampling on both
longitude and latitude axes. The closest available internal overview in logarithmic
factor space supplies wide views; output is capped at two million pixels. Native
Catchment mode requires factor 1, no output decimation, at least one physical screen
pixel per native pixel on **both** axes and compatible COG catmxy. Native data can
be used for display without qualifying as native selection if downsampled afterward.
The mode and reason appear above the map and in Inspector. Point Select shows the
one effective automatic mode; it is no longer a manual override.

Clicks in Grid mode read coarse attributes only and hide Pixel Information/native
outlines. Catchment clicks read the exact native pixel (not the display overview).
Boundaries use only the visible native window plus a true one-pixel neighbor halo,
merge collinear exposed edges, preserve holes/components, and never close a polygon
at the viewport edge. Counts are **assigned pixels in the visible window**, not
complete catchment counts or physical area. Pan recomputes that window; style-only
changes reuse geometry. Invalid/missing catmxy has no inferred assignment.

Automatic limits use **P5/P95** over valid native assignments, including
pixel-weighted inherited coarse values. Tiles with at most50million native pixels
keep exact full-tile statistics. Larger tiles (including Global1min) use
**approximate P5/P95 from fixed sparse native samples**, so opening the map does
not require a full-tile scan or a multi-GB statistics workspace.

The large-tile sample divides the entire raster into12×12 equal pixel strata and
reads a centered patch of at most16×16 native pixels from each: at most36,864
pixels. Paired catmx/catmy validation excludes sea, unassigned and invalid pixels;
finite-value/missing masks are retained. Each sampled assigned pixel contributes
its inherited coarse value, not one vote per coarse cell. This is an approximate
pixel-frequency distribution, not physical-area weighting. Fixed patches may miss
rare/small features or introduce sampling bias; the result is a visualization
estimate, not an exact whole-tile quantile. No viewport or averaged Overview
values define these statistics. A sample with no valid assignments reports an
error and requests Manual limits rather than inventing a range.

Background controls, diagnostics and PNG legend explicitly label large-tile limits
**Approximate**. Linear/Log and palette-range processing remain the same; Log uses
P5 if positive, otherwise0.01, after percentile calculation including finite
nonpositive reference values. Manual limits remain authoritative. Clicked native
values, catmxy assignments and exposed-edge geometry remain exact and do not use
the sparse display-statistics sample.

The disposable limit cache is under the system temporary directory
(`cmf-explorer-native-stats`); `CMF_EXPLORER_STATS_CACHE` can select another writable
location outside map data. Separate exact/sparse keys include sample policy,
source signatures, assignment policy, coarse dimensions and an inherited-field
content hash. Limits are reused on pan/zoom, palette changes and subsequent
sessions. Smaller exact tiles retain bounded block/disk processing (workspace up
to eight bytes/native pixel; Japan about253MB). Large sparse tiles create no
whole-tile statistics workspace. This supersedes the earlier large-tile Manual-only
restriction; Global can open directly with p01-f04b.

Raw geographic-window arrays share a64MiB session LRU; native outlines keep8 recent
windows. Cached values precede palette/opacity transforms. File replacement changes
cache identity; map switch/close releases session caches. Dataset-drawer visibility
also remeasures frame height. Pan/zoom redraws are coalesced75ms after events using
the latest extent. Coarse-grid edges remain all-or-none, never subsampled.

Tiles of the selected resolution family are composed in lexical order (later tiles
win overlaps); click lookup follows that draw order. Physical limits come from the
first rendered tile's full native reference, shared by the composed frame. This is
not an all-tiles percentile. Other limitations: native 8-neighbor elevation
difference is displayed only at native detail; Headwater Guides use only native windows
and defer in wide views as described above. The normal river graph
and headwater link-display policy still use model-grid topology. PNG export uses
the current frame/overview and scientific coordinates; it does not reread a full
native image merely because the export has more output pixels.

## Visualization and Inspector modes

The right panel starts in **Visualization** mode: Gallery Presets above
**Background / River / Overlays / View** tabs. The top segmented selector switches
to **Inspector**, hiding Gallery/settings and showing the existing Point Select
Grid/Catchment control and Cell Inspector. This only changes the visibility of
mounted panels: plot, geographic extent, last click, selected geometry, OSM,
Background/River/Overlays, Gallery selection and Visualization sub-tab all persist.
A map click updates the current selection in either mode and never switches modes.

River and Floodplain Geometry stays visible. **River Network Connectivity** is now
an Accordion, collapsed initially, alongside the existing collapsed Floodplain
Elevation Profile, High-resolution Pixel Information and Advanced / Native Values.
Each section retains expansion while cells or top-level modes change; values update
while collapsed. Connectivity definitions and regional graph counts are unchanged.

The ordinary pixel section uses **High-res** labels (1-based Fortran ix/iy), stored
catmx/catmy, elevtn/flddif[m], signed catmz100 codes, rivwth[m], and genuine High-res
uparea[km²] where supplied. **Assigned Unit Catchment uparea** is a separate inherited
coarse attribute. Ordinary pixel rows no longer include Assignment status or
pixelwise fldhgt. Internal assignment validation and Advanced diagnostics remain;
invalid/unassigned pixels never report a successful catchment assignment. The
separate coarse NLFP profile is unchanged and never substituted for pixelwise data.

Above the map, the compact summary distinguishes **Selected Grid** from **Selected
Unit Catchment** and shows selected 1-based indices, stored Outlet (lat,lon), selected
coarse uparea converted from m² to km², selection method and assigned High-res visible-window pixel
count where available. It uses validated stored outlat/outlon, never the click or
cell center. Coordinates use five decimal places; uparea uses nine significant
digits. Missing values show Unavailable. The pixel count is not a physical area.
The selected computational rectangle is **pale lavender #D8C8F0, dashed, 3px**;
the irregular orange native catchment outline remains separate. Both browser and
PNG share these coordinates and corresponding styles.

Ordinary automatic limits now use full-reference **P5/P95**; see below for Log,
pixel weighting and the unified Gallery/legacy Auto policy. [Validation evidence](../../research/records/validation_runs/VR-0168.md)
records synthetic, actual Mekong, browser and PNG checks.

## Background, selection and view controls

The map stays mounted on the left; Visualization and Inspector modes remain on
an independently scrollable right panel. These controls preserve the geographic
viewport except for explicit navigation and aspect actions.

- **Show OpenStreetMap** is OFF initially. **OpenStreetMap Opacity** (0–100%,
  step 5) controls only the basemap; Background Opacity controls only the scientific
  raster. No Background + OSM gives an online map with scientific vectors; both
  off gives the existing blank background. Scientific missing-data fills retain
  their previous appearance and can cover tiles at 100% raster opacity.
- OSM is reprojected from Web Mercator into the unchanged longitude/latitude axes
  at each output row, rather than stretching a tile affinely in latitude. Native
  clicks, river endpoints, outlets, computational grids and catchment edges stay
  geographic. Attribution appears below the map. Only the current visible zoom
  level is requested, at most 32 tiles after a 250 ms debounce, using browser HTTP
  cache, browser identification and Referer. No prefetch or offline archive.
  Public tiles follow the [OSMF tile usage policy](https://operations.osmfoundation.org/policies/tiles/).
  They require network access and have no availability guarantee. For deployment,
  choose a suitably licensed provider via `CMF_EXPLORER_TILE_URL` (HTTPS XYZ
  `{z}/{x}/{y}` template) and `CMF_EXPLORER_TILE_ATTRIBUTION`; the provider must allow
  browser CORS image reads. Loopback HTTP is allowed for local/self-hosted tests.
  Default provider: `https://tile.openstreetmap.org/{z}/{x}/{y}.png`.
  Failed tiles remain transparent with a visible status; scientific layers work.
- **Palette Minimum / Maximum** are independent 0–1 sliders (step 0.01) for Coarse
  and High-resolution Raster. Physical Color Minimum/Maximum retain their units.
  Processing order is physical Linear/Log normalization → existing Gallery
  nonlinear transfer → `pmin + t*(pmax-pmin)` → colormap lookup. Thus Gray [0,.5]
  darkens the image; Gray [.5,1] brightens it without changing values or colorbar
  ticks. Gray reversed is also available. Defaults [0,1] preserve original colors.
  Categorical identities retain discrete colors with cropping disabled. Invalid
  intervals roll back with an explanation. Variable-specific session preferences
  are retained; active intervals are saved in JSON, not the entire profile cache.
- Terrain automatic limits are full-tile P5/P95 over **valid native paired catmxy
  assignments only**, using the existing assignment helper and coarse dimensions.
  Unassigned/sea/out-of-range pairs and nonfinite/missing values are excluded;
  Log statistics retain finite nonpositive values until after P5/P95 calculation,
  then use lower=P5 if P5>0, otherwise0.01, and upper=P95; nonpositive display pixels are masked. Elevation Difference uses native neighbors
  before this center-pixel assignment mask; this is not a new terrain derivation.
  Limits do not depend on pan/zoom or the sampled display image. Missing/unusable
  catmxy gives an explicit diagnostic and clears the unavailable background;
  use manual physical limits to display such a terrain tile. Inherited catchment
  uparea uses its coarse contributing-area values repeated for every valid assigned
  high-resolution pixel (pixel-weighted P5/P95), not the genuine native uparea
  product. Coarse cells with no assignments in the selected tile do not contribute;
  these are pixel-frequency weights, not physical-area weights. Statistics are cached by tile/variable/positive policy/
  assignment-mask version/coarse dimensions. Blocks bound RAM; disposable disk
  workspace scales with native tile size and initial scans can take time.
- Ordinary **Unit Catchment Boundaries** default to `#4A4A4A`, 0.65 px. The existing
  color picker and saved colors remain authoritative. Selected native boundaries
  remain orange solid 3 px; computational rectangles are pale lavender #D8C8F0, dashed, 3px.
- **Inspector → Point Select → Grid / Catchment** reports the automatic
  resolution-aware mode. Overview/decimated/fallback/coarse/no-background views use
  Grid; undecimated native COG views with catmxy use Catchment. Changes re-resolve
  the last click without creating another selection state. Invalid assignments in
  native mode never fall back to a containing Grid.
- **High-resolution Pixel Information** is collapsed initially and retains its
  expansion across updates. It reports High-res 1-based ix/iy, catmx/catmy,
  genuine High-res uparea[km²], elevtn[m], rivwth[m] and signed catmz100
  codes when supplied. catmz100 is the stored 100-level floodplain profile position;
  -9 is sea/unassigned, not an elevation or converted percentage. Native flddif[m]
  is explicitly separate. No pixelwise native fldhgt is inferred or shown in this ordinary section;
  the coarse NLFP profile remains in its existing section.
  The clicked pixel's native uparea and assigned coarse catchment uparea are
  separate rows in native Catchment mode. Grid mode hides this section and performs
  no native pixel reads. Scalar inspection uses native COG pixel windows.
- **View → Apply Aspect Ratio**, directly below the selector, reapplies its shape
  around the current center even when the selector has not changed. Repeated
  clicks work after pan/zoom/manual extent/resize. Custom keeps the current
  geographic proportions. Manual extents remain authoritative until an explicit
  predefined shape action. Existing viewport-height bounds and legend remain.

JSON v1/v2 still load. Missing new fields default to OSM off, full palette range
and automatic resolution-aware selection; new files retain compatible
`point_select`, `basemap`, `layers.coarse_palette_range` and
`layers.highres_style.palette_range` plus `layers.auto_limits_policy`. Fresh sessions
use `percentile`; old JSON may retain `gallery` as a compatibility flag. Both
use the same P5/P95 Auto calculation, including after applying a preset. Gallery presets reset OSM off and palette
ranges to [0,1], re-evaluating automatic Point Select from current resolution. Shared
preset settings remain CSV references to the canonical visualization catalog.

**PNG:** local Matplotlib uses the same scientific palette, physical limits and
selection geometry. Online tiles are deliberately excluded, with a notice in the
GUI/export status and PNG legend. No tile requests are made for PNG export.
See [validation report](../../research/records/validation_runs/VR-0165.md) for
executed checks and current limits; no model simulation equivalence is claimed.

## Install and launch

Python 3.10+ with NumPy, netCDF4, Matplotlib, Panel, Bokeh and rasterio is required.
macOS automatic setup has the narrower supported combinations below.
Activate the usual CaMa-Flood Python environment if it already contains them.
If dependencies are missing, an interactive launcher asks **[y/N]** before
creating/updating the isolated `visualization/map_explorer/.venv/` and installing
its requirements. Enter `y` or `yes` to continue; Enter, `n`, or no terminal
means no environment changes. Downloads require network access. After successful
installation, the launcher restarts using that environment with the same map,
port and browser options. Failed setup stops with an error and can be retried.
Conda, system Python and the shared repository `.venv/` are not modified.
For macOS use the dedicated instructions below. An independent Linux installation,
run from the repository root, is:

```sh
python3 -m venv visualization/map_explorer/.venv
visualization/map_explorer/.venv/bin/python -m pip install -r visualization/map_explorer/requirements.txt
./visualization/map_explorer/run.sh
```

If dependencies are already in the active environment:

```sh
./visualization/map_explorer/run.sh
./visualization/map_explorer/run.sh "/path/to/custom_map"
```

MAP_DIR is optional and resolves relative to this repository when not absolute.
An absolute path also works from any current directory. The Python selection
order is explicit `PYTHON`, active `VIRTUAL_ENV`, app-local `.venv`, repository
`.venv`, `python3`. Set `PYTHON` to choose another interpreter explicitly.
A Conda prompt alone does not override this order; select its interpreter with
`PYTHON` when that is intended.

The app opens a browser at **http://127.0.0.1:5006/**; the terminal also prints
the URL. Use `--no-browser` on a headless machine or `--port 5010` if occupied.
Stop with Ctrl-C. The service listens on loopback only. It uses local plotting
resources and needs no Internet connection after installation; no account, external backend or database is required. The optional OSM basemap
needs an Internet connection; offline scientific rendering stays available.

### Double-click launchers

- **macOS:** double-click `launch_mac.command` in Finder.
- **Windows:** double-click `launch_windows.bat` in File Explorer.

With no map argument, these launchers immediately use bundled Mekong. The
launcher chooses an available local port and opens the browser. Keep the terminal
open; Ctrl-C stops the app. Errors remain visible; existing instances are not
stopped. Choose another map afterward through Map Dataset, or pass an explicit
map path on the command line. No Tk/folder-dialog dependency is needed.

Both launchers use an explicit `PYTHON` if supplied, then active `VIRTUAL_ENV`,
app-local `.venv`, then repository `.venv`. macOS then checks standard python.org
Framework, Homebrew and `/usr/local` paths by Python version (3.12, 3.11,
3.10, then 3.13), followed by unversioned Python paths; no Homebrew installation is required;
Windows then tries `py -3` and `python`. A `PYTHON` override must name an executable,
without flags.

Each machine needs its own environment (a macOS `.venv` cannot be reused on
Windows). With Python 3.10+ installed, the setup prompt can prepare it; manual
installation from **Command Prompt** in the repository root is also possible:

```bat
py -3 -m venv visualization\map_explorer\.venv
visualization\map_explorer\.venv\Scripts\python.exe -m pip install -r visualization\map_explorer\requirements.txt
```

Double-click launchers ask in their terminal before installing missing dependencies.
If Python itself is unavailable, install Python 3.10+ first; the launcher does not
install an OS Python distribution. Neither the default launch nor in-browser
map switching requires `_tkinter`.
If executable permissions were lost when copying the Mac launcher, restore them with
`chmod +x visualization/map_explorer/launch_mac.command`.
The Windows batch wrapper is supplied but has not been executed on Windows
in this macOS development session.


### macOS first installation and recovery (β05b01 follow-up)

Install CPython from [python.org](https://www.python.org/downloads/macos/) if it
is not already installed. Extract the package into a writable local folder, then
double-click `launch_mac.command`. Answer `y` at the **one setup confirmation**.
The launcher creates/repairs only this Explorer's `.venv`, installs binary wheels,
checks native imports, and starts the bundled Mekong map. Keep Terminal open.
No Homebrew, GDAL installation, `gdal-config`, compiler, or Tk is required.
A working Python installation and network access to PyPI/files.pythonhosted.org
are prerequisites; the launcher does not install Python or bypass Gatekeeper.

| Automatic setup | Python | Interpreter architecture |
| --- | --- | --- |
| macOS 11–13 | CPython 3.10–3.12 | arm64 or x86_64 |
| macOS 14+ | CPython 3.10–3.13 | arm64 or x86_64 |

These are the automatic installer's supported combinations, subject to an
available complete wheel set. The interpreter's architecture determines pip's
wheel tags; use a native arm64 Python on Apple Silicon. Rosetta/x86_64 on Apple
Silicon has not been runtime-tested. Python 3.9, 3.14+, PyPy, older macOS and
unknown architectures receive a pre-install diagnostic instead of a source build.
Already working manually managed environments are not upgraded automatically.

**Why the old installation failed:** the ordinary `rasterio>=1.4,<1.5` requirement
also admits source releases. Pip can choose a newer source release ahead of an
older compatible wheel. Rasterio 1.4.2–1.4.4 arm64 wheels target macOS 14+, whereas
[1.4.1 has macOS 11+ arm64 wheels](https://pypi.org/project/rasterio/1.4.1/#files).
On macOS 11–13 the old installer could therefore attempt compilation and fail
because `gdal-config` was absent. Updating pip alone does not create compatible
wheels. Rasterio's [binary wheels include GDAL](https://rasterio.readthedocs.io/en/stable/installation.html).
The reported user's exact macOS version was not supplied; the failure was
reproduced on macOS 13.7.8 arm64 with CPython 3.12.3.

The macOS installer uses **`requirements-macos.txt`**: it includes the shared
requirements and requires **wheels for every dependency**. Pip can select an
older compatible release without pinning all platforms to it. For Python before
3.13 it also requires NumPy <2: macOS 11–13 may select netCDF4 1.6.5 wheels built
for the NumPy 1.x ABI, which otherwise fail during import with NumPy 2. Newer
macOS/CPython 3.13 uses newer wheels. Windows/Linux requirements and installer
commands are unchanged. Installation settings apply only to the child process:
pip config files and inherited `PIP_*`/Python-path redirections are ignored, using
the default PyPI index. They are never rewritten. A private-index-only or
custom-pip-certificate deployment needs a separately managed environment; normal
system HTTPS proxy/certificate settings remain in effect.

**Restart:** an intact local environment launches without another installation
prompt. **Failed installation:** correct the reported network/disk problem and
run the same launcher again, approving the same local setup prompt. A partial
`.venv` is reused; a module whose native extension cannot import also triggers
repair. Setup failures keep their pip diagnostic and print Python/macOS/CPU
information. No source-build retry is attempted and no GDAL installation is
suggested. If no complete wheel set exists, choose a supported interpreter/OS;
the launcher cannot make an incompatible wheel run. Symlinked `.venv` targets
and interpreter-prefix mismatches are refused to protect other environments.

For a manual **macOS-only** installation from the repository/package root:

```sh
python3 -m venv visualization/map_explorer/.venv
visualization/map_explorer/.venv/bin/python -m pip install --only-binary=:all: -r visualization/map_explorer/requirements-macos.txt
./visualization/map_explorer/launch_mac.command
```

Validation distinguishes runtime execution from wheel availability: actual clean
venv installation, server/document startup, restart and failed-install recovery
are checked on macOS 13.7.8 arm64 / CPython 3.12.3 with `gdal-config` absent from
PATH. Other supported OS/Python/CPU combinations are checked through pip's
cross-target wheel resolution, not claimed as runtime or Finder tests on those
machines. This workstation is not a freshly provisioned macOS installation.


## Operation and independent layers

The app keeps navigation, native inspection and export while separating three
independent groups. The map stays mounted on the left (about 70–75% on desktop),
with Gallery presets and Background / River / Overlays / View tabs in Visualization mode, or Inspector
on the right. Switching settings tabs never replaces the map. The right panel
scrolls independently; **Settings panel** hides/shows it. Narrow windows wrap
settings below the map. The actual Bokeh frame fits both available width and
approximately75% of browser height, reserving space for axes and the legend.
Tall maps become narrower instead of distorting geography, cropping, or requiring
internal scrolling. Coordinates/selection stay above and Legend & Diagnostics
immediately below. Resize, pan/zoom/reset and style changes retain geographic
ranges unless navigation explicitly changes them. PNG geometry remains independent
of browser dimensions. Very narrow windows may still place settings below the map.

### View: frame shape and center navigation

**Map Aspect Ratio** offers **Square (1:1)** (fresh-session default),
**Landscape (4:3)** and **Portrait (3:4)**. Ratios refer to the map frame,
using longitude × cos(midlatitude), not degree ratios. A fresh Square is the
largest centered square fitting the domain; use Full map to show all bounds.
Changing shape keeps the center and vertical span when possible, reducing scale
only to fit the available domain. The map widget remains mounted; the frame
continues to fit the available width and browser-height cap.

Manual West/East/South/North plus **Apply extent** remains authoritative and
sets **Custom**. **Full map** also chooses Custom. Pan/zoom retain the frame
preference and synchronize both extent and center fields.

**Center Longitude [°]**, **Center Latitude [°]** and **Move to Center** translate
the current view with exactly the same longitude/latitude spans. Near a domain
edge, the view shifts to the nearest fitting position and reports the adjusted
center; requests outside the regional domain are rejected without changing the
map. Complete global longitude domains retain periodic normalization.
Selection and layer settings survive translation.

Preserving exact degree spans at a new latitude conflicts with preserving an
exact physical ratio. The explicit policy is to preserve spans and requested
frame allocation and **letterbox the undistorted geographic plot within it**.
Thus the inner axes can be slightly narrower/shorter after translation; no data
stretch or hidden zoom occurs. PNG retains geographic extent/proportions rather
than browser letterboxing. JSON v2 optionally stores `viewport.aspect` and
`viewport.frame_ratio`; v1/v2 files without this object infer Custom and load
exact saved bounds, without a forced Square migration.

### Background: Raster Type → Variable

First choose **Coarse Raster** or **High-resolution Raster**, then the variable.
Only the relevant variable selector is shown. **No Background** independently
hides the raster; it does not introduce a third raster type or hide networks,
overlays or selection highlights. Each type retains its last variable when you
switch back. Raster changes keep the map mounted and preserve the viewport.

**Coarse Raster Variable** lists supported readable fields discovered by the
existing reader: uparea, basin, bsncol, subcol, coarse elevtn, ctmare, rivlen,
rivwth, rivhgt, nxtdst, grdare and rivman when supplied. Existing units/masks
remain; upstream area converts m² → km², and basin/bsncol/subcol remain discrete.
Colors are display categories, never an inferred basin identity.

**High-resolution Raster Variable** is specific to the selected tile:

| GUI variable | Existing mode | Required products / meaning |
| --- | --- | --- |
| Unit-Catchment (outlet uparea) | catchment | native catmxy plus coarse uparea; assigned coarse-cell contributing area, displayed in km² |
| Elevation (elevtn) | elevtn | native elevtn, metres |
| Floodplain Height (flddif) | flddif | native flddif and elevtn, metres; elevation supports the documented missing-fill treatment |
| Elevation Difference (8-neighbor) | difference | native elevtn; maximum valid eight-neighbor absolute elevation difference in metres, **not slope** |

The Unit-Catchment view follows Gallery p01-f04: each native pixel inherits the
uparea of its stored one-based catmx/catmy river-cell assignment. It is a
high-resolution **representation of a coarse attribute**, not an independently
computed high-resolution contributing-area field or a new catchment delineation.
Unassigned land (-999 in both records) is gray; other background/missing pixels
are white. The new menu always uses uparea for this option. Loading older JSON
that intentionally inherited another field preserves that exact rendering under
an explicit **Unit-Catchment (legacy inherited VARIABLE)** compatibility choice.

**High-resolution source** uses existing location.txt discovery, with no Mekong
or 1min path hardcoding. It also remains accessible when independent native
assignment inspection/overlays need it, including Coarse Raster or No Background.
Changing source retains a supported variable; otherwise it selects a named valid
fallback with a visible explanation, or disables the background if none exists.
Only supported choices are offered; no optional high-resolution files are needed
to start. Source changes reassess the last clicked location and replace previous geometry.
One selected tile is rendered; multi-tile mosaics remain unimplemented.

#### Background Opacity and Color Settings

**Background Opacity** is 0–100%, default 100%, in 5% steps. It multiplies
only the base raster's existing alpha: originally transparent pixels remain
transparent. At 0% the raster disappears; networks, bifurcations, ordinary
boundaries, selected grid/catchment outlines and Channel Pixels retain their
own opacity. The colorbar gradient follows Background Opacity over the same
canvas color as the raster; its numbers, tick labels and normalization remain
unchanged and readable. PNG uses the same raster/colorbar opacity rule.

One **Color Settings** section shows the active representation's controls:

- Continuous coarse fields retain their existing palettes, auto/linear/log scale
  and automatic/manual limits. Categorical fields retain discrete colors and
  disable continuous normalization with an explanation.
- Every continuous high-resolution variable has **Colormap**, **Color Scale**,
  **Automatic Color Limits**, **Color Minimum** and **Color Maximum**. Palettes:
  Gallery Default, Gray, Pale Terrain, Viridis, YlGn, YlGnBu, Terrain, Plasma,
  Magma and Blues. Changes apply immediately without applying another preset.
- Unit-Catchment uparea uses the Gallery yellow-green palette and Log km²
  rendering, with ordinary pixel-weighted P5/P95 limits. Other palettes, Linear/Log and manual km² limits affect only display;
  native catmxy, coarse uparea, catchment geometry and network remain unchanged.
- Ordinary terrain defaults use assigned-pixel full-tile P5/P95 with Gallery square-root stretch and
  subdued gray range or pale-terrain gamma. **Linear** and **Log** use their
  stated numerical normalization without Gallery stretch. Colorbars stay in
  physical metres (or inherited km²), including for Gallery's nonlinear palette
  transfer. Elevation Difference is maximum absolute eight-neighbor difference,
  in metres; it is not physical slope.

Ordinary continuous coarse limits use P5/P95 of all finite source map-cell values
in physical display units, respecting native missing masks. Terrain normally uses full-tile
P5/P95 of finite values with valid paired native catmxy indices within coarse bounds.
Inherited catchment attributes use every assigned pixel's inherited finite value,
so large pixel populations have proportionate weight. Neither viewport nor display
sampling participates. Above50million native pixels the fixed sparse native
sample described earlier supplies approximate P5/P95 instead; the viewport still
does not affect limits. Categorical identifiers retain discrete normalization.

For Log, compute percentiles **before** excluding nonpositive values, then use
`lower=P5 if P5>0 else 0.01`, `upper=P95`. If upper<=lower, show a range error and clear the
unavailable background; never manufacture a positive upper limit. Rendering masks
nonpositive pixels and saturates positive under-range values. Linear uses P5/P95;
a constant Linear field retains the existing small display-only expansion for a
usable colorbar. None of these operations changes scientific data or raw inspection.

Disable Automatic Color Limits to retain exact manual bounds. Manual Log requires
0<lower<upper; invalid minima are reported rather than reset to0.01. The automatic fallback applies only when P5<=0; positive Auto minima below0.01
and valid manual minima below0.01 are preserved. Palette Minimum/Maximum
remain independent, applied after physical normalization and any Gallery transfer;
colorbar and PNG share the same DisplayLayer. The finite reference/quantile/population
policy is cached per tile; block processing uses disposable disk workspace and may
pause on the first large-tile scan.

**Unified Auto policy (DT-0122):** Gallery presets and old JSON now use the same
valid P5/P95 population as ordinary Explorer backgrounds, including Gallery Default
scales. The optional saved `auto_limits_policy` field is accepted for compatibility
but cannot select the old coarse-extrema / P2/P98 / forced0.01 Auto calculation.
Gallery palette definitions, transfer curves and River classification remain intact;
explicit manual limits are authoritative. This is an intentional Explorer Auto-range
update; Gallery plotting scripts and canonical catalog data are unchanged.

Missing flddif with valid elevation retains its neutral, non-measured fill;
missing both remains white. Palette cropping and opacity do not create data.

Styles are retained per raster type/variable **during the session**, so coarse
elevtn edits do not overwrite uparea settings, and terrain modes remember their
own palettes, scales and limits. JSON saves the active style and both type/variable
choices; inactive profiles are not serialized and restart from defaults after a
fresh load. No display transform changes scientific source data.

**Channel Pixels Opacity** in **Overlays → Overlay Display Settings** controls
only the Channel Pixels layer from 0% (transparent) to 100% (opaque), in 5% steps.
Default is 100%. It is enabled when Channel Pixels can render and is switched on;
toggling the layer off/on retains the chosen value. Background opacity, river
vectors and selection highlights are independent. Browser and PNG use the same
RGBA alpha. JSON saves `layers.overlays.channel_pixels_opacity` as a 0–1 fraction;
older settings default to 1. Gallery presets restore the default opaque appearance.

**Channel Pixels** appears in **Overlays → Visible Overlays**, immediately
after Unit Catchment Boundaries. It is enabled only for a visible High-resolution
Raster whose selected tile has `visual`; otherwise it remains visible but disabled
with an explanation. It draws native visual=10
blue main-channel and visual=7 lavender small-stream pixels above the base raster.
With catmxy, the existing valid-assignment mask is retained; without catmxy,
visual codes can be shown but no river-cell assignment is inferred. Coarse Raster
and No Background never render this layer; switching back to high-resolution
restores the checkbox preference. The browser uses a separate image renderer
above the background and below vector/selection glyphs; toggles and raster
updates replace or clear this layer independently. These pixels are independent
of Background Opacity. Sampling may omit small features without category
averaging; the diagnostics explicitly recommend zooming in when pixels are sampled.

Enable **Unit Catchment Boundaries** in **Overlays** for native assignment-pair
edges in native COG Catchment mode, independently of Channel Pixels and displayed values.
Grid/overview/fallback modes disable it with a reason. Ordinary boundaries are omitted
in sampled views and above 100,000 visible native edges; zoom in. Selected
catchment boundaries remain independent of that display limit.

### River Network

**Network source** selects complete stored `nextxy` or Off. **Representation**
selects Grid Center, Outlet Vector (when coordinates exist), or Off. Links come
from stored indices, not traced centerlines. Outlet vectors preserve actual
`outlon/outlat`, including valid regional outlets outside coarse bounds. Only
full360° grids wrap/split longitude seams. Flexible Downstream is defined by
coarse-grid index displacement (with periodic adjacency), never vector length.

**COLOR** and **WIDTH** are independent:

- **Uniform** shows one **All Links Color** for every main link, including
  flexible links. **Connection Type** shows **Local Links Color** and
  **Flexible Links Color**. Area palette/limit controls are hidden in both.
- **Upstream Area** color hides those pickers and shows **Colormap** and area
  limits. The dropdown contains exactly **Shades_rainbow, Turbo, Blues, YlGnBu,
  plasma, Blue → Navy, Gray → Black, Gray → White**, in that order. Display labels map to `shade_rainbow`, `turbo`, `Blues`,
  `YlGnBu`, `plasma`, `blue_navy`, `gray_black`, `gray_white`. The first retains
  approved control colors; Turbo/Blues/YlGnBu/plasma use Matplotlib, and the
  three additions use explicit four-color Matplotlib gradients. Discrete classes sample the selected palette. River mode
  switches retain the chosen palette. Background palette menus are unchanged.
- **Width Mode** is Uniform or Upstream Area. Fresh sessions default to
  **Upstream Area** width and **Continuous (log scale)** mapping; without uparea,
  width defaults Uniform. **Base Line Width [px]** sets uniform width or the
  overall area-width multiplier. Thinner links render first.

The area is source-cell `uparea`, converted m²→km²: **contributing drainage area,
not discharge**. Grid centers use complete valid topology; outlet vectors use
links with valid stored endpoints. Periodic display pieces are counted once.
References remain fixed during pan/zoom.

**AREA MAPPING** appears when color or width uses area. **Area Scale** selects
**Log** (default) or **Linear**, independently of the Background scale.

| GUI option / saved identifier | Meaning |
| --- | --- |
| Continuous / `continuous` | Continuous normalization in the selected Linear/Log scale |
| 4 equal intervals / `quartiles` | Minimum-to-maximum range split into four equal Linear/Log intervals; not population quartiles |
| 6 equal intervals / `six_log` | Minimum-to-maximum range split into six equal Linear/Log intervals; not population sextiles |
| Fixed log range (legacy) / `fixed` | Historical fixed1–10⁶km² Log normalization and width formula; Area Scale disabled |

For N=4 or6, Linear boundaries are `min + i*(max-min)/N`. Log boundaries are
`10**(log10(min) + i*(log10(max)-log10(min))/N)` for i=0..N. A value exactly on an
interior edge enters the next interval; the maximum stays in the final interval.
Repeating source values changes counts but never the boundaries. Source-link
min/max uses the complete positive finite reference (unique native links with
valid endpoints), independent of viewport, sampled images and headwater omission.

**Automatic Area Limits** uses these full-reference physical min/max. Disable it
for finite positive **Area Minimum [km²]**/**Maximum**, max>min. For Continuous,
4 or6 intervals, these are **color-only** limits: saturation maps outside values
to endpoint colors; width retains full-reference range/classes in the selected
scale. Only legacy Fixed disables limit controls. Legend labels report physical
km² for each color/width interval, with Linear/Log explicitly identified.
Missing/nonpositive areas retain base width and neutral gray for generic colors;
no valid positive area reports an error. A constant reference stays constant,
without inventing a wider physical range. Mode switches preserve saved preferences.

**Arrow Size [px]** is0–20, step1, default0 (Off). Positive sizes change actual
main-network triangle geometry; position and direction follow stored downstream
connections in both representations. Above600 visible segments, arrowheads are
omitted with an explicit zoom-in diagnostic; all main links remain. PNG uses
the same positions/angles and converts requested pixels to Matplotlib points
at160dpi. Export and browser have comparable requested pixel sizes. Independent
bifurcation arrows/styles are untouched.

Gallery presets explicitly retain historical exceptions in the flat preset CSV:
p01-f03/f04 use Tutorial02's four blue colors (`gallery_quartiles`); f02c and
relevant f05 styles use continuous shade-rainbow colors with six width bins
(`gallery_continuous`). Generic `palette` styles use the chosen discrete palette.
Applying a preset restores its color exception, Log scale and original arrow
preference (True→7px). Explorer main-network4/6 bins now follow the equal-range
policy above, even when the serialized preset ID says quartiles. Static Gallery
scripts/figures retain their independently documented definitions and are unchanged.
Old saved/Gallery palettes outside the eight-option River menu remain rendered
under their original identifier. A visible compatibility message names that palette;
the dropdown has no active choice, rather than displaying a false substitute.
Selecting any of the eight explicitly replaces it. Saved JSON preserves the actual
loaded palette until replacement. Gallery historical colors also remain explicit.
Changing Colormap, Mapping or Area Scale releases that exception and marks the preset custom;
individual changes never silently replace the scientific method registry.

The added River gradients use linear RGB interpolation through explicit controls:
Blue → Navy: #5E88BE / #4F80BF / #285A9B / #103A70; Gray → Black:
#BDBDBD / #969696 / #525252 / #111111; Gray → White:
#777777 / #A0A0A0 / #CCCCCC / #F5F5F5. They work through the existing Continuous,
4-equal and6-equal interval mappings in either selected scale. Manual color
limits never change the full-reference width range. Changing
these palettes leaves network geometry and width mapping untouched. Background
palettes and the approved shade_rainbow controls are unchanged.

JSON remains v2. `network_options.area_scale` is `linear` or `log` (old files
default Log). Serialized `quartiles` and `six_log` identifiers are retained for
compatibility but mean4/6 equal value-range intervals in the selected scale.
Loading an older four-class file reports the changed class convention.
`network_options.area_limits` is null for automatic, or physical
`[min,max]`; `area_color_style` is `palette`, `gallery_quartiles` or
`gallery_continuous`. Existing `classification`, colors, width and palette fields
remain. Old files infer historical four-color/f02 palette definitions; old booleans
`layers.arrows` map False→0 / True→7px. New files store numerical
`layers.arrow_size` (and compatible boolean). Explicit saved modes override fresh
session defaults. v1 and v2/v3-created v2 files remain supported.

### Overlays

**Visible Overlays** groups Unit Catchment Boundaries, Bifurcation Channel,
Bifurcation Overland, Outlets, Headwater Guides and Coarse Grid, with Channel Pixels
immediately after Unit Catchment Boundaries.
**Overlay Display Settings** follows below with boundary/bifurcation colors,
base width and Channel Width mapping, and outlet size. Irrelevant controls stay
visible but disabled, retaining saved styles when visibility is toggled.
Channel Pixels is grouped here; its high-resolution-only rendering condition remains.

Each overlay remains independent of the background and main-network style:

- **Unit Catchment Boundaries** draws native catmx/catmy assignment-pair edges.
  **Unit Catchment Boundary Color**, default `#4A4A4A` (0.65px), changes only these ordinary
  solid boundaries. It never changes the selected catchment's orange solid
  outline, selected computational rectangle, network or bifurcations. Native
  geometry and sampling/performance limits remain as documented above.
- **Bifurcation Channel** draws **dashed** stored paths whose first-layer width
  is positive. **Bifurcation Overland** draws **dotted** paths with first-layer
  width zero; its separate color and uniform base width remain. Neither style
  redefines endpoints, direction or scientific classification.
- **Bifurcation Channel Width** replaces the ambiguous Bif Classes checkbox.
  **Uniform** applies **Base Bifurcation Width [px]** directly. **Channel Width**
  multiplies it by the existing four full-reference log-width quantile classes,
  derived from positive stored first-layer width in metres. This represents
  channel geometry, **not discharge or upstream contributing area**. The selector
  is disabled when Channel is off. Overland never inherits these classes.
- **Outlets** uses actual stored outlon/outlat hollow-circle positions.
  **Outlet Size [px]**,0–20 step1/default4, is disabled when Outlets is off.
  Zero hides ordinary outlets while preserving selected-cell/catchment markers.
  The existing20000-visible-marker safeguard reports omissions explicitly.
- **Headwater** draws visible-window native assignment centroids to stored outlets
  for positive-uparea cells with no incoming full-model-grid links. These guides are
  not confirmed physical headwaters/channels. They support COG/Global at native
  detail, cache bounded windows, and defer wide/downsampled views without scanning
  the full high-res source. Centroid scope and periodic behavior are detailed above.
- **Coarse Grid** draws every native computational edge from params.txt only
  while both displayed map spans are below30 cells. At30 or more cells on either
  axis, the entire grid overlay is hidden: lines are never thinned. Span is the
  displayed width/height clipped to map bounds divided by native resolution, so
  panning a fixed-size view does not toggle visibility (except at domain edges).
  Tiny rounding tolerance accommodates printed minute-resolution metadata.
  Bokeh's adaptive degree-tick graticules are disabled; axes/ticks remain.
  This is the computational grid (Japan1min; Mekong15min), not the high-resolution
  catmxy pixel grid. Selected Grid rectangles and irregular catchment outlines
  remain independent; PNG uses the same all-or-none edge geometry.

PNG uses the same typed overlay geometry/color/width/style. Channel dash6/3px
and Overland dot1/3px patterns use separate fixed-style Bokeh renderers and
matching absolute pixel patterns converted to Matplotlib points at160dpi.
Outlet diameters use the same pixel-to-point conversion, rather than fixed area.
The underlying scientific data are read-only.

JSONv2 adds optional `layers.overlays.catchment_boundary_color` and `outlet_size`.
Missing values load as gray/default4. The width selector still saves the existing
boolean `bif_classes` (False=Uniform, True=Channel Width), so old settings and CSV
Gallery classifications remain compatible. Existing CSV rows need no duplicated
style metadata: preset loading supplies the new optional defaults.

Bifurcations use the first valid record of each unique directed endpoint pair,
following Gallery f04. Reversed pairs remain distinct records. Invalid indices,
widths, outlets, duplicates and conflicting duplicate widths are reported.
No stored record is changed. Bifurcation link picking is deferred; rendering,
class distinctions, unique counts and error diagnostics are implemented.

### Navigation, native inspection and export

Use drag-pan, wheel zoom, box zoom, or Reset. In **View**, enter
west/east/south/north in degrees, confirm with Enter and Apply extent. Layer
changes retain the view. The viewport is taken from the browser's complete
range event, avoiding partially synchronized axis updates.

Click to select a native location. **Inspector** distinguishes coarse
indices/attributes, high-resolution indices, raw assignment codes/status,
assigned coarse-cell attributes, native elevation/flddif/visual, and the derived
elevation difference. For catchment backgrounds, orange highlights follow the
assigned coarse river cell and its selected network geometry. The clicked
geographic coordinate is retained separately. Outlet representation adds the actual
source/destination outlet coordinates. The inspector never treats display
colors or sampled images as measurements. Missing values remain explicit.

**Export current view · PNG** uses the same scene, classifications, masks and
colors with Matplotlib/Agg, including selected catchment outline/source/link, bifurcations, other
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
| p01-f03a | Coarse subcol + outlet vectors + four equal Log-area intervals |
| p01-f03b | Outlet vectors + four equal Log-area intervals + channel/overland + outlets/guides |
| p01-f04a | Unit catchments/uparea + outlet vectors + channel bifurcations |
| p01-f04b | f04a combination + channel pixels + optional assignment boundaries |
| p01-f05 | High-resolution elevation/difference/flddif + gray/pale terrain + independently styled network |

Explorer keeps scientific classes/definitions while allowing different palettes,
width scales, extents and layouts. Runtime imports no Gallery plotting module.
Tests alone load Gallery reference functions for numerical comparison. The
existing [visualization catalog](../visualization_catalog.csv) remains the
single Figure metadata registry. v3 adds only flat settings and references in
[presets.csv](presets.csv); no Gallery descriptions or variable definitions are
copied into it. Runtime reads the canonical catalog for names, explanations and
documentation links. Gallery plotting scripts remain independent.

## Gallery presets and editable settings

Select a panel in **Gallery Presets**, read its canonical scientific purpose,
and press **Apply preset**. The map updates in place, preserving its current
extent. **Apply suggested Gallery extent** is explicitly opt-in and rejected
before changes if outside this map. Missing required products are named and
Apply is disabled; there is no silent substitution of topology or terrain.
Without the shared catalog, presets are unavailable but exploration still works.

Exactly seven presets appear in the dropdown, in this order:

| Visible panel | Essential rendering |
| --- | --- |
| p01-f01a | Coarse upstream area, log YlGnBu; no network |
| p01-f01d | Pastel subcol inside valid bsncol coverage; unassigned gray, outside white; black bsncol display-class edges |
| p01-f02a | Faint log-area background (17%); nextxy local black straight links and flexible orange curved links, direction heads |
| p01-f03a | Pastel subcol and stored-outlet vectors; historical four blue area/width classes |
| p01-f03c | Gray subcol; nextxy stored-outlet vectors; continuous log shade_rainbow color with four full-reference equal Log-area width intervals |
| p01-f04b | Native catchments inheriting uparea with channel pixels and the existing f04 overlays |
| p01-f05f | Native flddif pale-terrain background with network and bifurcations |

The same CSV/library retains 15 callable IDs for compatibility with existing
scripts and saved workflows; omitted choices were not deleted or redefined.
The older supported methods include:

| Canonical panel | Essential Explorer settings |
| --- | --- |
| p01-f01a | Coarse uparea, log YlGnBu, no network |
| p01-f01c | bsncol, pastel basin display colors, no network |
| p01-f02c | Gray subcol, grid-center nextxy, continuous log shade_rainbow colors / six log width classes |
| p01-f03a | Pastel subcol, stored outlet vectors, full-network log-four equal Log-area intervals / direction heads |
| p01-f03b | Pastel bsncol, outlet vectors, channel + overland bifurcations, outlets, guides, coarse grid |
| p01-f04a | Native assigned catchments inheriting uparea, boundaries, outlet vectors, channel bifurcations, guides, grid |
| p01-f04b | f04a plus visual 10/7 channel pixels |
| p01-f05a / f05c | Native elevtn / flddif with grayscale assigned P5/P95 stretch and area-colored outlet network |
| p01-f05d / f05f | Native elevtn / flddif with pale terrain, black outlet network and area widths |
| p01-f05e | Native maximum 8-neighbor elevation difference [m], pale terrain and black outlet network; no distance-normalized slope |

Presets are initial settings. All individual controls remain editable; deviations
show **Custom (modified from …)**. Panning alone does not mark a preset modified.
User files remain **JSON version 2**, including files created by the v3 GUI;
version 1 also loads with its original coarse/grid behavior. No schema-version
migration is forced. The optional `background_ui` object saves `raster_type`,
`coarse_variable`, `highres_variable` and `no_background`; active scientific
`layers.background`, `variable`, coarse palette/limits stay in their original fields.
Optional `layers.background_opacity` is a fraction from 0 to 1 (default 1).
Optional `layers.highres_style` holds `palette`, `scale` and `limits`: e.g.
`{"palette": "YlGnBu", "scale": "log", "limits": [100, 1000000]}`.
`limits: null` selects automatic limits; palette/scale `gallery` restore Gallery
behavior, including the legacy `terrain_palette` gray/pale choice. Older files
without these fields retain opacity 100% and infer their prior linear/log or
Gallery terrain rendering. Gallery presets set opacity/style to their documented panel values.
Legacy coarse/catchment/elevtn/flddif/difference/none values project into the new
UI. Conflicting new UI/scientific fields are rejected before mutation. Unsupported
saved high-resolution variables use an explicitly named fallback; other legacy
choices, including non-uparea catchments and linear normalization, are preserved.
Selection is ephemeral and is not serialized into user configuration.

CSV schema: `gallery_id` is a foreign key into `visualization_catalog.csv`;
`background`, `variable`, `palette`, `terrain_palette`, `background_opacity`
(fraction) and `background_method` (`default` / `subbasin_context`) set the background;
`network_source`, `representation`, `color_mode`, `width_mode`, `classification`,
`area_palette`, `area_color_style`, `line_width`, `arrows`, `flexible_color` and
`network_geometry` (`straight` / `gallery_arcs`) set the main network; flat named overlay
columns mirror the existing layer controls; `west/east/south/north` are suggested
degree bounds. Boolean fields use true/false; widths use display units. See the
header and [presets.py](code/presets.py) for allowed values. CSV is UTF-8 (BOM accepted)
and Excel-compatible, with no nested JSON fields or duplicated Figure registry.

Presets reproduce essential data/method choices, not exact published graphics.
Explorer retains full-network area normalization. f02a uses quadratic Arc3
flexible connectors (rad 0.22, 17 sampled points) in approximate physical display
coordinates, and tangent-aligned downstream heads. These are graphical connectors,
not new meandering channel geometry. Stored endpoints and local/flexible classes
are unchanged; a conservative curve hull filters the viewport. Above 600 visible
links, heads are explicitly omitted with a zoom-in diagnostic. f02c's legacy
straight connectors and static Gallery population-based class normalization can still differ. Overlay widths/heads and typography can also differ. This
preserves v2 definitions and pan-independent scientific classes. Existing f04b
retains its outlets-off preset setting; the Gallery image shows outlet squares.
Enable the independent Outlets control to display stored outlet positions. A custom edit
does not become a newly Gallery-approved method. No two-way synchronization.

## Selecting a Grid and its stored unit catchment

Selection uses the one automatic **Inspector → Point Select** status:

| Point Select | Selection method | Selected river-map Grid |
| --- | --- | --- |
| Grid | Coarse Grid geographic containment | params.txt rectangle containing the click |
| Catchment | Native catmxy assignment | river cell assigned to the exact clicked native pixel |

A high-resolution pixel can lie inside geographic Grid A while its catmxy points
to river Grid B. Grid mode selects **A** with no native read/outline. Native
Catchment mode selects **B** with B's true exposed assignment edges in the visible
window. The selected rectangle, attributes, outlet and downstream link refer to
the selected river cell. JSON v1/v2 selection hints still load, but current source
and resolution determine the effective mode.

The **Inspector** presents the selected Unit Catchment as a scientific object.
Its persistent 2×2 summary reads, in row order:

1. **Outlet coordinates**: native outlat/outlon, about five decimal places. These
   are read even when the network is drawn at grid centers; no center-coordinate
   substitute is used when native outlets are unavailable.
2. **Upstream Area [km²]**: selected coarse uparea converted from m², not ctmare.
3. **Unit Catchment ID (ix, iy)**: selected river-map pair, **1-based Fortran**.
   The identifier does not imply a rectangular catchment boundary.
4. **Clicked Location**: original geographic latitude/longitude, distinct from
   the selected river-map cell and its outlet.

The selection-method line explicitly says **High-resolution catmxy assignment**
or **Geographic coarse-grid containment**. Geometry remains visible; Connectivity
is collapsed by default and retains its expansion while selection or modes change; the old long Location & Assignment table is available under
**Advanced / Native Values**, collapsed initially. Opening/closing this section
or the profile survives new clicks; panes update without rebuilding the map.

**River and Floodplain Geometry** uses elevtn/rivwth/rivhgt in metres,
rivlen/nxtdst converted from metres to kilometres, and ctmare from m² to km².
Valid negative elevations and zeros are retained. The expandable **fldhgt [m]**
table lists **all native layers**, using NLFP from params.txt. fldhgt is the
floodplain height-profile thresholds, not simulated flooded fraction fldfrc.
Layers are labeled by native layer index; no area percentages are inferred.
Mekong supplies ten layers; other maps may have a different count. Missing
products or individual values explicitly show Unavailable.

Inspector-only reads follow the existing registry: Binary fldhgt is little-endian
Float32 in NLFP consecutive NX×NY records, x fastest, native north-to-south rows.
NetCDF validates Float32 metres, geographic axes, NLFP layer count and native
layer order, including -9999/attribute fills. Spatial dimension permutations and
coordinate reversals are normalized; inconsistent/packed products are rejected
with an Advanced diagnostic. No size-based dtype guessing or data modification.
These products are not added to the Background raster menu.

**River Network Connectivity** defines:

- **Downstream ID**: stored destination in the selected nextxy
  product, with terminal/boundary, missing, invalid and out-of-map codes explicit.
- **Total upstream Unit Catchments**: distinct supplied river-map nodes that can
  reach the selected node by following this directed product, excluding itself.
- **Direct upstream Unit Catchments**: distinct nodes whose stored destination is
  the selected node (graph in-degree). A stored self-loop contributes to direct
  in-degree, but total always excludes the selected node. Neither count is
  inferred from drainage area or restricted to the viewport.
- **Channel/Overland bifurcations**: separate **Incoming / Outgoing** counts of
  unique directed paths from Products.bifurcations, using the renderer's first-
  valid-endpoint-pair deduplication and outlet/width validity filters. Positive
  first-layer width means Channel; zero means Overland. Counts are independent
  of layer visibility and do not use line color/proximity.
- **Basin ID** is actual basin. **Subbasin ID** is shown only with a readable
  subbsn or subbsn-sample product; positive integers identify prepared segments,
  zero is unassigned. Mekong's subbsn-sample uses the documented 30000/5000 km²
  sample segmentation. subcol/bsncol are display categories, never substitutes.

Graph indices are cached per selected network product. An iterative O(N)
functional-graph pass accumulates in-degree and total counts; cycles are handled
as distinct-node components, without recursive or per-click network scans.
Counts cover the **supplied regional network**; omitted upstream connectivity
outside it can be unknown. Selecting a different stored network refreshes all
counts even when its graphic representation is Off. First loading a large graph
costs O(N) time/memory; global performance has not been certified.

Advanced retains geographic coarse indices, native pixel, catmx/catmy, source
attributes, visual code, hires elevtn/flddif, raw profile, boundary diagnostics,
color categories and network product/representation. Existing programmatic
inspect() keys remain; source outlet coordinates, fldhgt/subbsn and upstream
counts are additionally available. Selection geometry is never derived from
these formatted summaries.

The native assignment boundary is **orange (`#FF7F00`), solid, 3 px**, preserving
holes/components. The computational rectangle is **pale lavender (`#D8C8F0`),
dashed, 3px at full opacity**, without casing. Both remain visible when ordinary
Unit Catchment Boundaries are disabled and use identical browser/PNG coordinates.
The selected outlet/link stay yellow with a downstream endpoint arrow. This
supersedes earlier pink/cased presentation; selection logic is unchanged.

Resolution/source/background changes re-evaluate the last geographic click when
the automatic mode changes. Palette/opacity/network/UI changes preserve compatible
selection. Grid↔Catchment changes clear stale native geometry/fields. Selection is
not serialized; loading settings reassesses the current display resolution.

In Catchment mode, unassigned/missing/mixed/outside-tile pixels retain raw diagnostic
information and clear prior selected geometry/link. No geographic or nearest-cell
fallback is allowed. Grid mode needs no catmxy and performs no native inspection.

catmxy maps native pixels to river-map cells; nextxy defines connectivity between
those cells. A regular computational rectangle and an irregular unit catchment
are different spatial regions. Outlines visualize stored assignments, not new
watershed delineations, observed basin boundaries or recalculated flow products.
The two selection methods intentionally answer different questions: which
computational raster cell was clicked, versus which river cell owns a fine pixel.

Display rasters are sampled for speed and may miss small features. Selection
always uses the native pixel, not the displayed sample. A lazy block-wise index
scans the selected tile once, retaining sparse assignment bounding boxes/counts;
subsequent boundaries read that box with native halos. Exposed pixel edges are
merged into collinear runs without joining gaps or filling holes. Up to 24
boundaries are cached per indexed tile. Complete geometry survives off-screen;
only intersecting runs transfer to the browser. PNG export uses the **same
native coordinates**, clipped to its axes, above other layers. Use **Export
current view · PNG** in View, rather than Bokeh's canvas-only Save tool.

The first selection can pause while indexing a large tile. Index memory scales
with assigned coarse cells and extraction work with the assignment bounding box;
a highly fragmented catchment may still contain many runs. Selection covers
all matching pixels in the **selected tile**; cross-tile stitching/mosaics and
asynchronous global indexing remain unimplemented. Tile borders are explicit
limits of the stored tile geometry, not inferred drainage divides. All source
data stay read-only.

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
are retained. A Log view clips finite values below its display minimum to the
minimum color; it does not edit the native values or reveal missing pixels.
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
See [DESIGN.md](DESIGN.md), [v1 evidence](../../research/records/validation_runs/VR-0151.md) and [v2 evidence](../../research/records/validation_runs/VR-0152.md) and [v3 evidence](../../research/records/validation_runs/VR-0153.md) and [UI refinement evidence](../../research/records/validation_runs/VR-0154.md) and [Background UI evidence](../../research/records/validation_runs/VR-0155.md) and [selection-rule evidence](../../research/records/validation_runs/VR-0156.md)
and [View/palette/preset evidence](../../research/records/validation_runs/VR-0160.md)
and [scientific Inspector evidence](../../research/records/validation_runs/VR-0163.md)
for scientific conventions, executed checks and limits.

- **Missing GUI dependencies**: check `PYTHON`; install requirements into a
  chosen virtual environment. Some systems need NetCDF-C/HDF5 headers if pip
  cannot obtain a netCDF4 wheel. The launcher performs no installation.
- **Cannot open map / no supported rasters**: check params.txt and the source
  diagnostics. A missing optional file is harmless; a known file with wrong
  geometry, units, type or record count is rejected, never guessed.
- **Log limits**: all Auto paths use positive P5 (otherwise0.01) / P95 from finite values before
  Log masking. Nonpositive display values are masked; positive under-range values
  saturate. Invalid manual bounds or upper<=lower report errors; source values
  remain accessible through inspection. Gallery/legacy Auto uses this same policy.
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

## Windows Launcher (WSL)

Use `launch_windows.bat` for **native Windows Python**, or double-click
`launch_windows_wsl.cmd` for **Linux Python/Panel inside WSL + Windows default browser**.
`launch_mac.command` and `run.sh` retain their existing behavior. WSL is optional;
the launcher does not install WSL, distributions, Python or packages automatically.

Prerequisites: configured WSL distribution (`wsl --list --verbose`), Linux Python
3.10+, the Explorer requirements installed in a Linux environment, and Windows/WSL
executable interop + localhost forwarding enabled. Follow the official
[WSL commands](https://learn.microsoft.com/en-us/windows/wsl/basic-commands) and
[localhost networking](https://learn.microsoft.com/en-us/windows/wsl/networking)
guides if WSL is not ready. No administrator/firewall changes are made by this launcher.

Manual setup, **inside the selected WSL distribution**, from the repository root:

```sh
python3 -m venv "$HOME/.venvs/cmf-map-explorer"
"$HOME/.venvs/cmf-map-explorer/bin/python" -m pip install -r visualization/map_explorer/requirements.txt
```

Set `CMF_WSL_PYTHON` in **Windows** to that Linux executable path (for example
`/home/your-name/.venvs/cmf-map-explorer/bin/python`). This is a Linux path, not a
Windows `Scripts/python.exe`. Without an override the launcher probes, in order,
repository `.venv/bin/python`, Explorer `.venv/bin/python`, then Linux `python3`.
A Windows/macOS venv fails the Linux-platform probe and is skipped. The selected
runtime reports missing packages without installing anything; install requirements
manually there or set the override to a prepared environment.

Optional Windows `CMF_WSL_DISTRO` selects an installed distribution; otherwise WSL's
default is used. A repository/map accessed through `\\wsl.localhost\Distro\...` or
`\\wsl$\Distro\...` selects its owning distro; contradictory/different-distro paths
are rejected. Windows drive paths (including D:), spaces and Unicode are passed as
arguments and converted using `wslpath`; Linux paths are also accepted for the map.

```bat
visualization\map_explorer\launch_windows_wsl.cmd "D:\CaMa data\map\mekong_15min"
```

With no argument WSL starts bundled `map/mekong_15min` without a folder chooser.
Explicit Windows/Linux map paths remain supported. The map must contain a valid `params.txt`.
The minimal CMD delegates to a repository PowerShell helper; its execution-policy
bypass is process-local and does not change machine/user execution policy.

The shared desktop launcher chooses an available loopback port, runs Panel in the
foreground and waits for HTTP readiness. A Windows PowerShell helper verifies the
same URL from Windows before opening the **Windows default browser**; the Linux
browser is suppressed. No fixed port is assumed, occupied ports/processes are not
replaced, and no public listener is opened. Keep the terminal open; **Ctrl-C** stops
the server. Closing the console provides best-effort process termination; Ctrl-C is
preferred. If startup fails, the CMD retains the error for inspection.

Troubleshooting: check `wsl --list --quiet`, distro initialization and
`CMF_WSL_DISTRO`; check the chosen Linux Python/version/requirements; check map
`params.txt`; check Windows-executable interop and WSL localhost forwarding when
Windows cannot reach the printed URL. The server stays in the terminal if browser
opening fails. No automatic port forwarding or firewall modification is attempted.
A small OS bind race remains between port reservation and Panel binding; a startup
error is reported if another process takes it. WSL double-click/browser/lifecycle
execution has **not been verified on a real Windows host** in the macOS development session.

## Session Pins and comparison

In **Inspector**, use **Pins** below the existing scientific sections. Select a valid
Grid or assigned Catchment, enter an optional name (Enter commits text), and click
**Add Pin**. Empty names get `Pin 1`, `Pin 2`, …; Unicode is supported. Stable IDs are
independent of names. The same target/mode/source selects the existing Pin instead
of making a duplicate. An invalid/unassigned Catchment cannot be pinned.

Markers show the **original clicked longitude/latitude**, never an inferred outlet.
Labels combine A/B/… with the first28 name characters; lists/CSV retain the full name.
Active markers are larger/purple; other Pins are teal. Rename changes display only.
Delete removes only that Pin, marker and comparison column, retaining the ordinary
current selection. Choose a Pin from the list or click its marker to restore its
saved source and river cell when the current automatic mode is compatible. A mode
mismatch is reported; zoom to native detail or out to Grid before restoring that
Pin. A saved mode never overrides current resolution. An off-screen Pin recenters
the viewport while preserving its span. Coincident markers can be chosen via the
list. Restored Inspector connectivity uses the Pin's saved network product without
changing current River visibility/style. The clicked coordinate, stored outlet,
selected1-based river indices and irregular native `catmxy` boundary remain distinct.
Pins CSV adds `assigned_pixel_scope` so visible-window counts cannot be mistaken
for complete native catchment totals; prior columns remain compatible.

Pins survive background/OSM/River/overlay/preset/navigation/UI-mode changes within
this browser session. They are **not saved in visualization JSON**, persistent storage
or scientific inputs; reloading/closing the session loses Pins. Source path/size/mtime
fingerprints and exact native assignment are checked before revisit. Missing/changed
sources report an error rather than silently substituting a containing Grid. Do not
modify source datasets during a session; fingerprints are metadata checks, not full
content hashes of enormous arrays.

**Pinned Locations Comparison** sits below **Legend & diagnostics**, across the map
column. Expand it to compare parameters as rows and Pins as columns. Checkboxes
include/exclude individual Pins without deleting them; retained creation order and
accordion expansion do not depend on selection. The parameter column is sticky
inside horizontal scrolling. There is no fixed small Pin limit; tens are supported.

Values reuse the Inspector's structured read-only scientific extraction and graph
indexes. They are cached when a Pin is created, not parsed from HTML or recalculated
on rename/inclusion. Units: areas m²→km², river/downstream lengths m→km; elevations,
widths/depths in m. Stored outlet coordinates are separate from clicks. Basin and
true optional subbasin IDs retain source meaning; display-color categories never
substitute for IDs. Counts use the same regional directed-link and deduplication
rules as Inspector (total distinct upstream nodes excludes self). Expand optional
profile/native groups for all actual NLFP height layers and genuine high-res values;
inherited coarse uparea is labeled separately. Missing data show Unavailable.

**Export Pins CSV** downloads/saves one row for every Pin, including excluded Pins.
**Export Comparison CSV** downloads/saves the parameter-by-Pin matrix for included
Pins only. Matrix headers contain stable IDs + marker labels + full names, so duplicate
names remain unambiguous. Both use UTF-8 BOM for Excel, proper CSV quoting and empty
missing numeric fields. CSVs go to the existing validated output directory with
collision-resistant timestamp filenames; the Pins panel reports the saved path.
Comparison CSV always includes all available profile layers and native-value rows,
even when their presentation accordions are collapsed. Pins CSV has stable scalar
identity/selection/source/geometry/connectivity columns. Neither CSV stores polygons.

PNG export includes all in-viewport Pin markers/labels at the same clicked coordinates,
independent of the lavender Grid/orange Catchment/yellow outlet/link selections.
Out-of-viewport markers are clipped. Unicode PNG labels depend on an installed CJK
font (Noto Sans CJK JP/Yu Gothic/Meiryo/Hiragino Sans are tried). As before, online OSM
is excluded from PNG with an explicit notice; scientific layers and Pins are retained.


River Map network sources now offer `nextxy` (plus Off), with no selectable
`nextxy_noedge`. All Gallery presets use complete `nextxy` connections. Old saved
settings naming nextxy_noedge load with an explicit migration notice; if nextxy is
missing, River rendering is disabled with that notice. Legacy files remain readable
by the low-level reader; source datasets are not deleted or modified.
Blue → Navy now exactly matches the p01-f04b/p01-f03a Gallery four colors:
#5E88BE, #4F80BF, #285A9B, #103A70. Both presets default to this selectable palette
with four upstream-area groups. Continuous modes interpolate those same anchors.

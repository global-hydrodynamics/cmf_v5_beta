# CaMa-Flood Interactive Map Explorer v3

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
independent groups. The map stays mounted on the left (about 70–75% on desktop),
with Gallery presets and Background / River / Overlays / Inspector / View tabs
on the right. Switching settings tabs never replaces the map. The right panel
scrolls independently; **Settings panel** hides/shows it. Narrow windows wrap
settings below the map. Geographic aspect remains corrected at the viewport
midpoint; a tall geographic extent may require page scrolling to see its south.

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
own opacity. The colorbar keeps its numerical values. PNG uses the same RGBA.

One **Color Settings** section shows the active representation's controls:

- Continuous coarse fields retain their existing palettes, auto/linear/log scale
  and automatic/manual limits. Categorical fields retain discrete colors and
  disable continuous normalization with an explanation.
- Every continuous high-resolution variable has **Colormap**, **Color Scale**,
  **Automatic Color Limits**, **Color Minimum** and **Color Maximum**. Palettes:
  Gallery Default, Gray, Pale Terrain, Viridis, YlGn, YlGnBu, Terrain, Plasma,
  Magma and Blues. Changes apply immediately without applying another preset.
- Unit-Catchment uparea defaults to the original Gallery yellow-green/log km²
  rendering. Other palettes, Linear/Log and manual km² limits affect only display;
  native catmxy, coarse uparea, catchment geometry and network remain unchanged.
- Terrain defaults retain Gallery full-tile P2/P98, square-root stretch and
  subdued gray range or pale-terrain gamma. **Linear** and **Log** use their
  stated numerical normalization without Gallery stretch. Colorbars stay in
  physical metres (or inherited km²), including for Gallery's nonlinear palette
  transfer. Elevation Difference is maximum absolute eight-neighbor difference,
  in metres; it is not physical slope.

Automatic terrain limits use full-tile P2/P98, not the zoomed viewport; catchment
limits use the full coarse attribute reference. Log uses positive reference
values and masks nonpositive **display** pixels explicitly, retaining their raw
values in native inspection. Linear accepts zero/negative terrain. Disable
Automatic Color Limits to edit finite limits with maximum strictly greater than
minimum; Log requires positive limits. Invalid input reports an error and keeps
the last valid image until corrected. An initial full-tile scan may take time;
statistics are cached, with a separate positive-only cache for Log.
Missing flddif with valid elevation retains a neutral, non-measured fill;
missing both remains white. Changing opacity never turns missing data opaque.

Styles are retained per raster type/variable **during the session**, so coarse
elevtn edits do not overwrite uparea settings, and terrain modes remember their
own palettes, scales and limits. JSON saves the active style and both type/variable
choices; inactive profiles are not serialized and restart from defaults after a
fresh load. No display transform changes scientific source data.

**Channel Pixels** appears in Background only for High-resolution Raster and
is enabled only if the selected tile has `visual`. It draws native visual=10
blue main-channel and visual=7 lavender small-stream pixels above the base raster.
With catmxy, the existing valid-assignment mask is retained; without catmxy,
visual codes can be shown but no river-cell assignment is inferred. Coarse Raster
and No Background never render this layer; switching back to high-resolution
restores the checkbox preference. Sampling may omit small features, without
category averaging. These pixels are independent of Background Opacity.

Enable **Unit Catchment Boundaries** in **Overlays** for native assignment-pair
edges on either raster type, independently of Channel Pixels and displayed values.
Missing selected catmxy disables it with a reason. Ordinary boundaries are omitted
in sampled views and above 100,000 visible native edges; zoom in. Selected
catchment boundaries remain independent of that display limit.

### River Network

**Network source** selects stored `nextxy` or `nextxy_noedge`. **Representation**
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
  limits. Palettes: viridis, plasma, magma, cividis, YlGnBu, YlGn, Blues, turbo,
  shade_rainbow. Discrete classes sample the selected palette; shade_rainbow's
  approved control colors remain unchanged.
- **Width Mode** is Uniform or Upstream Area. Fresh sessions default to
  **Upstream Area** width and **Continuous (log scale)** mapping; without uparea,
  width defaults Uniform. **Base Line Width [px]** sets uniform width or the
  overall area-width multiplier. Thinner links render first.

The area is source-cell `uparea`, converted m²→km²: **contributing drainage area,
not discharge**. Grid centers use complete valid topology; outlet vectors use
links with valid stored endpoints. Periodic display pieces are counted once.
References remain fixed during pan/zoom.

**Upstream Area Mapping** appears when color or width uses area:

| GUI option / saved identifier | Meaning |
| --- | --- |
| Continuous (log scale) / `continuous` | Continuous positive log-area normalization; recommended normal default |
| Quantiles (4 groups) / `quartiles` | 25th/50th/75th percentiles of full-reference log areas: approximately equal counts of links, not equal log intervals; four color/width classes |
| Logarithmic (6 classes) / `six_log` | Six equal log intervals, not quantiles; six palette colors and six widths in generic use |
| Fixed log range (legacy) / `fixed` | Historical fixed1–10⁶km² normalization and width formula |

**Automatic Area Limits** uses full positive source-link min/max. Disable it
for finite positive **Area Minimum [km²]** and **Area Maximum [km²]**, with max>min.
Continuous color clips outside bounds to endpoint colors; six-log color divides
these limits into six intervals. Physical links and native areas are never
removed or changed by display limits. These are **color-only limits**: area
width always keeps its full-reference normalization/classes. Quantile boundaries
always use full-reference data, and Fixed keeps its historical range; their
limit controls are disabled. Legends distinguish applied color and width ranges.
Missing/nonpositive areas retain links, using base width and neutral gray for
generic area colors (legacy fixed minimum width/color are retained). If no valid
positive area exists, selecting an area style reports an error without inventing
values. Color/width mode switches preserve palettes, limits and custom colors.

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
Applying a preset restores its exception and original arrow preference (True→7px).
Changing Colormap or Mapping releases that exception and marks the preset custom;
individual changes never silently replace the scientific method registry.

JSON remains v2. `network_options.area_limits` is null for automatic, or physical
`[min,max]`; `area_color_style` is `palette`, `gallery_quartiles` or
`gallery_continuous`. Existing `classification`, colors, width and palette fields
remain. Old files infer historical quartile/f02 colors; old booleans
`layers.arrows` map False→0 / True→7px. New files store numerical
`layers.arrow_size` (and compatible boolean). Explicit saved modes override fresh
session defaults. v1 and v2/v3-created v2 files remain supported.

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

Use drag-pan, wheel zoom, box zoom, or Reset. In **View**, enter
west/east/south/north in degrees, confirm with Enter and Apply extent. Layer
changes retain the view. The viewport is taken from the browser's complete
range event, avoiding partially synchronized axis updates.

Click to select a native location. **Inspector** distinguishes coarse
indices/attributes, high-resolution indices, raw assignment codes/status,
assigned coarse-cell attributes, native elevation/flddif/visual, and the derived
elevation difference. For catchment backgrounds, pink highlights follow the
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
| p01-f03a | Coarse subcol + outlet vectors + area quartiles |
| p01-f03b | Outlet vectors + area quartiles + channel/overland + outlets/guides |
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

All 12 presets are supported (the original 11 plus p01-f05e):

| Canonical panel | Essential Explorer settings |
| --- | --- |
| p01-f01a | Coarse uparea, log YlGnBu, no network |
| p01-f01c | bsncol, pastel basin display colors, no network |
| p01-f02c | Gray subcol, grid-center nextxy_noedge, continuous log shade_rainbow colors / six log width classes |
| p01-f03a | Pastel subcol, stored outlet vectors, full-network log-area quartiles / direction heads |
| p01-f03b | Pastel bsncol, outlet vectors, channel + overland bifurcations, outlets, guides, coarse grid |
| p01-f04a | Native assigned catchments inheriting uparea, boundaries, outlet vectors, channel bifurcations, guides, grid |
| p01-f04b | f04a plus visual 10/7 channel pixels |
| p01-f05a / f05c | Native elevtn / flddif with grayscale P2/P98 stretch and area-colored outlet network |
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
Gallery terrain rendering. Gallery presets reset opacity/style to original defaults.
Legacy coarse/catchment/elevtn/flddif/difference/none values project into the new
UI. Conflicting new UI/scientific fields are rejected before mutation. Unsupported
saved high-resolution variables use an explicitly named fallback; other legacy
choices, including non-uparea catchments and linear normalization, are preserved.
Selection is ephemeral and is not serialized into user configuration.

CSV schema: `gallery_id` is a foreign key into `visualization_catalog.csv`;
`background`, `variable`, `palette`, `terrain_palette` set the background;
`network_source`, `representation`, `color_mode`, `width_mode`, `classification`,
`area_palette`, `area_color_style`, `line_width`, `arrows` set the main network; flat named overlay
columns mirror the existing layer controls; `west/east/south/north` are suggested
degree bounds. Boolean fields use true/false; widths use display units. See the
header and [presets.py](presets.py) for allowed values. CSV is UTF-8 (BOM accepted)
and Excel-compatible, with no nested JSON fields or duplicated Figure registry.

Presets reproduce essential data/method choices, not exact published graphics.
Explorer retains straight flexible links and full-network area normalization;
f02c's Gallery curved links and f04's visible/path quartile normalization can
therefore differ. Overlay widths/heads and typography can also differ. This
preserves v2 definitions and pan-independent scientific classes. A custom edit
does not become a newly Gallery-approved method. No two-way synchronization.

## Selecting a Grid and its stored unit catchment

Selection depends on the **active raster type**, not the displayed variable:

| Active background | Selection method | Selected river-map Grid |
| --- | --- | --- |
| Coarse Raster | Coarse Grid geographic containment | params.txt rectangle containing the click |
| High-resolution Raster (all four variables) | High-resolution catmxy assignment | river cell assigned to the exact clicked native pixel |
| No Background | Coarse Grid geographic containment | same default rule as Coarse Raster |

A high-resolution pixel can lie inside geographic Grid A while its catmxy points
to river Grid B. Coarse Raster selects **A** and outlines all native pixels assigned
to A; High-resolution Raster selects **B** and outlines B's pixels. The clicked
native assignment never overrides the geographic rule in coarse/blank mode.
In either mode the selected rectangle, unit-catchment boundary, attributes,
cell/outlet marker and downstream link refer to the **same selected river cell**.
The native assignment shown for the clicked pixel can differ from that selected
cell and is explicitly labeled separately.

The Inspector shows Selection method, clicked lon/lat, clicked geographic Coarse
Grid, native pixel, raw catmx/catmy, selected river-map Grid, catchment status/
pixel count and downstream connectivity. GUI indices use **1-based (Fortran)** /
`(1-based, Fortran)`; Python row/column values remain zero-based internally.
Selected-cell attributes come only from the selected river Grid, not a different
clicked pixel's assigned Grid. Coordinates update the fixed Lon / Lat region;
there is no pointer-following coordinate Tooltip.

Prominent magenta edges show the complete native unit catchment, with holes and
components intact. A separate muted blue-gray dashed rectangle shows the selected
computational cell from params.txt. Neither substitutes for the other. Both
remain visible when general Unit Catchment Boundaries are off. PNG uses the
same two geometries plus the selected cell/outlet and downstream connection.

Changing Coarse ↔ High-resolution, including No Background, **re-evaluates the
last geographic click without another click**. The Inspector and all highlights
update to the new rule. Changing only variable, color, network, overlays, tabs
or viewport under the same rule/source preserves the selected Grid. Source/tile
changes also reassess the last clicked position; unrelated tile geometry is never
retained. Selection is not saved in JSON; loading a configuration during a session
reassesses an existing last click if its rule/source changes.

With High-resolution Raster, unassigned/missing/mixed/outside-tile pixels report
their native information and clear the previous Grid, catchment and link. Missing
catmxy reports assignment selection unavailable; **no geographic/nearest-cell
fallback** is allowed. In Coarse Raster/No Background the geographic Grid remains
selectable without catmxy, or if no pixels in the selected tile are assigned to
that Grid; only its catchment outline is unavailable, with an explicit status.

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
See [DESIGN.md](DESIGN.md), [v1 evidence](../../research/records/validation_runs/VR-0151.md) and [v2 evidence](../../research/records/validation_runs/VR-0152.md) and [v3 evidence](../../research/records/validation_runs/VR-0153.md) and [UI refinement evidence](../../research/records/validation_runs/VR-0154.md) and [Background UI evidence](../../research/records/validation_runs/VR-0155.md) and [selection-rule evidence](../../research/records/validation_runs/VR-0156.md)
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

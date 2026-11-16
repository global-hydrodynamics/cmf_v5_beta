# Interactive Map Explorer design

## v3 specification (2026-11-16, DT-0107)

Maintainer authorizes an incremental extension on clean main at 2effc881,
confirmed equal to freshly fetched origin/main. No commit/push, source-data
changes or Gallery-pipeline edits. This specification precedes implementation.

The Bokeh map and its sources remain mounted once in a stretchable left column.
The right column contains Gallery presets followed by compact settings/inspector
tabs, with independent vertical scrolling. A wrapping flex layout and a settings
visibility toggle provide a narrow-window fallback. Reparenting/recreating the
plot on tab changes is forbidden. Existing geographic aspect/range-event logic
is retained. Ordinary settings and presets preserve the view; Gallery extents
are opt-in and validated against MAP_DIR before changing controls.

presets.csv stores only canonical visualization IDs and flat Explorer settings;
titles/descriptions/scientific methods/doc links are read from the existing
visualization_catalog.csv. No copied metadata or YAML. Missing shared catalog
disables presets without preventing standalone map exploration. Each preset is
validated for required rasters, topology, outlets, bifurcations and a suitable
tile. Missing products are named; no alternate scientific products are silently
substituted. Presets initialize editable settings, not a new scientific approval.
A display-state comparison excluding extent marks subsequent edits Custom.
User JSON stays version 2, retaining v1/v2 compatibility; selection is ephemeral.

selection.py separates clicked coordinates, native fine pixel, assignment pair,
selected coarse river cell and complete catchment boundary. catmxy supplies
assignment; nextxy supplies connectivity only. Native pair equality selects all
assigned pixels, independent of the sampled browser raster and current viewport.
A lazy block-wise index of assignment bounding boxes/counts is built once per
tile, with a bounded LRU of recently extracted boundaries. Exposed N/S/E/W pixel
edges include different/missing neighbors, holes, disconnected components and
tile borders. Collinear runs merge without changing geometry. Boundary extraction
uses halos across processing blocks, never viewport clipping as delineation.

A dedicated magenta selection renderer lies above ordinary boundaries and
river links even when general catchment outlines are off. The complete geometry
is retained; only intersecting runs are transferred to the browser. PNG uses the
same complete native coordinates and clips to its axes. Palette/network/overlay
changes and pan/zoom preserve selection. Source changes clear it with an explicit
message. An unassigned/mixed/outside native pixel clears selection and reports
actual codes, without falling back to a containing coarse rectangle. Coarse
clicks keep native coarse selection; terrain clicks inspect pixels without
implicitly selecting a catchment. These outlines are stored assignments, not
new watersheds, observed boundaries or numerical preprocessing outputs.

Initial presets target p01-f01a/c, f02c, f03a/b, f04a/b and f05a/c/d/f. Small
display-only palettes implement documented pastel/subcol gray and shade-rainbow
choices independently of Gallery code. Explorer's full-network normalization,
straight flexible segments and overlay arrow/width differences remain explicit
compatibility limits rather than claims of pixel-exact Gallery reproduction.

Validation extends all v1/v2 tests with analytic exposed-edge cases, native vs
sampled click mapping, cache/view independence, missing products, preset atomicity
and viewport retention, map ownership and actual Mekong selections crossing
coarse-grid boundaries. Browser QA covers persistent desktop map, right scrolling,
presets, native selection, narrow fallback and exported selection geometry.

Earlier specifications below are retained as development history.

## v2 specification (2026-11-16, DT-0106)

Maintainer authorizes Gallery integration on the existing main checkout at
78bf975f, preserving v1 launchers/API and leaving changes uncommitted. This
specification precedes v2 implementation. Existing Gallery pipelines and all
map data remain read-only and are not runtime dependencies.

Three independent controls drive a shared scene, used by browser and PNG:
background (none/coarse/catchment/elevation/elevation difference/flddif),
main network (none/grid centers/outlets), and overlays (bifurcations, outlets,
regional headwater guides, coarse grid and true catchment boundaries).
New hires.py reads metadata and memory-mapped spatial subsets. New scene.py
combines reusable primitives; no Figure-specific pipeline is copied. The
existing reader, network, layer functions and app/controller are extended.

Verified contracts: location.txt records area ID/name, W/E/S/N, NX/NY and
spacing. catmxy is two little-endian Int16 planes, visual signed Int8; elevtn
and flddif Float32 with -9999 missing. catmxy=-999 in both planes is unassigned
land (gray), -9999 is other missing background (white); positive assignments
are one-based coarse cells. Boundaries compare both indices, never map values.
Visual 10/7 overlays are applied only to assigned river cells. Native terrain
zero/negative values are retained. Elevation difference is max absolute
8-neighbor elevation difference in metres, computed with a native 1-pixel
halo and no horizontal-distance division. It is not slope.

Terrain uses exact full-tile P2/P98 (cached on first use), square-root stretch,
gray intensity 0.16..0.58 or Gallery pale_terrain with the additional 0.4 gamma.
The tiny approved pale_terrain control table is embedded for independence,
with source attribution; no new metadata registry. Exact statistics scan bounded
chunks into temporary disk storage, not all global fields into RAM at startup.
Rendering samples native centers without averaging categories. A selected
high-resolution tile is explicit; automatic multi-tile mosaicking is deferred,
and outside the selected tile stays blank. Multiple location records and
directories are discoverable without 1min hardcoding.

Outlet geometry reads outlon/outlat aligned to params; connectivity and
local/flexible classification still follow nextxy. Straight outlet segments
are symbolic modeled connections, not observed centerlines. Full-map source
log-area quartiles match f03; six equal log intervals match f02. Continuous
log scaling and clearly labeled legacy fixed 1..1e6 km² remain separate modes.
Thin links precede thick links. Direction heads follow stored downstream,
suppressed above 600 visible segments to avoid crowding (legend reports it).

Bifurcations read integer ix/iy/jx/jy and width(layer,path) in metres. Reject
invalid indices/nonfinite or negative widths; validate stored end coordinates
when present. Unique directed endpoint pairs use the first valid record, as
f04; duplicate/conflicting records are reported, not rewritten. width[0]>0
is channel, zero is overland; width never means discharge. Channel-width
quartiles use positive first-layer log widths over the complete dataset.
Overlays use stored outlets even if main-network representation is grid-based.

Headwater guides sum native assigned pixel-center coordinates by coarse ID,
in bounded chunks over the full selected tile. Candidate cells have no incoming
regional network links, not necessarily physical headwaters. Optional products
fail with diagnostics and disable only dependent features. Native inspection
adds assignment status/indices, terrain and derived difference, distinguishing
sampled display pixels from scientific values. Pink highlighting follows the
selected geometry, including assigned catchment cells.

Settings v2 extend v1 JSON; old files migrate to legacy fixed area styling.
Unknown v2 fields warn and are ignored; unsupported versions fail clearly.
Tests extend the existing suite and compare actual Mekong arrays, classes and
derived quantities to independently loaded Gallery reference functions during
tests only. Browser QA verifies combined views and export; no claim of
scientific model validation or globally certified responsiveness.

The original v1 specification below is historical where superseded above.

Status: initial specification, 2026-11-16; DT-0105. Maintainer request authorizes
autonomous implementation on the existing checkout, without commit/push.

## Purpose and scope

Researchers need to inspect raster attributes and explicit river connectivity
without modifying scripts, maps, or running the model. A local Panel/Bokeh app
accepts only MAP_DIR. It does not import river_map modules or execute map tools.
The initial scope is coarse regular geographic CaMa-Flood maps with params.txt.
Bifurcation tables, outlet-coordinate vector maps and high-resolution layers
are deferred; their geometry and units differ from the coarse grid.

## Architecture and decisions

- map_reader.py: immutable geometry, explicit supported-file schema, lazy read
  and bounded cache. NetCDF is preferred; valid Binary fallback is reported.
- river_network.py: stored one-based nextx/nexty, local/flexible classification,
  exact line/viewport intersection. No nearest-neighbor reconstruction.
- map_layers.py: shared display transformation and Matplotlib PNG renderer.
  Export uses the same categories, colors, extent and network settings as GUI.
- app.py: per-browser-session state, Bokeh image and segment sources, Panel
  controls, tap inspection, extent entry, export and JSON settings.
- run.sh: resolves caller-relative then repository-relative MAP_DIR, selects
  explicit PYTHON / active environment / repository .venv / app-local .venv /
  python3; no installs at launch. An ignored app-local .venv is provisioned
  during development so the requested bare command works on this workstation.

Panel+Bokeh provides Python callbacks and responsive local browser interaction
without a JS application or database. Matplotlib export avoids Selenium and a
headless browser dependency. Local resources must be used for offline operation.
Serve on loopback only. Map handles are read-only and closed after each read.

## Data contracts

params.txt has eight leading numeric values: NX, NY, NLFP, resolution in degrees,
west, east, south, north. Dimensions are positive integers; bounds must agree
with spacing. Internal arrays are (north-to-south row, west-to-east column).
Centers are west+(column+0.5)*resolution, north-(row+0.5)*resolution.
Cell inspection reports Fortran indices ix=column+1, iy=row+1.

Binary storage is explicitly little-endian Float32 or Int32, X-fastest, with
independent records. Reshaping as (record,NY,NX) in C order is equivalent to the
Fortran (NX,NY,record) layout; never guess dtype from size. nextxy contains two
Int32 records. Only known filenames are supported. Unexpected sizes are errors.

NetCDF files in netcdf/ (or MAP_DIR itself) must contain named lon/lat axes and
the expected variable. Either ascending/descending axis orientation and either
(lat,lon)/(lon,lat) dimension order can be normalized if coordinates match the
params centers. Other grids are rejected. Coordinates are checked without
loading variable fields at startup. Fill attributes and known -9999 sentinels
are combined; finite zero/negative values are retained. Units must match the
schema (common textual m2 variants accepted); no silent units guessing.

Supported coarse rasters initially: uparea, basin, bsncol, elevtn, ctmare,
rivlen, rivwth, rivhgt, nxtdst, grdare, rivman. uparea/ctmare/grdare are stored
in m² and displayed in km². uparea is contributing area, not discharge; logarithmic
display masks nonpositive values only in the rendered layer. basin is identity,
bsncol is a reusable display category. Both use discrete category colors, never
continuous interpolation. flddif is a high-resolution relative-height layer;
do not pretend that it is a coarse params.txt raster.

## Connectivity and inspection

Default connectivity is nextxy; nextxy_noedge is a separately selectable product
when available. Do not silently substitute the latter for model connectivity.
Only pairs with 1<=nextx<=NX and 1<=nexty<=NY create destinations. -9999 is
missing; -9/-10 are preserved as terminal/boundary codes without assigning an
unconfirmed physical subtype. Mixed/nonpositive codes, self links and positive
out-of-map indices are reported and never indexed. A link is flexible when the
maximum absolute grid-index displacement exceeds one; periodic x adjacency is
used only for a complete 360-degree grid. Longitude seam links are split at the
map edge for display, not drawn across the whole globe. Lines show connections;
the inspector identifies source and destination with exact stored indices.
Link rendering does not require positive uparea (the stored network is primary).

## GUI and performance

Above: raster/network selectors. Tabs: Explore (map with pan/wheel zoom/box
zoom/reset, coordinates and colorbar), Display & export (styles, extent fields,
export/settings), Cell inspector (raw values, units, downstream status and
source diagnostics). This replaces the initial three-column design after an
actual narrow-browser check exposed horizontal overflow. Bokeh frame height
tracks rendered inner width and geographic aspect in a small local callback.
Panel widget callbacks schedule Bokeh model changes on the document's next
locked tick. Actual browser validation exposed partial range/palette updates
without this lock; synchronous headless tests alone did not reveal that issue.
The browser image uses explicit RGBA pixels from the same Matplotlib palette/
normalization as export, while a separate Bokeh mapper draws the colorbar.
This also avoids stale browser image mapper state after categorical/log swaps.
Layer/style changes preserve ranges. Data errors remain visible without taking
down the session. Manual extents are validated. Longitude/latitude use a local
equirectangular aspect correction at viewport midpoint (not a map projection).

Binary uses read-only memmap; NetCDF fields load on demand. A small LRU limits
retained rasters. Display takes a representative nearest cell per screen tile
when zoomed out, never averages category IDs. Inspection reads native values.
Network filtering includes segments crossing the viewport with both endpoints
outside it. Full nextxy construction still scales with total coarse grid size;
advanced global indexing/Datashader and high-resolution streaming are deferred.
No remote basemap or internet service is used.

## Validation strategy

Synthetic tests address CaMa-Flood risks: record ordering, coordinate flips and
transposition, fill handling including valid zero/negative elevation, bad grid
metadata, optional missing rasters, explicit connectivity and terminal codes,
viewport crossings and global seams. GUI programmatic checks exercise raster
switching, click inspection, ranges and PNG/settings export. Mekong integration
compares actual NetCDF and Binary rasters, checks network and export. Browser
interaction and visual QA are reported only if actually performed. Source data
hashes before/after establish read-only behavior for the tested map.

## Limits, review and extensions

No scientific data or definitions change. Existing f02 evidence confirms the
grid-displacement classification. No new scientific threshold is introduced.
Deferred: bifurcations, upstream tracing/basin selection, high-resolution flddif,
arbitrary/curvilinear grids, consolidated legacy NetCDF and global-scale GUI
performance certification. Inspect unreadable-file messages rather than assuming
a directory's presence implies every product can be displayed. Deployment in a
distributable package and dependency pins remain a future packaging task.

Investigation note: requested docs/preprocessing_code_conventions.md is absent;
the Python/Shell and test conventions in root AGENTS.md are used instead.

Implementation API references: [Panel document-lock guidance](https://panel.holoviz.org/en/docs/latest/how_to/callbacks/server.html),
[Bokeh interaction callbacks](https://docs.bokeh.org/en/latest/docs/user_guide/interaction/js_callbacks.html),
and [Bokeh image origin](https://docs.bokeh.org/en/latest/docs/reference/plotting/figure.html).

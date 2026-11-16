# Interactive Map Explorer design

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

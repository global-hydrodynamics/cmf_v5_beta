# Interactive Map Explorer design

## Unit Catchment Inspector redesign (DT-0117)

Maintainer authorizes the compact scientific Inspector and orange solid native /
subdued dashed computational selection styles, with commit and push of accumulated
Explorer work on current main. This supersedes previous no-publication requests
for these changes. Fetched origin/main remains75bc362f; no overlapping open
Issues/PRs found. Keep existing dirty work, readers/rendering/selection semantics,
source data and core model unchanged.

Use a persistent2x2 summary (native outlet lat/lon; uparea km²; selected Fortran
ix/iy identifier; original click lat/lon), method line, visible geometry and
connectivity, separate collapsed fldhgt profile and Advanced/Native Values.
Update persistent pane contents so accordion state survives clicks. The native
API/diagnostics remain available, including invalid/unassigned selections.

Add inspector-only validated fldhgt/subbsn readers, not competing raster layers.
Verified registry/CTL/converter and actual Mekong: fldhgt Float32 little endian,
NLFP records in native layer order (10 here); NetCDF(layer,lat,lon),units m,
-9999 fill. Preserve valid zero/negative values; no invented area percentages.
subbsn[-sample] Int32 positive segment IDs,0 unassigned; subcol/bsncol are not IDs.
The sample ID depends on documented30000/5000km² segmentation thresholds.

Connectivity uses the full selected regional raw nextxy arrays, independent of
viewport/outlet-coordinate validity or renderer seam splits. Precompute in-degree
and distinct total upstream counts once per product via functional-graph leaf
peeling; cycle nodes share component totals excluding themselves. Nonrecursive,
linear time/space; retain cycle diagnostics and regional external uncertainty.
Bifurcation incidence reuses Products.bifurcations first-valid directed-pair
 deduplication and valid outlet/width filters. Incoming/outgoing counts per kind
are explicit; positive first-layer width is Channel, zero is Overland.

Native boundary becomes3px#FF7F00 solid; coarse rectangle1px#888888 dashed at.65
alpha without casing. Selected outlet/link/endpoint head stay yellow. Browser
and PNG receive identical selection geometry. Validate synthetic graphs/profile
layout/unit conversions/cycles and actual Mekong/UI/PNG, then full suite and
protected data hashes before publication. No new dependency or Gallery edits.

## Selection visibility follow-up (2026-11-16)

Maintainer requests doubling the native selected outline from1.5 to3px,
retaining dashed pink. Selected outlet ring/link become yellow#FFD400 and
a15px triangle marks the stored downstream endpoint, oriented with geographic
latitude correction. Reuse selected_link data, clearing its angles together
with coordinates. PNG receives the same endpoints and orientation. Geometry,
assignment and ordinary outlet/network styles remain unchanged. This supersedes
prior selected-outline width/color notes below.

## Channel Pixels control location (2026-11-16 follow-up)

Maintainer requests moving Channel Pixels from Background to Overlays. Reuse
the same widget and saved layers.overlays.channel_pixels key, immediately after
ordinary catchment boundaries. Keep it visible but disabled with an explanation
when the background is coarse/hidden or visual is absent. Its preference survives
background switches; rendering, palettes, native visual=10/7 masks and PNG
composition remain unchanged. This supersedes earlier placement notes below.

## View controls, seven Gallery choices and selection styling (DT-0114)

Maintainer authorizes all five requested groups on main75bc362f, retaining dirty
DT-0113 work. No branch/commit/push, scientific data, model or Gallery script edits.

Add explicit four-control-color River gradients, through existing area mapping.
Group Overlay visibility before disabled-but-retained style controls. Selection
geometry stays unchanged; muted1.5px dashed pink native outline and2px bright
solid computational rectangle with dark casing are separate from ordinary layers.

Navigation helpers separate data-coordinate bounds from frame preference. New
sessions choose the largest centered Square fitting the domain. Aspect choices
preserve center/vertical span where possible, shrink to available domain when
necessary, using longitude*cos(midlatitude). Manual four-bound edits are authoritative
and become Custom. Center moves preserve exact degree spans, clamp position (not
size) inside domain, report adjusted center, and retain selection. Different latitude
makes exact spans and exact physical shape incompatible: retain a requested frame
allocation and letterbox the undistorted geographic plot inside it. Pan/zoom update
bounds/center without recursive changes. JSONv2 optional viewport object stores
aspect and frame_ratio; old files infer Custom without changing saved bounds.
The height cap remains; one plot stays mounted. State loading replaces prior navigation messages so the View panel cannot show an unrelated previous center correction. PNG uses unchanged geographic
extent and projection proportions, independent of browser letterboxing.

Visible presets are exactly f01a/f01d/f02a/f03a/f03c/f04b/f05f; retain old programmatic
IDs in the same CSV/library. Reuse canonical metadata, no copied descriptions.
f01d needs native bsncol coverage/class edges with subcol pastel display; f03c
needs nextxy outlet vectors, continuous shade colors and four quantile widths.
f02a uses faint uparea, stored local/flexible classification, curved flexible
connectors and downstream heads; existing arrow-density safeguard remains explicit.
Add flat CSV settings for these display distinctions, keeping source geometry
and palette mapping separate. Verify actual seven renders, not just IDs. The CSV uses flat background_method,
network_geometry, background_opacity and flexible_color columns; older CSVs infer
original defaults. Curved connectors retain exact source endpoints, use 17 samples
for flexible quadratic Arc3 paths and two for local links, and align direction
heads with the downstream tangent. Conservative Bezier-hull visibility avoids
missing curved bulges; full-network statistics remain pan-independent. f01d
bsncol class boundaries indicate display classes, not unique basin identities.

Current selection style supersedes earlier magenta/blue-gray styling below:
#D96BA0 dashed 1.5px native stored-assignment boundary; #E6E6E6 solid 2px
computational rectangle over #555555 3.5px casing. PNG converts pixel widths
and dash lengths at160dpi. No extraction, assignment or selected-grid rule changes.
Earlier DT-0113 sections document the superseded five-choice menu; the current
River menu appends Blue → Navy, Gray → Black and Gray → White, and retains the
same explicit named legacy compatibility behavior.


## Overlay styling and bounded map viewport (DT-0113)

Maintainer authorizes autonomous Overlay/UI refinements including exactly five
River palettes on current main75bc362f, clean and equal to fetched origin/main.
No commit/push, Gallery/source-data/model edits. Preserve selection/classifications.

Overlay records carry explicit geometry/color/width/label/dash fields. Separate
static-dash Bokeh sources avoid unsupported per-row line_dash. PNG matches dash
lengths at160dpi. Native ordinary boundaries get a color; selection stays magenta.
Channel first width>0 is dashed, zero-width Overland dotted. Existing log-width
quartiles persist behind Uniform/Channel Width labels, never applied to Overland.
Hollow outlet sizes0..20px remain independent of selection; existing density limit.
Optional JSON defaults boundary gray/outlet4px; preserve presets and old booleans.

A ReactiveHTML viewport measures available width and browser height. Constrain
actual Bokeh frame dimensions by both bounds with geographic aspect preserved at
viewport midpoint; shrink width for tall maps instead of stretching/cropping or
internal scrolling. Coordinates/selection stay above, legend below. PNG geometry
is independent of browser dimensions. Observe resizing and retain one plot/document,
ranges, pan/zoom/reset/tap. CSS-only max-height leaves an oversized Bokeh frame and
is insufficient. Browser checks must cover wide/tall/zoomed/smaller desktop views.

River's visible selector contains exactly Shades_rainbow/Turbo/Blues/YlGnBu/plasma
in that order; internal IDs shade_rainbow/turbo/Blues/YlGnBu/plasma. Keep renderer
legacy palettes for saved files/Gallery. Legacy loaded palettes remain rendered
and named in a visible message, with no active menu choice until explicitly
replaced. Never display a misleading substitute. Background palettes unchanged.
Verify exact menu order, actual colors, legacy rendering, overlay/PNG contracts,
layout/aspect/interactions and protected source hashes.


## River display controls (DT-0112)

Maintainer authorizes autonomous corrective River controls on current main,
retaining dirty DT-0109/0110/0111 work; no commit/push, data or Gallery-script edits.
Conditional color controls and source-area widths remain independent. Ordinary
sessions default to continuous log mapping and area-dependent widths. Display
color limits affect only continuous/six-log COLOR; WIDTH retains its complete
valid-link reference. Quantiles use full-reference log-area quartiles, fixed
uses historical1..1e6km²; these disable manual color limits. Link populations,
periodic topology, invalid endpoint handling and stored direction stay unchanged.

Extend area_style with validated area_limits and explicit area_color_style:
palette (generic), gallery_quartiles (Tutorial02 colors), gallery_continuous
(f02/f05 continuous color with six width classes). Flat preset CSV references
canonical Gallery IDs and declares these exceptions without duplicated descriptions.
Old saved files infer historical style; new GUI palette/mapping edits release a
Gallery exception and mark the preset custom. Color and width legends state their
separate applied references. No physical link is removed by a display limit.

Keep old public boolean arrows as a hidden adapter; True maps to old7px, False0.
Visible Arrow Size0..20px controls main-network triangles only, retaining direction
and600-visible-segment safeguard. Frame carries numerical sizes for Bokeh and
Matplotlib; export converts pixels to points using its160dpi, not a fixed marker.
JSONv2 adds optional area_limits/area_color_style and layers.arrow_size, retaining
old fields and default interpretation. Reject malformed settings before mutation.
DT-0112 supersedes earlier descriptions of fixed four-blue colors, a direction
checkbox, or quartile defaults for ordinary sessions. Verify mathematical
classes/color-width independence, presets/legacy settings,
arrow geometry/export and actual Mekong browser controls/PNG.


## Background display controls (DT-0111)

The maintainer requires four corrective controls, all verified in actual GUI:
raster-only 0–100% opacity, high-resolution-only visual channel pixels,
configurable inherited-uparea palettes, and continuous high-resolution Gallery /
linear / log normalization with automatic or manual physical limits. Preserve
background-dependent selection, all scientific source values and old defaults.
Work continues over retained uncommitted DT-0109/0110 changes, without commit/push.

A shared background_style.py validates high-resolution display options and builds
DisplayLayer palette/norm/limits used identically by Scene, browser colorbar and
PNG. Defaults reproduce existing catchment green/log and terrain full-tile P2/P98,
sqrt/gray-range/pale-gamma exactly. Custom linear/log are distinct choices; log
masks nonpositive display pixels and uses full-tile positive-reference limits.
Manual limits are finite, strictly increasing and positive when log. No viewport
normalization or scientific data mutation. Numerical normalization, palette lookup
and final image alpha are separate operations.

Keep active coarse and high-resolution controls distinct within one visible Color
Settings section. New high-resolution fields have per-variable session profiles.
Legacy coarse/terrain controls remain adapters for old JSON/public calls. Saved
JSON v2 gains optional layers.highres_style and layers.background_opacity; absent
fields infer prior behavior. Gallery presets explicitly restore original defaults.

Opacity multiplies existing base-raster alpha only, preserving transparent/missing
pixels and colorbar values. Channel pixels become a separate transparent RGBA
image above the raster, so opacity cannot fade them or vector/selection overlays.
Coarse/blank backgrounds never render them, while their stored high-res preference
is retained. High-res visual codes 10/7 preserve their meanings and prior valid
assignment mask when available; without catmxy, visual codes alone may be displayed
without inventing an assignment. Missing visual disables the high-res control.

DT-0111 supersedes the earlier fixed/hidden high-resolution color controls below.
Per-variable styles remain session-local; JSON stores only the active style.
Legacy categorical inherited fields keep their discrete palette and disable
continuous controls. Native selection state is never changed by opacity, palette,
scale or limit edits. Re-render errors keep the previous valid image; correction
clears the error. Log excludes nonpositive values from full-reference statistics
and masks them in the DisplayLayer, never in the source/inspection arrays.

Acceptance requires automated RGBA/norm/reference-limit/config/export contracts,
Mekong integration and actual browser comparisons for all four controls, with a
feature-by-feature verification matrix and honest remaining limitations.

## Background-dependent scientific selection (DT-0110)

The maintainer explicitly replaces background-independent selection with two
rules, retaining the preceding uncommitted DT-0109 UI/configuration work.
Coarse Raster and No Background select the params.txt rectangle containing the
click. High-resolution Raster (all four variables) selects the native catmxy
assignment. In either case the selected grid, its exact computational rectangle,
its stored native catchment boundary and downstream link refer to the same cell.
The clicked native assignment can differ from a coarse geographic selection and
is reported separately; it never overrides the coarse rule.

SelectionState records the method and geographic containing cell in addition
to clicked coordinate/native pixel/selected river cell/native geometry. Existing
CatchmentIndex is reused for either selected cell. No matching native pixels
or missing selected catmxy leaves a coarse selection valid without a catchment
outline. A missing/unassigned high-resolution assignment clears all selected
geometry and markers, retaining clicked/native information and last click.
There is no geographic fallback in high-resolution mode, even without catmxy.

On rule changes or tile changes, reassess the last geographic click. A variable,
palette or network change under the same rule/source preserves the grid. The
actual scientific background mode (including none) determines the rule so that
legacy/public widgets and saved configurations follow the same contract. PNG
continues to use the same SelectionState geometry as the browser. Inspector
explicitly distinguishes method, geographic containing grid, raw native codes
and selected river-map grid; selected attributes/connectivity use only that grid.
This supersedes earlier background-independent selection sections below, which
remain as historical design evidence. No boundary algorithm or source data change.

## Background hierarchy refactoring (DT-0109)

Maintainer authorizes this incremental UI/configuration task on current main
f78591bd, without commit/push. One two-stage selector chooses Coarse Raster or
High-resolution Raster, then an independent retained variable for that type.
A separate No Background toggle does not introduce a third raster type.

background_controls.py adapts the new UI to existing scientific background and
variable controls; no alternate renderer/reader or algorithm is introduced.
Coarse fields retain SCHEMA units/categorical treatment. New Unit-Catchment
means exactly p01-f04 inherited coarse uparea via catmxy, not native high-res
upstream area. Terrain retains full-tile P2/P98, sqrt and documented palette
transforms. Common Color Settings only shows applicable controls and explains
fixed/disabled transforms. Session-local profiles retain styles per variable;
JSON persists active style plus independent variable/type choices, not every
inactive profile. Existing JSON versions 1/2 (including v3-created version-2
files) remain supported with an optional background_ui extension; no forced
version migration. Legacy non-uparea catchment displays get a clearly labeled
compatibility choice instead of silently changing scientific variables.

Tile-local availability refreshes choices. A supported high-res variable is
retained; otherwise a named supported fallback is selected with explanation,
or background disabled if none exist. Missing optional products never block
startup. Source selection remains accessible for independent overlays/native
inspection even with a coarse or blank background. Selection geometry follows
the existing source-clear rules and is independent of background hierarchy.

Gallery presets still use flat canonical-ID CSV references and existing modes;
application translates them into the two-stage UI. p01-f05e (terrain maximum
8-neighbor elevation difference in metres, not slope) is added after checking
its actual catalog entry. Existing scientific algorithms/data remain unchanged.
Acceptance: UI state/availability, retained variable/style choices, legacy JSON,
all presets, exact arrays/masks compared to pre-refactor rendering, native
selection, actual Mekong modes, PNG and browser inspection.

## v3 UI refinement and background-independent selection (DT-0108)

The maintainer authorizes this incremental extension on current main bb36a2ec,
with no commit/push and all source data preserved. This supersedes only the v3
rule that coarse/terrain backgrounds do not select native assignments.

Background changes must never alter selection science: any selected tile with
catmxy resolves native clicks for every background, using existing SelectionState
and CatchmentIndex. Missing/mixed/outside-tile assignments clear the previous
selection without a containing-cell fallback. A map with no catmxy retains
explicitly labeled coarse geographic selection. Tile-source changes clear state.

General assignment boundaries move out of background raster construction into
a shared overlay step. Existing native-only and segment-count limits remain;
missing catmxy gives a diagnostic. Its control moves to Overlays, labeled Unit
Catchment Boundaries. No duplicate control/state or JSON key migration.

The assigned computational rectangle is calculated once from params geometry,
kept separately from the irregular native boundary and drawn with a dedicated
muted blue 1px dashed renderer. Both browser/PNG use the same complete rectangle
and catchment coordinates; neither is inferred from displayed colors or nextxy.
The rectangle helps explain different spatial domains; it never substitutes for
a catchment. Selection stays mounted through background/style/navigation changes.

Mousemove updates the existing fixed coordinate Div above the map; remove the
HoverTool tooltip entirely. GUI labels become Bifurcation Channel/Overland.
Inspector index labels explicitly state 1-based (Fortran); raw assignment codes,
physical click, fine pixel, selected river cell and connectivity are distinct.
Legacy programmatic result keys and saved configuration keys remain compatible.
Validation covers every background, native-vs-geographic assignment differences,
invalid pixels, missing products, independent geometry/export and actual browser.

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

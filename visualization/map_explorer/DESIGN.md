# Interactive Map Explorer design

## Current Auto-range policy — DT-0122

All continuous Auto backgrounds, including Gallery Default, presets and old JSON,
use full-reference P5/P95. Fine-grid references require valid paired native catmxy
indices bounded by the coarse map; inherited fields are pixel-weighted. Coarse
references respect native source masks. Compute percentiles before Log masking;
use lower=P5 when positive, otherwise0.01; never raise a small positive P5 to0.01.
Manual limits, discrete categories, Gallery palette/transfer and River coloring remain
unchanged. This supersedes DT-0120's P3/P97 and Gallery Auto exceptions below, which
are retained as historical design rationale. See the DT-0122 investigation at the end.

## Current map geometry metadata

`params.nml` is the authoritative v5 map geometry source. `map_reader.py` uses
the shared `map/tools/code/map_metadata.py` reader for `&GRID` (`NX`, `NY`,
`NLFP`, `RESOLUTION`) and `&DOMAIN` bounds. Legacy `params.txt` is read only
when `params.nml` is absent. Discovery, launch validation, map switching,
coarse-grid coordinates, and high-resolution tile alignment use the same
resolved geometry.

High-resolution tile inventories use Map's standard `location.csv` contract
and shared metadata reader. CSV takes precedence when both CSV and legacy
`location.txt` exist; TXT discovery remains for older Binary-only maps.

## Historical Inspector/navigation/statistics refinement (DT-0120, 2026-11-17)

Maintainer authorizes implementation, validation, commit and push on the current
feature/package-builder branch, starting at93e425d0 (equal to fetched origin).
No overlapping open Issues/PRs. Scope is Explorer UI, raster display statistics,
selection styling/summary, tests and documentation; source data/Gallery scripts
and model calculations remain read-only. Acceptance includes synthetic analytical
population tests, full Explorer regressions, actual Mekong browser/PNG checks.

Keep mounted Visualization and Inspector containers; top RadioButtonGroup toggles
visibility only. Persistent collapsed connectivity Accordion wraps the existing
connectivity pane. Simplify ordinary High-res labels without discarding internal
native diagnostics. Shared stored outlet/selected-cell attributes feed map summary.
Selected computational rectangle becomes lavender #D8C8F0/3px dashed at full alpha;
ordinary overlays and orange irregular native catchment remain independent.

Ordinary automatic limits use full-reference P3/P97, including finite zero/negative
values before Log range construction. Log low=max(P3,.01), high=P97; reject an
invalid range, never fabricate a positive upper limit. Nonpositive display values
are masked; positive values below the lower bound saturate. Manual limits remain
explicit and strictly validated. For inherited catchments, blockwise native
catmxy assignments index coarse values, yielding pixel-weighted statistics; no
coarse cells without assignments contribute. Cache policy/quantiles/population.

Explicit Gallery presets and old JSON retain a persisted gallery reference policy
for Auto/Gallery scales (old coarse extrema / terrain P2/P98 and Gallery transfer).
Selecting explicit Linear or Log uses ordinary P3/P97 even after a preset. Preserve
old normalization helpers for this documented exception, not as ordinary defaults.
JSON remains version2 with an optional auto_limits_policy field; absence means
legacy behavior, fresh sessions use percentile. Palette intervals are unchanged.


## Historical background/selection/view follow-up (DT-0119, 2026-11-17)

DT-0119 was superseded by DT-0120 above for UI/statistics/style; its original
policy superseded historical background-dependent selection and
unrestricted terrain-statistics choices below. Earlier sections remain as
scientific rationale/history, not competing current behavior. See README and
[VR-0165](../../research/records/validation_runs/VR-0165.md) for usage/evidence.

Maintainer explicitly assigns this work to feature/package-builder and requests
commit/push, overriding the attachment's publication restriction. Clean starting
HEAD1a734f7b matches fetched origin/feature/package-builder; no overlapping open
Issues/PRs. Do not change scientific datasets/core/package store/Gallery scripts.

Keep geographic plotting coordinates. Browser-only visible XYZ tiles are reprojected
by exact spherical Mercator inverse mapping per geographic output scanline; never
affinely stretch a whole Mercator tile in latitude. Browser fetch uses normal HTTP
cache/User-Agent/Referer; one visible zoom level, bounded tile count, debounced stale
requests; no prefetch/offline harvest. Provider configurable via environment. Keep
visible OSM attribution under map. Online basemap OFF by default and excluded from
local PNG, explicitly reported. Scientific layers/native clicks never reprojected.

Palette interval is separate from physical limits: physical normalization, Gallery
transfer, then range crop, then palette lookup. Categorical controls disabled. Full
[0,1] preserves previous colors; per-variable session styles and active JSON state.
Use shared range validation and preserve masks/physical colorbar labels.

Terrain full-tile block percentiles use the existing native assignment helper,
paired index bounds and finite/positive requirements. Cache includes mask policy
and coarse dimensions. Missing/unusable catmxy gives a diagnostic, not unrestricted
statistics. Inherited uparea remains a coarse attribute. Ordinary boundaries become
#4A4A4A/.65px; saved/custom colors and selected orange solid outline stay independent.

Point Select=Catchment when catmxy exists, otherwise Grid, independent of Background.
Preserve/re-resolve last click on mode changes; no invalid-assignment fallback. Old
JSON infers its prior background rule; new files save explicit mode. Native Pixel
Information is persistent/collapsed, scalar reads only: verified Binary elevtn,
uparea[km²],rivwth[m], signed catmz100 codes plus native assignment/pixel information.
No native fldhgt product is verified; show Unavailable, never substitute coarse NLFP.

Apply Aspect Ratio explicitly reruns existing center/scale fitting even with unchanged
selector; manual extents stay authoritative until explicit shape action. Keep map
mounted and bounded. Validate all features with synthetic data, actual Mekong,
actual GUI and PNG, document limitations and baseline unrelated research-link errors.

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
are explicit; positive `riv_width` is Channel, zero is Overland-only.

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
needs nextxy outlet vectors, continuous shade colors and four equal Log-range widths.
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
Current DT-0129 color limits affect Continuous/4/6 interval COLOR; WIDTH retains
its complete valid-link min/max in the selected Linear/Log scale. Legacy Fixed
uses historical1..1e6km² Log and disables manual color limits. Population quartiles
from the historical DT-0112 implementation are superseded. Link populations,
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


## Historical background display controls (DT-0111)

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

## Historical background-dependent scientific selection (DT-0110)

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
area ranges now use4/6 equal Linear/Log intervals per DT-0129, superseding the
historical f03 population-quartile match. Static Gallery scripts remain unchanged.
Continuous selected-scale mapping and legacy fixed Log1..1e6km² remain separate.
Thin links precede thick links. Direction heads follow stored downstream,
suppressed above 600 visible segments to avoid crowding (legend reports it).

Bifurcations read integer ix/iy/jx/jy, `riv_width(path)`, and optional
`ovl_width(layer,path)` in metres. Internal channel width is layer 1; overland
widths follow in layers 2 onward. Reject
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
The initial implementation supported coarse regular geographic CaMa-Flood maps
with params.txt; current v5 maps use params.nml as described above. The Explorer
reuses the shared metadata reader only for geometry and does not invoke map
preprocessing or river-map implementations.
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

Standard NetCDF files at MAP_DIR (legacy `netcdf/` files are also accepted) must contain named lon/lat axes and
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

## DT-0120 statistical and compatibility details

Ordinary Log includes finite nonpositive reference values before P3/P97; only
its rendering masks them. Positive values below the chosen lower bound saturate.
Manual positive bounds are authoritative even below0.01. A constant Linear field
retains the previous small display-only upper-bound expansion; invalid Log ranges
never use that expansion. This supersedes the preceding ordinary Log fallback
from DT-0118/0119-era controls while retaining it only for explicit Auto/Gallery
compatibility policy. Cache keys include (variable, positive-filter flag, quantiles,
assigned-pixel-v2, inherited/native population, coarse dimensions) within each Tile.
Ordinary Linear and Log share the same finite-reference cache, then resolve bounds.

Inherited uparea repeats selected coarse values at all valid assigned native pixels,
excluding nonfinite coarse values. These are pixel-frequency weights, not physical
area weights, and the genuine high-resolution uparea file is not read for this
background. catmxy provides assignment; nextxy still provides network connectivity.
The native selection geometry remains independent of background normalization.

Shared Inspector.update validates/caches stored outlets and exposes selected-cell
attributes to the map summary, even when networks are off or drawn at grid centers.
The summary does not reconstruct geometry or use click/center coordinates as outlets.
No duplicated Point Select state or plot/Inspector reconstruction is introduced.
See [VR-0166](../../research/records/validation_runs/VR-0166.md) for executed evidence.


## DT-0121 — WSL launcher and session Pins (approved implementation plan)

Maintainer requests implementation, tests, browser inspection, commit and normal push
on feature/package-builder. Reuse shared launch_desktop lifecycle; an additive Windows
WSL wrapper selects a Linux runtime and requests a Windows browser after readiness.
Do not install dependencies automatically in WSL. Native launchers remain unchanged.
Pins cache the existing Inspector's structured scientific result and original clicked
coordinate, selected grid, mode and source fingerprint. Dedicated markers and a
comparison Accordion below diagnostics do not belong to saved visualization JSON.
CSV exports use UTF-8 BOM, scalar units and unique pin headers. Revisit validates
sources and assignment before restoring selection; no geographic fallback.
Acceptance: isolated launcher and synthetic Pin tests, real Mekong browser + PNG/CSV
QA; Windows end-to-end explicitly unverified on macOS. Preserve unrelated TE-Japan
worktree deletions, scientific datasets and Gallery scripts.


### DT-0121 implementation details and limits

`pins.py` owns the Pin record, widgets, small comparison matrices and CSV serializers.
The immutable record fields persist one-based river_ix/river_iy; `cell` exposes a
zero-based row/column adapter for existing scientific functions. The existing
`Explorer.inspect` / `CellInspector.update` structured dictionary is the single
attribute source; snapshots copy it, including actual NLFP and cached graph results.
Inspector now exposes the same directed-pair bifurcation counts as numeric keys.
No HTML scraping, new scientific reader, watershed delineation or normalization
change was introduced. High-res native values remain distinct from inherited values.
Each snapshot records source path/size/mtime identity; metadata identity cannot prove
unchanged bytes if another process deliberately preserves timestamps and lengths.

Dedicated Bokeh scatter/LabelSet and Matplotlib scatter/annotations use saved click
coordinates. One map Tap callback tests marker screen-distance before ordinary
inspection, preventing a second geographic reassignment. Coincident markers use
list selection. Selection source validation precedes state mutation. Revisit uses
saved Inspector network product independently of current displayed River settings;
viewport translation reuses existing navigation. Switching ordinary selection clears
active-Pin emphasis if its mode/cell/source/click no longer matches. Pins and small
comparison tables never enter saved visualization state. Widget watcher mutations
are queued through Explorer._schedule for Bokeh document-lock ownership; the real
browser caught and verified this fix, with a corresponding regression test.

Comparison reuse is O(number of Pins × small field count), without full Scene.build,
assignment scans or graph rebuilding. Full source/native geometry is read only for
normal selection/revisit; existing catchment indexes/boundaries remain cached.
Accordion objects stay mounted. Optional subgroups contain all available native
NLFP layers and native scalar pixel fields; comparison CSV includes these regardless
of collapsed UI presentation. Missing numeric fields are None→empty CSV and never0.
No arbitrary small Pin cap is imposed; huge sessions still consume browser/matrix memory.

The additive CMD→PowerShell→WSL sh chain uses argument arrays and positional paths,
not a shell command containing user input. UNC distro ownership is checked; Windows
drives use wslpath. Linux runtime probing rejects Windows/macOS Python. Shared
launch_desktop uses no-setup mode, params validation, dynamic loopback port and an
in-process foreground Panel lifecycle. Readiness worker first probes Linux HTTP,
then Windows PowerShell verifies host localhost before Start-Process. Its generated
numeric localhost URL is encoded UTF-16LE as documented by Microsoft; no user string
enters executable script code. Cancellation stops the readiness worker on server exit.
Windows interop/localhost/network behavior requires real Windows QA; isolated tests
and static review are not evidence of a successful Windows double-click run.

Knowledge-gap review: no new scientific-definition questions; this task reuses the
existing documented attributes, masks, graph/bifurcation conventions and assignment
geometry. Windows runtime execution is a validation limitation, not a claimed result.


## DT-0152 follow-up — Cross-platform Python profile setup (2026-11-28)

This implementation extends the earlier macOS setup work to macOS, native Windows,
and WSL. On launch, the selected environment is checked with `pip check`, compiled
imports, and Panel/Bokeh model construction. A missing or incompatible environment
prompts once, then tries standard requirements, the minimal 2024 Explorer profile,
and the experimental 2022 profile in that order. A candidate is selected only after
the dependency/API smoke checks and synthetic-map `Explorer` initialization pass.

Profile environments are isolated by operating system and profile. Native Windows
uses `Scripts/python.exe`; macOS/Linux use `bin/python`. WSL environments are stored
under the WSL user's Linux home cache, not alongside or inside Windows/macOS virtual
environments. WSL retains an explicit no-setup option; its ordinary launcher now
allows the same consent-based automatic setup as the native launchers. Existing
working environments, system Python, Conda environments, and the repository root
`.venv` are not altered. macOS requires binary wheels for every profile and keeps
the historical NumPy ABI constraint. For 2024 on macOS arm64 with Python <3.13,
netCDF4 1.6.5 is selected because the 1.7.2 arm64 wheel is not available for the
supported older macOS range; other platforms retain the historical 1.7.2 pin.

The hidden `--test-setup-profile 2024` launcher option safely exercises the
standalone 2024 profile without replacing other environments. The full 2022 GUI
compatibility exercise is deferred to Cloud. On this local checkout, a synthetic
map successfully initializes and serves through the 2024 profile. The bundled
The Mekong map's `params.nml` geometry is now accepted by startup validation,
map discovery, and the internal reader. Native Windows/WSL execution remains
unverified on this macOS host.


## DT-0122 — All-background Auto P5/P95 (2026-11-17)

Maintainer requests investigation of disappearing assigned-pixel P3/P97 behavior,
replacement by P5/P95 and Log lower=0.01 only if the computed lower is nonpositive.
Approved scope: background display statistics/tests/docs on feature/package-builder;
scientific data, network coloring and manual limits remain unchanged. Investigation
found legacy Gallery branches forced Log lower=0.01 and bypassed pixel weighting.
Remove those Auto exceptions, including when loading legacy JSON/presets; retain
Gallery palettes/transfers and explicit manual limits. High-res references use full
native tiles and valid paired catmxy bounded by coarse dimensions; inherited coarse
uparea is pixel-weighted over that assignment mask. Coarse rasters use full source
finite/missing-value masks (catmxy is a separate fine-grid assignment, not a coarse
viewport filter). No positive-only filtering before computing percentiles. Validate
synthetic masks, small positive bounds, presets/JSON, actual Mekong and browser/PNG.


## DT-0123 — Startup p01-f04b with Overland bifurcations

2026-11-17 maintainer requests p01-f04b as initial display and Overland ON.
Apply through the existing create_app startup factory shared by all launchers,
reusing preset validation/application; keep the canonical preset CSV unchanged.
Use the recommended Gallery extent at startup when contained in the selected map;
otherwise retain its valid map extent. Missing required products keep the usable
base display and report an actionable startup message, rather than failing map
launch. Overland is an Explorer startup override and therefore shows Custom
(modified from p01-f04b), preserving scientific preset provenance. User-loaded
JSON/later preset applications retain their own settings; never reapply defaults.
Tests cover startup/factory, unavailable products and later saved settings.


## DT-0124 — Gallery f04 bifurcation comparison

2026-11-17 explicit correction: f04a retains Channel only, f04b adds Overland
alongside Channel. Update Gallery scripts, regenerated panels/combined/Gallery
PNG, both visualization READMEs and canonical CSV. Native bifprm first-layer
width>0 means Channel; width=0 means Overland; validate endpoints/nonnegative
finite layers and retain first valid directed pair. Keep area normalization and
all other layers unchanged. Explorer CSV references now declare f04b Overland ON;
startup no longer needs a custom override and should show the canonical preset.
This supersedes DT-0123's startup-only Overland difference. Validate path counts,
rendered geometry, unchanged panel-a output and source data, and inspect PNGs.


DT-0124 additional maintainer steering: use complete nextxy throughout p01 River
Map workflows and Explorer presets; remove nextxy_noedge from the UI while keeping
low-level data reading and explicit old-JSON migration. Align Blue→Navy anchors
with the existing Gallery quartet and select it by default for p01-f03a/f04b.
Regenerate f02/f03/f04/f05 figures and Gallery copies after source changes. This
supersedes the earlier f04-only scope: full nextxy changes the complete
connectivity and headwater/reference populations. The local f04a delta output
nevertheless remains byte-identical because its plotted local geometry is unchanged.
No scientific input file, p02 simulation-product pairing or model is modified.


## DT-0126 — Session-level dataset switching and native NetCDF

2026-11-17 maintainer approves map switching plus explicit high-resolution
NetCDF standard for TE-Japan, Mekong and global maps; commit/push on the existing
feature/package-builder branch. No data conversion/restoration/model changes.

A session-local ExplorerSession owns the persistent Map Dataset controls and a
single view host. Shallow candidate discovery uses params/MapReader metadata only.
Relative custom paths resolve from the repository root; no upload or OS-dialog
substitute is used. Load Map prepares a coherent Explorer/Scene/Inspector/Pins
bundle and validates its first raster before adopting it. Failed preparation
preserves the old bundle. Pins require explicit confirmation before successful
replacement clears them; failure/cancel retains them. Selection, map settings,
geometry and caches reset; application mode/control behavior remains. One server
creates a fresh session controller per browser; there is no global active map.

Panel host replacement removes old document models; Explorer.close cancels queued
Bokeh work, guards stale callbacks and releases reader/network/selection/tile/
Inspector caches. Session teardown registers a Bokeh-compatible one-argument
callback. No forced memmap close is used while NumPy views could still exist.
Two map bundles coexist briefly while preparing a replacement; large-map memory
peaks therefore exceed a single settled view. Individual settings edits do not
recreate the plot. The session holds no cross-map Pins or scientific values.

Startup uses bundled Mekong, script-relative and without a dialog across terminal,
macOS/native Windows/WSL/direct Python paths. Every supported map receives p01-f04b
on initial load or switching; only bundled Mekong requests the Gallery extent.
Other maps first get their complete native extent with a Custom geographic frame,
then apply p01-f04b while preserving that extent. Missing/invalid preset inputs
retain a usable coarse display and an explicit preset-status reason. Optional
Gallery methods continue to validate products/extents; JSON mismatch rejects
before any state mutation and asks for an explicit Map Dataset switch. No schema
migration; export filenames now identify the current map.

The shared high-res Tile.sample handles read-only Binary plus preferred native
NetCDF with validated dimensions/coordinate centers/orientation/types/units.
catmxx/catmyy and catmx/catmy are explicit paired aliases, never reconstructed from
geographic containment. No automatic mask/scale changes integer assignment codes;
Float32 declared fill/nonfinite values become display NaN. Native uparea m² -> km²
is explicit; inherited coarse uparea remains a separate concept. Present invalid
NC fields are unavailable, while absent optional NC fields may use legacy Binary.
Mekong visual/catmz100 remain such compatible supplements. Canonical legacy tile
keys drop the directory _nc suffix, allowing same-map old JSON to select the same
native geometry. Duplicate Binary/NC geometry must agree before merging fields.

Discovery inspects headers/1-D coordinates; NetCDF reads open/close only requested
native row/column blocks. CatchmentIndex now consumes these same native samples
rather than assuming an mmap, preserving exact exposed pixel-edge/hole/component
semantics. Existing P5/P95 assigned-pixel/inherited-area weighting and Log fallback
remain unchanged and shared with PNG. Reference statistics stay full-tile and
block processed with disk workspace, cached per Tile. No high-res statistics or
raster arrays are materialized on generic map startup. Global full-native scans
are still expensive and were not benchmarked; no regional-to-global performance
claim is made. Detailed actual-map measurements and limitations: VR-0172.


### Dataset controls on demand (2026-11-17)

The header places a session-owned Map dataset toggle beside Settings panel. Its
controls are hidden initially and mounted between the header and map/settings
content, independently of Visualization/Inspector mode. Toggling visibility does
not replace the Explorer or alter its viewport/selection. A successful dataset
switch transfers the same toggle/drawer to the new Explorer; failed mounting
restores them to the previous Explorer along with its Pins. The drawer remains
open until explicitly closed, so loading errors and Pins confirmation stay visible.
No scientific processing or settings schema changes.


### Registered categorical NetCDF units (2026-11-17)

The shared bin2nc converter correctly emits visual as signed int8 with units
`code`, per the variable CSV. Explorer must accept this categorical unit as well
as legacy `1`. The compatibility exception is limited to visual; it does not
relax catmxy assignment-unit validation or permit physical units on visual.
Integer classes and missing codes remain raw and unchanged. Invalid present
NetCDFs still do not silently fall back to Binary. Discovery is session-scoped;
restart a running server after a reader fix to rebuild its cached scene/products.


### Independent Channel Pixels opacity (2026-11-17)

Channel Pixels remains a separate RGBA image above the raster. Overlay state
channel_pixels_opacity (0–1, default1) scales only existing alpha via the shared
apply_opacity helper; it never alters visual categories, assignment masks, RGB,
background alpha, network, selection or source products. The Overlay FloatSlider
shows0–100% in5% steps and is disabled when the layer is off/unavailable, retaining
its value. Both Bokeh and Matplotlib consume the same adjusted image. JSON
validates finite nonboolean fractions; missing old keys use1 with no schema bump.
Gallery defaults use1; manual opacity marks the preset Custom as usual.


### Headwater-only main-network drawing (DT-0128, revised 2026-11-17)

The maintainer rejects the initial upstream-area ranking as too aggressive.
Current Auto marks zero-incoming-link source cells once from the complete valid
non-self nextxy graph (not the current viewport or available outlet-coordinate
subset). Native destination indices accumulate incoming counts; source-cell flags
are cached per network. Display seam pieces map back through link_index.

After straight-segment/conservative Bezier-hull clipping, count unique headwater
source cells among candidate links. Only when count > threshold (default5000),
omit links leaving flagged cells. All unflagged links remain; no area threshold,
ranking, hard remaining-link budget or iterative pruning is applied. A smaller
view restores heads when count <= threshold. This is an internal flag, not an
extra headwater point renderer or a change to the separate Headwater Guides overlay.

Bifurcation connectivity does not redefine this primary-nextxy headwater flag.
All native arrays/Inspector links, selection and full-reference color/width
classifications remain intact. Browser/PNG share retained geometry and count
notes. The River threshold control range remains1000–20000. The existing optional
network_budget JSON key now stores the headwater-count trigger; auto/all values
and old-file All links compatibility are retained. Current policy supersedes the
area-cutoff implementation preserved historically in VR-0174.


### Equal value-range classes (DT-0129, 2026-11-17)

Explicit maintainer instruction replaces population-based quartiles with4/6 equal
intervals in the selected Linear/Log space. River Area Scale is independent of
Background; it controls both color and width normalization. Native full-reference
positive finite source-link min/max are cached per valid endpoint population.
Outlet views must discard Grid-center range caches. Repeated values, viewport,
sampling and headwater suppression cannot shift the bounds or class edges.

For N classes, use linspace(min,max,N+1) in Linear or linspace(log10min,log10max,N+1)
in Log then invert for physical legend labels. Interior equality enters the higher
bin, max enters N-1. Constant domains map to the first color/base width without
fabricating a range. Missing/nonpositive values keep existing semantics. Manual
color limits split the selected range while width uses its full-reference bounds.
The legacy Fixed mode remains1..1e6 Log. No scientific input/unit conversion changes.

JSON adds optional area_scale, default log for old files. Existing classification
IDs quartiles/six_log now denote4/6 equal intervals; old four-class loads disclose
the changed convention. No second preset metadata table or schema-version bump.
Presets reset Log and preserve approved palette anchors/continuous-color exceptions,
but main-network width classes use current range bins. Static Gallery scripts and
bifurcation-width population quartiles are outside this correction and untouched.


### All-or-none native computational mesh (DT-0130, 2026-11-17)

The maintainer requests binary visibility, not grid-line decimation. Coarse Grid
uses clipped displayed longitude/latitude spans divided by params resolution:
if either axis spans >=30 cells, omit the entire mesh and report why in diagnostics.
Below30 on both axes, draw every native edge within view, with no stride. This
span convention avoids toggling when a fixed-size view crosses partial cells.
A1e-5-cell threshold tolerance handles rounded minute spacing; coordinate-index
roundoff snaps only within1e-8 cells. Horizontal edges are indexed southward from
the native north edge, consistently with row indexing. Deep zoom within one cell
has no internal edge and creates no empty overlay.

Bokeh's automatic degree-tick graticules can resemble decimated computational
lines but are unrelated to params.txt; disable them while retaining axes/ticks.
Browser and PNG share the explicit overlay geometry. Selection rectangles and
stored catmxy catchment boundaries are separate renderers and remain visible.
No input arrays, scientific assignments, model behavior, saved settings or grid
resolution change. This replaces the old combined500-line omission safeguard.


## DT-0134 — COG display and resolution-aware selection (2026-11-17)

Maintainer authorizes this incremental architecture on feature/package-builder,
including commit/push. This section supersedes earlier manual Point Select,
NetCDF-first high-res and whole-tile CatchmentIndex interaction descriptions.
Model-grid NetCDF readers, river topology/classifications and native scientific
values remain unchanged. Converter/package/catalog generation is outside scope.

`hires_cog.py` is a read-only window/overview adapter. Tile discovery prefers
compatible existing numeric COGs by product before opening high-res NetCDF.
Geometry/orientation/types/band metadata/units/source filename and freshness are
checked; optional absent products have reasoned fallback. Metadata stat calls to
an NC source are not native NC reads. No rendered RGB or assignment overview is
ever a scientific input. Coarse/model-grid readers retain their original contract.
For current maps, the paired NetCDF source is resolved from the same resolution
directory declared by `location.csv` (for example `1min/1min.catmxy.nc`), while
the cached COG resides under `COG/1min/`. Legacy `_nc`-suffixed tile directories
remain discoverable from their own location metadata.

`Sampling` records native window edges, output shape, overview factor, both pixel
screen scales and actual native/decimated state. Screen size is the fitted Bokeh
frame times measured DPR (batched callbacks accept both events). Closest logarithmic
overview factor supplies display; factor1 alone does not establish native mode.
Both native pixels must span at least one physical pixel, output shape must remain
native, and compatible catmxy COG must exist. The two-million-output-pixel budget
can force Grid even on a very large display. The one disabled Point Select group
reports effective mode, never an independent manual preference. Both map header
and Inspector show reason. Current source/LOD wins over legacy JSON/Pin mode hints.
The existing plot stays mounted on style/tab changes; a dataset switch replaces
only the session's validated map as before. Drawer toggles explicitly remeasure
the frame because moving a DOM box need not trigger its ResizeObserver.

Grid mode never invokes native pixel/boundary inspection. Catchment mode resolves
exact native row/column at click, validates both one-based catmxy indices against
coarse dimensions, then reads coarse scientific attributes from the assigned cell.
`nextxy` supplies connectivity only. Invalid pairs preserve their stored codes and
clear prior selection; they do not choose a geographic/nearest river cell. Native
scalar uparea and inherited coarse uparea remain separate, with unit conversion.

`visible_catchment_boundary` reads only viewport+one native neighbor halo, compares
stored assignments and emits real exposed edges merged into collinear runs. No
viewport border is invented; true tile borders, holes and disconnected groups
are retained. Geometry is explicitly incomplete outside the visible window;
count scope is included in Inspector diagnostics, summary and Pins CSV. The old
full CatchmentIndex remains for explicit small scientific tooling/tests but is not
used in the controller. Selection source identity/extent govern geometry reuse.
The orange outline and lavender Grid rectangle use these same coordinates in PNG.

Tiles in the selected resolution family compose in lexical order; overlap clicks
use the last drawn tile. Frame color limits are the first rendered tile's full
native reference shared across images, not combined multi-tile quantiles. Native
8-neighbor difference is deferred until native detail. Centroid Headwater Guides
are disabled for COG to prevent full native scans; model-grid river links retain
existing display policy. These are explicit current limitations, not science
substitutions or future functions advertised as present.

Exact assigned-native P5/P95 is preserved with existing bounded-memory/disk
partitioning. Inherited uparea uses pixel weights, valid paired assignments and
actual coarse units. No overview statistics enter limits. Persistent tiny JSON
limit caches outside map directories include native COG/NC stat signatures,
quantiles/mask policy, coarse shape and inherited array hash. More than50million
native pixels without an exact cache requires Manual; no global cold scan starts
on a click/pan. The temporary workspace may still be large for supported tiles.
Raw values share64MiB session LRU, geometry8 windows; selected geometry caches one
current source/cell/window. Large statistic stripes do not evict active display
values. Replaced file signatures invalidate caches; closing/switching releases
session references. Freshness metadata cannot prove byte-identical provenance;
no hash exists in existing converter outputs. Malformed/disappeared active files
produce a read error; reload the map to rediscover available fallback products.

Navigation coalesces latest extent75ms under Bokeh's document lock. No busy scan or
worker races are introduced. Palette/opacity reuse values and geometry. PNG uses
the already composed screen frame and overview; Matplotlib output size is not a
request for native data. Launchers probe Rasterio along with existing modules;
macOS wheel1.4.1/GDAL3.9.2 tested, real Windows/WSL execution remains unverified.

Validation and single-trial old-NetCDF benchmark: VR-0180. The comparator is
read-only baseline d6ede25f in a temporary directory, not a switched branch.
No new scientific knowledge gap was identified: the maintainer specifies LOD and
selection semantics, while tests independently establish native units/indices/
true-edge geometry. Execution is evidence of I/O/UI contracts, not model physics.


## DT-0136 — Sparse large-tile visualization statistics (2026-11-17)

Maintainer reports that uncached Global1min native statistics block Map Dataset
loading and explicitly permits sparse sampling for visualization. This supersedes
the DT-0134 Manual-only guard for tiles above50million pixels; small-tile exact
statistics, native click/assignment interpretation and scientific inputs remain.

Tile.percentiles selects a separate sparse-patches12-16-v1 cache policy for large
tiles. Twelve equal raster strata per axis contain one centered16×16 patch each,
up to144 native windows /36,864 sampled pixels. Very small test dimensions clamp
patches/strata to native bounds. Only actual native paired catmxy bounded by coarse
dimensions participates; invalid/sea/unassigned/missing/nonfinite values are
excluded. Inherited attributes repeat the selected coarse value for every sampled
valid native pixel. Native terrain and derived difference retain their existing
units/neighbor interpretation. Approximate limits never use averaged Overview
values or the current viewport. The output is a deterministic, spatially sparse
visualization reference; patches can miss rare features and are not guaranteed
unbiased or equivalent to full-population P5/P95. It is not a physical-area statistic.

Large tiles do not allocate TemporaryFile/memmap for whole-native populations.
Existing source signatures/coarse shape/inherited content hash invalidate stored
limits; exact and approximate policies never share a cache entry. Raw sample
windows reuse the existing bounded raster cache; pan/zoom/style changes reuse
limits. Manual ranges and Linear/Log handling remain authoritative; nonpositive
reference values enter percentile estimation before the Log lower-limit policy.
Empty assignment samples still explicitly request Manual, never fabricate data.

Background controls, frame legend and PNG explicitly say approximate sparse
native P5/P95. Native Inspector/catmxy clicks and actual boundary coordinates are
unchanged. The p01-f04b method/settings remain the default; only its large-tile
Explorer display-limit estimation changes, not the Gallery script/method catalog.
No converter, scientific map/COG, package definition or model code is changed.

VR-0182 records synthetic masking/cache/manual/native-selection tests, actual
Japan→Global load with full-stat workspace/high-res NC opens forbidden, and actual
browser/PNG checks. Old exact-cache values are not presented as sparse estimates;
the new large-tile cache uses its explicit new policy key.


## DT-0137 — Endpoint markers and native-window headwater guides (2026-11-17)

Maintainer reports partial-looking Outlet Vectors and missing guides, then requests
markers for nextxy=-10. Direct Global inspection of the reported viewport finds
all235 stored visible links retained (74zero-incoming sources,below5000). No
endpoint-invalid or zero-length links occur there. Main-link omission is not
observed; the18paired(-10,-10) endpoints have no downstream line by definition.

Frame now contains a dedicated terminal-point array shared by Bokeh and PNG,
shown automatically with an active river network. A red diamond/white border at
stored outlon/outlat for Outlet Vector,or computational center for Grid Center,
marks only paired(-10,-10); missing/outlet-invalid/mixed/-9 are excluded. No inferred
connection is added. Missing actual outlets are reported rather than using centers
under an Outlet label. Inspector identifies the stored terminal code explicitly.
Regional region_cut_domain.F90 also writes paired-10 when downstream is outside
its crop. Therefore the marker is called terminal,not uniquely an inland mouth.
No scientific code definitions or source data are rewritten.

The COG-wide disable of centroid guides is replaced by bounded native-window
centroids. Full model-grid incoming counts and positive uparea define candidates,
including isolated cells with no outgoing valid link,as in the prior regional
algorithm. Read only native catmxy pixels in the intersecting raster window when
native pixels are sufficiently resolved and window≤2million. No Overview category
or sparse display-statistics sample defines guide assignment/position. Native
coordinate means are grouped by paired coarse IDs; only visible-window pixels
contribute,not undisplayed components. This explicit window scope can change with
pan/clipping and does not claim a complete catchment centroid. Global longitude
uses circular mean; split_segments handles periodic edges. Later tiles mask earlier
overlap. Stored outlets are endpoints,never an inferred flow route.

Guide arrays cache8windows by network product,extent,tile/source identity; coarse
candidate masks cache by selected stored topology. Both are released on close/map
switch. Color/overlay changes reuse geometry. Wide/downsampled views show a zoom
message and omit guides rather than scan the whole high-res tile. This supersedes
the earlier COG guide-disable and periodic-global unsupported limitations. Existing
regional complete centroids remain a low-level scientific helper; the interactive
controller no longer invokes them. Main link arrays/classes/automatic omission,
settings formats and Gallery scripts remain unchanged. VR-0183 provides exact
synthetic pair/coordinate/seam oracles and actual Global/browser/PNG evidence.


## DT-0138 — Zoom-aware -10/-9 endpoint presentation (2026-11-17)

Maintainer reports global red-diamond clutter and requests zoom-only/scaled -10
markers plus subdued -9 mouth markers. Scene applies one simple geometric rule
to both types: show only if longitude and latitude spans divided by model-grid
resolution are each≤60cells (small tolerance for metadata rounding). Wider views
produce no endpoint points and explain the zoom condition in diagnostics. This
uses coarse geometry independently of COG/display sampling; camera changes clear
both mounted point sources. No marker state is added to saved configurations.

Paired(-10,-10) retains red diamonds,reduced from10to7px. Paired(-9,-9) uses6px
muted blue #6489AE circles at70%opacity. Thin white outlines and identical shared
style constants keep Bokeh/PNG consistent. Both retain actual outlet coordinates
in Outlet Vector or computational centers in Grid Center. Raw missing/mixed pairs
are excluded; missing outlets are reported,not replaced. Network Off clears both.
No downstream connection/coastline/classification is invented. Main vectors,
headwater guides,native assignments and source science remain unchanged. This
supersedes DT-0137's always-visible10px terminal-marker presentation only.
VR-0184 records exact zoom-boundary/pair/style/position checks and real Global QA.

## Source layout

All Python implementation modules live in `code/`, including the Python
launcher and WSL browser helper. Platform launchers remain at the project root,
with metadata/configuration documents, `requirements.txt` and `presets.csv`.
Tests remain in `tests/` and import from `code/`; repository-relative map
resolution, root-local `.venv/` and `output/` are preserved. This relocation
does not change display, selection, scientific readers or settings formats.

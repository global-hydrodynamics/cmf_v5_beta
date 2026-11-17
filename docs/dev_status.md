# Development status

Development policy: [AGENTS.md](../AGENTS.md). Authoritative published registry:
`origin/main:docs/dev_status.md` in `global-hydrodynamics/cmf_v5_beta`.
Working-tree updates remain proposals until published. V4 maintenance is separate.

## Current v5 work

### Large-map sparse display limits (DT-0136, 2026-11-17)

Maintainer reports Global load blocked by uncached exact P5/P95 and explicitly
permits sparse sampling for visualization. Codex owns Explorer native-stat helper,
labels/cache/tests/docs on existing feature/package-builder. Large tiles use a
fixed bounded native sample, identified as approximate; smaller exact statistics,
manual limits, scientific assignments and source data remain unchanged.

DT-0136 complete:399 tests plus3subtests PASS;1existing Windows SKIP. Actual
Japan-to-Global cold-cache load succeeds without full-stat workspace/high-res NC
opens. Browser native Catchment/Inspector/PNG verified; original catmxy point
oracle agrees;147scientific file stats unchanged. See VR-0182.


### Automatic distributed COG resolution (DT-0135, 2026-11-17)

Maintainer requests copy-and-run s05 defaults: MERIT Hydro-derived distributed
high-res1min; J-FlwDir-derived distributed high-res15sec. Codex owns COG task
selection, shared/Mekong shell copies, focused tests and docs on existing
feature/package-builder. Default auto selects the first existing1min_nc,30sec_nc,15sec_nc directory,
coarse to fine, as the maintainer subsequently simplifies the policy. Explicit
resolutions remain authoritative; no map-name/source-family inference.
No raster algorithm, source data, COG generation or package-definition changes.

DT-0135 complete:32 tests PASS;1 unchanged memory test deselected. Copied templates
select1min/30sec/15sec and preserve explicit overrides. Actual plans choose
Global1min,Mekong1min,Japan15sec;147/149/132 source file stats unchanged. Four
shell syntax checks PASS. No actual scientific raster conversion. See VR-0181.


### Explorer COG integration (DT-0134, 2026-11-17)

Maintainer explicitly approves COG display/native interaction integration on
existing feature/package-builder, including tests/browser/benchmarks/docs and
commit/push. Codex owns Explorer reader/Tile/Scene/controller/selection/Pins
integration and tests. Preserve model-grid NetCDF science, exact assigned native
P5/P95, Gallery methods and source data. No converter/package changes or COG
regeneration. Automatic Grid for overview/decimated display; Catchment only for
compatible non-decimated native COG with catmxy. Window-only native boundaries;
bounded caches and explicit fallback. No overlapping open Issue/PR found.

DT-0134 complete:396 tests plus3 subtests PASS;1 existing Windows SKIP. Actual
Japan native7products/3pixels exact;0normal high-res NC accesses;22source SHA256
and stat snapshots unchanged. Actual browser/PNG/Mekong switch and single-trial
NetCDF baseline benchmark verified. Explicit global-stat/visible-window/centroid
limits documented. See VR-0180; unrelated user data/deletions remain excluded.

### COG known non-target skips (DT-0133, 2026-11-17)

Maintainer confirms bifprm.nc and legacy rivclim/rivpar containers are outside
conversion scope and must skip without ERROR. Codex owns converter planning,
focused tests/docs/records on existing feature/package-builder with commit/push.
Explicit exclusion reasons avoid opening or generating these inputs, even with
--force; count as SKIP and successful exit when no target errors exist. Unknown
or malformed conversion-target rasters retain failure behavior.28 focused tests
PASS;1 unchanged large-memory case deselected. Actual Mekong shell:0 PASS/50 SKIP/
0 UNSUPPORTED/0 FAIL, SUCCESS/exit0;47 COGs and source file stats unchanged.
No numeric conversion/mask/Overview algorithm changes. Details:VR-0179.

### Map format tools and NetCDF-to-COG (DT-0132, 2026-11-17)

Maintainer explicitly approves format-tool rename and new numeric COG generator
on existing feature/package-builder, including commit/push. Codex owns tracked
script_format_conv templates/Mekong copy, common converter, focused tests,
reference paths, registry usage/docs/research. Preserve untracked map workflows,
scientific values, Binary/NetCDF algorithms and all workflow_stage fields.
No Explorer COG reader, Package Builder behavior/catalog change or full Japan
conversion. Acceptance: exact chunk read-back, coordinates, multiband/NoData,
average-vs-nearest overviews, atomic/overwrite/memory and existing conversion
regressions.54 related tests plus10 subtests PASS; actual Japan four small-window
COGs pass strict validation/native bytes and preserve source hashes. Metadata-only
inspection accepts46 installed raster files; bifprm table is explicitly unsupported.
512MiB artificial plane passes320MiB RSS guard (observed162.5MiB). No concurrent
agent claims/open Issues/PRs found. Details and knowledge-gap review:VR-0178.

### gosh_test mek01/mek02 maintenance (DT-0131, 2026-11-17)

Maintainer explicitly approves minimal upkeep on existing feature/package-builder,
including commit/push. Codex owns only the two maintained Mekong runners, their
README/isolated tests and records. Keep mek01 nextxy_noedge.bin versus mek02
nextxy.nc intentionally different; retain test-mek_1deg matrices and all scientific
Namelist settings. Resolve mek01 root from script location; derive exact mek02
annual NetCDF cleanup names from CVARSOUT and configured years. Existing Restart,
log and bookkeeping cleanup unchanged. Three isolated tests PASS; before/after
Namelists byte-identical; no real model execution or data deletion. See VR-0177.

### Explorer all-or-none grid lines (DT-0130, 2026-11-17)

Maintainer requests all native computational edges below30 cells on both axes,
and no grid when either axis spans30 or more. Codex owns scene/UI/tests/docs on
approved feature/package-builder; existing commit/push scope retained. Disable
unrelated adaptive degree graticules; keep axes, selection and catchment outlines.
54 related tests PASS; real Japan29/30/31 spans and browser29/30 verified;
PNG29/30 visually inspected. Data and unrelated user changes excluded.
Details and knowledge-gap review:VR-0176.


### Explorer equal value-range classes (DT-0129, 2026-11-17)

Maintainer explicitly replaces population quartiles/sextiles with4/6 equal
intervals between min/max in selected Linear/Log space. Codex owns shared River
styles/UI/config/preset wiring/tests/docs on approved feature/package-builder;
commit/push scope retained. Separate River Area Scale; full-reference native area
extrema; manual color ranges separated from full-reference width; physical legend
labels and cache population isolation. Legacy IDs retained with disclosed new
meaning; no source-data, model, Background, static Gallery or bifurcation changes.
376 tests plus3 subtests PASS;1 Windows SKIP. Actual Japan all4 scale/class
combinations, native-value invariance, browser Linear4/Log6 and PNG verified.
Details and knowledge-gap review:VR-0175.

### Map Explorer automatic river detail (DT-0128, 2026-11-17)

Maintainer correction supersedes area-based ranking as too aggressive. Auto now
caches native zero-incoming-nextxy source-cell flags and omits only their outgoing
links when visible headwater count > threshold5000. Every non-headwater link stays;
no area ranking, recursive pruning or remaining-link target. All links opt-out and
same JSON keys retained. Native Japan oracle:52142 heads omitted;79528/131670
retained, versus previous5000. Zoom562/562 restored with255 heads.48 related tests
PASS. Scope stays Explorer display/tests/docs on feature/package-builder; data,
Inspector, selection and scientific classifications unchanged. Details VR-0174.

### Map bin2nc overwrite and high-resolution coverage fixes (DT-0127, 2026-11-17)

Maintainer reports s02 interactive y followed by converter exists/--force error.
Bounded follow-up on existing feature/package-builder: Codex fixes only per-file
Shell overwrite authorization in template/Mekong and the current untracked local
Japan copy; no scientific conversion/format change or data overwrite performed.
7 tests plus2 subtests PASS including real temporary NetCDF overwrite and skip.
Maintainer follow-up adds full-list existence preflight/count summary and one
Overwrite all prompt: Yes approves selected outputs; No/Enter retains per-file
confirmation.8 tests plus4 subtests PASS including27-file bulk overwrite and
unselected-output preservation. Updated stale CWD test fixtures and a stub that
previously ignored the converter's existing-output guard. See research/records/validation_runs/VR-0173.md.

### Map Explorer dataset switching (DT-0126, 2026-11-17)

Latest Explorer UI follow-up adds independent Channel Pixels Opacity (0–100%,
5% steps; default100%) to Overlay Display Settings, JSON and shared browser/PNG
RGBA.77 related tests PASS; actual Mekong browser100/50/0% verified. User source
products are unchanged/excluded; existing feature/package-builder publication
scope retained. Details/knowledge-gap review VR-0172.

Latest maintainer follow-up: every loaded/switched supported map defaults to
p01-f04b; only bundled Mekong uses the Gallery extent. Other maps retain their
full native extent; missing preset inputs keep usable coarse fallback/status.
19 related tests PASS; actual Japan/global/Mekong switch sequence PASS with
all3 required overlays ON. Observed loads9.52s/28.47s/0.55s; no source-data edits.
Existing feature/package-builder scope/publication retained; details VR-0172.

Follow-up: regenerated visual.nc was present but rejected because the reader
expected units1 rather than canonical CSV units code. Accept code only for visual
while retaining legacy1; assignment validation remains strict. Three installed
maps now report p01-f04b missing=[]; Mekong startup applies p01-f04b. Native
classes match direct NetCDF reads; tests/record in VR-0172. Source data unchanged;
newly user-generated NetCDFs and unrelated scripts/deletions excluded from commit.

Maintainer follow-up: place infrequently used Load Map controls behind a header
Map dataset toggle beside Settings panel; initially hidden and independent of
Visualization/Inspector modes. Existing branch and publication scope retained.

Maintainer approves in-session Map Dataset controls, bundled Mekong no-dialog
startup across launchers, coherent Explorer replacement with Pins confirmation,
JSON mismatch rejection, tests/browser/real-map checks, docs and commit/push on
existing feature/package-builder. Codex owns Explorer controller/launcher/config
and associated tests/docs/research records. No scientific data/model changes,
new branch, new server per switch or real-data generation. Start clean61dfe5f2,
equal to refreshed remote; main coordination and open Issues/PRs checked with no
overlap. Acceptance: synthetic dimensions/extents/failure/state/session tests,
actual installed TE-Japan/coarse/Inspector/PNG/browser and return to Mekong;
optional high-resolution checks with the actual products. Subsequent maintainer
steering explicitly requires high-resolution NetCDF in Japan, Mekong and global
maps. Extend native block readers/selection to prefer validated NetCDF, preserving
Binary compatibility for legacy/missing optional fields and lazy I/O; no restoration
or scientific-data changes.
Implementation complete:345 tests plus3 subtests PASS,1 real-Windows SKIP;
actual browser/Japan native17-pixel selection/Inspector/PNG/OSM/Pins/return and
lazy global coarse startup verified.433 map metadata entries unchanged.12 unrelated
inp deletions excluded. Details and knowledge-gap review: VR-0172.

### Package Additional Data Import / Diff (DT-0125, 2026-11-17)

Maintainer explicitly approves implementation, tests, documentation and commit/push
on existing `feature/package-builder`. Codex owns `package/` tools/tests/catalog,
package/design documentation and task research records. Use one catalog with an
optional exclude_patterns column; preserve six existing fields. Shared read-only
selection/comparison, one-time ordinary-file Import, two-stage conflict approval,
Git/ignore/path protections and atomic verified copies. No real-data Import,
external-store edits, assembler, scientific conversion or model changes. Acceptance:
small temporary fixtures for selection/status/interaction/safety, plus actual
read-only store Diff when available. No overlapping open repository Issues/PRs
were found; starting tree clean at3199920e, equal to refreshed project remote.
Implementation complete:28 tests PASS; real symlinked-store read-only Diff and
Dry-run select273 source-only files (1811422147 bytes); independent inventory
and330 source metadata checks pass. No real Import or assembler. See VR-0171.

### Explorer UI and statistics (DT-0120, 2026-11-17)

Maintainer authorizes the six UI/Inspector/P3-P97/selection refinements, automated
and actual browser/PNG validation, commit and push on existing feature/package-builder.
Owner Dai Yamazaki; Codex implements. Starting93e425d0 matches fetched origin;
open Issue/PR searches found no overlapping work. Scope: visualization/map_explorer,
related documentation and research evidence. Scientific input/model/Gallery scripts
remain unchanged. Implementation106a41aa published to feature/package-builder.
All six changes implemented;283 tests +3 subtests PASS, actual
Mekong/browser/PNG verified,248 protected hashes unchanged. Explicit Gallery/legacy
exceptions and10 pre-existing research-link failures documented. Design/acceptance:
Explorer DESIGN.md DT-0120; [VR-0166](../research/records/validation_runs/VR-0166.md).


### Explorer background, selection and view (DT-0119, 2026-11-17)

The maintainer explicitly assigns subsequent Explorer work to the existing
feature/package-builder branch after main integration and requests commit/push
at completion, overriding the attachment's no-publication instruction. Owner:
Dai Yamazaki; Codex implements/tests/publishes. Bounded scope:
visualization/map_explorer background/overlay/Inspector/view controls, relevant
map-reader usage metadata, documentation and research evidence; no scientific
data, core-model, Gallery-script or additional-data-store changes. Starting
1a734f7b equals fetched project branch; open GitHub Issue/PR overlap searches
returned none. Acceptance: synthetic contracts, complete Explorer regression,
actual Mekong native comparison, browser rendering and PNG inspection.

Implementation 60fcbee7 published to feature/package-builder; 277 tests and 3
subtests PASS, actual Mekong/browser/PNG verified, source data unchanged. Known 10
pre-existing research-link failures are documented. Evidence: [VR-0165](../research/records/validation_runs/VR-0165.md).
This branch's status remains a proposal until integrated/published through the
maintainer workflow; main is not a push target.


### Parallel research-log integration (2026-11-16)

The maintainer authorizes reconciliation of university main and local
feature/package-builder research records. Integrate main into the existing
feature branch without rewriting either history. Retain main IDs;
runoff records become DT-0118, VR-0164 and EV-0526..EV-0531. Both full histories
and measured narratives are preserved; see the commit-scoped
[ID mapping](../research/records/decisions/ADR-0013-reconcile-parallel-research-ids.md).
After reviewing the resolved state, the maintainer explicitly authorized the
merge commit and push to feature/package-builder (EV-0533). Main is not a push
target. No model/scientific or additional-data changes are part of conflict
resolution.


### Scientific Unit Catchment Inspector (DT-0117, 2026-11-16)

Maintainer authorizes Inspector redesign plus orange solid native / subdued
dashed computational highlights, and explicitly requests commit/push of completed
accumulated Explorer work on main (starting75bc362f). This supersedes prior
no-publication requests for DT-0113–0116; retain their historical work/evidence.
Owner Dai Yamazaki; Codex implements/publishes. No branch, scientific-data or
core-model changes. Added2x2 native outlet/area/Fortran-ID/click summary,
geometry/fldhgt profile, cached regional graph counts/true optional IDs,
renderer-deduplicated bifurcation incidence and persistent collapsed diagnostics.
204 PASS/0 FAIL/0 SKIP; actual browser/PNG, all10 Mekong layers and independent
1049 total/1 direct upstream check pass;251 protected hashes unchanged.
Three registry rows gain reader-usage evidence; workflow_stage unchanged.
Published implementation and accumulated DT-0113–0116 work in
[47cf2574](https://github.com/global-hydrodynamics/cmf_v5_beta/commit/47cf257492f9af53846358bbd6bc12172be972aa); origin/main verified. Existing SSH authentication used; no force-push. See
[guide](../visualization/map_explorer/README.md),
[design](../visualization/map_explorer/DESIGN.md),
[VR-0163](../research/records/validation_runs/VR-0163.md).


### Selected catchment visibility (DT-0116, 2026-11-16)

Maintainer requests double selected boundary width and yellow outlet/link with
endpoint arrow. Implemented on same main retaining prior dirty work:3px dashed
pink native boundary, yellow selected ring/link and15px downstream endpoint
triangle. Browser and PNG use same stored endpoints; no selection/data changes.
16 targeted tests PASS; Mekong228-pixel selection and PNG visually verified.
No commit/push. See [VR-0162](../research/records/validation_runs/VR-0162.md).


### Channel Pixels placement and preset labels (DT-0115, 2026-11-16)

Maintainer requests Channel Pixels in Overlays and removal of duplicate preset
ID prefixes. Codex implemented on current main retaining DT-0113/0114 work;
no commit/push. Same saved key and high-resolution rendering conditions; one
widget after Unit Catchment Boundaries, with disabled-state explanation.
Canonical Gallery text unchanged; f03c/f05f dropdown names have one ID prefix.
3 targeted tests PASS and actual browser verified. See
[VR-0161](../research/records/validation_runs/VR-0161.md).


### View controls, River gradients and seven Gallery choices (DT-0114, 2026-11-16)

Maintainer authorizes all five requested groups on current main75bc362f, equal
to freshly fetched origin/main; retained uncommitted DT-0113 work. Owner Dai
Yamazaki; Codex implements. No branch change, commit/push or scientific/Gallery
input edits. Added three River gradients (eight visible palettes), visibility-
first Overlay controls, Square/Landscape/Portrait plus Custom and exact-span
center navigation, seven visible presets with legacy IDs callable, and muted
pink dashed native / light-gray cased solid computational selection styling.
Center translation letterboxes undistorted geography when latitude changes;
old JSON retains exact extent. Inspected Gallery code and actual seven renders,
including f01d context, f02a curves and f03c continuous shade/four width groups.
186 PASS/0 FAIL/0 SKIP; actual browser menus/colors/layout/center/navigation and
PNG styles/legend verified; native64/98=228 pixels versus coarse64/97=287 pixels
independently confirmed;251 protected digests unchanged. Windows/global
performance unclaimed; existing direction-head/sampling budgets remain explicit.
See [guide](../visualization/map_explorer/README.md),
[design](../visualization/map_explorer/DESIGN.md),
[VR-0160](../research/records/validation_runs/VR-0160.md).
Local review proposal; no publication. Supersedes DT-0113's five-choice menu and
prior selected-style presentation while retaining its Overlay/height behavior.

### Overlay styles, map height and River palette menu (DT-0113, 2026-11-16)

Maintainer authorizes autonomous Overlay/UI improvements plus exact five River
palettes on current main75bc362f; initial worktree clean, equal to fetched origin/main.
Owner Dai Yamazaki; Codex implements. No commit/push, branch change, scientific
inputs, Gallery assets/scripts or model/preprocessing changes.
Implemented ordinary catchment-boundary color, explicit Channel dashed/Overland
dotted styles, Outlet0–20px, Uniform/Channel Width selector retaining stored-width
quartiles, and actual viewport-bounded geographic frame with legend below.
River menu is exactly Shades_rainbow/Turbo/Blues/YlGnBu/plasma; old palettes stay
rendered/named until replaced, Gallery colors and Background menus unchanged.
165 PASS /0 FAIL /0 SKIP; actual Mekong browser all5 palettes, mixed styles,
Outlet0/4/10/20, width modes, native295-pixel selection, pan/wheel/box/reset/tap,
tall/wide/zoom/small desktop and PNG/JSON checked. Legend bottom721px within760px
small desktop;251 protected hashes unchanged. Windows/global performance unclaimed;
extremely thin map longitude labels may crowd. See
[guide](../visualization/map_explorer/README.md),
[design](../visualization/map_explorer/DESIGN.md), and
[VR-0159](../research/records/validation_runs/VR-0159.md).
Local review proposal; changes remain uncommitted.

### River display controls (DT-0112, 2026-11-16)

Maintainer authorizes autonomous River refactoring on current main f78591bd;
Dai Yamazaki owns scope, Codex implements over retained dirty DT-0109/0110/0111.
No commit/push, branch, scientific-input, model/preprocessing or Gallery changes.
Implemented conditional color controls;9 palettes; independent color-only limits
and full-reference area widths; clearer Continuous/Quantiles/Six Log/Fixed mapping;
fresh continuous-log/area-width defaults; numerical main Arrow Size0–20px with
pixel-consistent PNG and old boolean7px migration. JSONv2/CSV presets retain
explicit historical quartile blues and continuous shade-rainbow/six-width styles.
144 PASS /0 FAIL /0 SKIP; actual Mekong browser modes/limits/classes/arrows0/5/10/20,
base width, Gallery presets, PNG and numerical JSON confirmed. All12 pre-change
Gallery main coordinate/color/width arrays exact;251 protected hashes unchanged.
See [guide](../visualization/map_explorer/README.md),
[design](../visualization/map_explorer/DESIGN.md), and
[VR-0158](../research/records/validation_runs/VR-0158.md).
Windows/global performance remain unclaimed. Local review proposal; uncommitted.

### Working Background display controls (DT-0111, 2026-11-16)

Maintainer authorizes all four corrective controls on current main f78591bd;
Dai Yamazaki owns scope, Codex implements over retained uncommitted DT-0109/0110.
No commit/push, branch, source-data, model/preprocessing or Gallery-script changes.
Implemented raster-only opacity0–100%, high-res-only visual10/7 channel image,
10 inherited-uparea/terrain palettes and Gallery/Linear/Log with automatic/manual
physical limits. Gallery defaults remain exact; native selection stays unchanged.
JSONv2 gains optional active highres_style/background_opacity; older files load.
116 PASS /0 FAIL /0 SKIP; actual Mekong browser100→30, all four requested
catchment palettes, channel restriction/restoration, elevation Linear0–50m and
Log1–50m, independent styles, GUI PNG/JSON checked. 251 protected hashes unchanged.
Windows execution/global performance remain unclaimed. See
[design](../visualization/map_explorer/DESIGN.md),
[guide](../visualization/map_explorer/README.md), and
[feature matrix/evidence VR-0157](../research/records/validation_runs/VR-0157.md).
Changes remain uncommitted for review; status is a local proposal.

### Background-dependent Grid selection (DT-0110, 2026-11-16)

Maintainer authorizes this explicit rule change on current main f78591bd with
DT-0109 still uncommitted and retained; owner Dai Yamazaki, Codex implements.
No commit/push, branch, scientific-data or model/preprocessing changes.
Coarse Raster/No Background now select geographic containing grid; every
High-resolution Raster selects native catmxy. Both use that selected cell's
native catchment, rectangle, attributes and downstream link. Inspector separates
method/geographic grid/raw assignment/selected grid. Background-rule and tile
changes reassess the last click; high-res missing assignments never fall back.
80 tests pass; actual Mekong and browser switch without re-click verified:
coarse ix64/iy97 (287 pixels) versus assigned ix63/iy97 (295 pixels). PNG geometry
matches browser selection; 251 protected files unchanged. See
[design](../visualization/map_explorer/DESIGN.md),
[guide](../visualization/map_explorer/README.md), and
[VR-0156](../research/records/validation_runs/VR-0156.md).
Changes remain uncommitted for review; this status is a local proposal.

### Map Explorer Background hierarchy (DT-0109, 2026-11-16)

Maintainer authorizes autonomous work on current main f78591bd; Dai Yamazaki
owns the scope, Codex implements. Scope: map_explorer Background UI/configuration,
existing CSV presets, tests/docs and evidence. No commit, push, branch change,
scientific renderer/data, model/preprocessing or Gallery changes.

Implemented two-stage Coarse / High-resolution Raster variable selection,
retained independent choices and session styles, applicable common Color Settings,
tile availability/fallbacks, legacy JSON projection and p01-f05e preset. Existing
native assignment selection/overlays stay independent. JSON remains version 2
with optional background_ui; active style/choices persist, inactive style profiles
remain session-local. 74 tests pass; actual Mekong modes, browser switching,
PNG and browser JSON save/reload reviewed. 251 protected files unchanged.
See [design](../visualization/map_explorer/DESIGN.md),
[guide](../visualization/map_explorer/README.md), and
[VR-0155](../research/records/validation_runs/VR-0155.md).
Changes remain uncommitted for review; this status is a local proposal.

### Map Explorer v3 UI refinement (DT-0108, 2026-11-16)

Maintainer authorizes autonomous work on current main bb36a2ec; owner Dai
Yamazaki, Codex implements. Scope: existing map_explorer app/scene/selection,
related tests, README/DESIGN and evidence. No branch change, commit, push,
Gallery/data changes or numerical preprocessing/model execution.

Implemented fixed Lon/Lat without pointer tooltip, explicit Bifurcation labels,
background-independent native assignment selection and ordinary boundary overlay,
separate dashed assigned coarse-cell rectangle in browser/PNG, and 1-based
(Fortran) inspector labels. Existing JSON keys/presets/readers remain unchanged.
61 tests pass; actual Mekong coarse/None/elevation clicks, selection retention,
Overlay labels, Inspector and exported PNG reviewed. Tile mosaics/global-scale
performance and Windows execution remain outside this validation. See
[design](../visualization/map_explorer/DESIGN.md),
[guide](../visualization/map_explorer/README.md), and
[VR-0154](../research/records/validation_runs/VR-0154.md).
Changes remain uncommitted for maintainer review; this status is a local proposal.

### Map Explorer v2 Gallery integration (DT-0106, 2026-11-16)

Maintainer authorizes autonomous extension on current `main`, starting at
`78bf975f`; Dai Yamazaki owns the project and Codex implements. Scope is the
existing map_explorer app, tests/docs and evidence. No branch change, commit,
push, Gallery modifications, map writes or model/preprocessing execution.

Implemented independent Background / River Network / Overlay controls,
metadata-discovered high-resolution tiles, inherited unit catchments, terrain
and native-neighbor elevation difference, outlet vectors, stable full-network
area quartiles/six log classes/continuous/fixed styles, direction heads,
channel/overland bifurcations, outlets, regional centroid guides and true
assignment boundaries. PNG uses the same scene; v2 JSON retains v1 loading.
Mac/Windows launchers and existing coarse-map functionality are preserved.

34 tests pass, including the original 23 and actual Mekong/Gallery comparisons.
Browser combined views, resizing, native inspection and PNG/JSON saving checked;
exported PNG visually reviewed. All 250 protected map/Gallery hashes unchanged.
Mekong has 382 unique valid bifurcations (77 channel, 305 overland). A single
local check measured startup 0.154 s, first difference/vector view 0.285 s,
and cached rendering 0.008 s; these are not global performance guarantees.
Automatic tile mosaics, bifurcation picking and periodic global centroid guides
remain deferred. See [design](../visualization/map_explorer/DESIGN.md),
[user guide](../visualization/map_explorer/README.md), and
[VR-0152](../research/records/validation_runs/VR-0152.md).
Changes remain uncommitted for maintainer review.


### Interactive Map Explorer (DT-0105, 2026-11-16)

Maintainer-requested autonomous specification/implementation/testing on the
existing `main` checkout; owner: Dai Yamazaki (maintainer), Codex implements.
Starting revision: `fc97d485`. Scope: independent read-only local browser app
under `visualization/map_explorer/`, a concise visualization-index link and
project/research evidence. No branch creation/switch, commit, push, model/map
changes or existing Figure-workflow changes. The request explicitly authorizes
proceeding from design into implementation without another approval gate.

Implemented Panel/Bokeh GUI: lazy Binary/NetCDF rasters, stored nextxy/noedge
selection, local/flexible links, pan/zoom and extent controls, 1-based native
cell inspection, area styling, Matplotlib PNG and JSON settings save/load.
The design precedes application implementation; see [DESIGN](../visualization/map_explorer/DESIGN.md)
and [user guide](../visualization/map_explorer/README.md). An ignored app-local
virtual environment is provisioned without changing the shared environment.
Mekong and synthetic tests: 23 pass. Actual browser interaction and exported
PNG were visually inspected; 105 source/data hashes remain unchanged. GUI
locking and image-color issues found during browser checks were fixed.
High-resolution rasters, bifurcations, basin tracing and global-scale performance
validation are deferred. Evidence/limits: [VR-0151](../research/records/validation_runs/VR-0151.md).
Follow-up at maintainer request: Mac `.command` and Windows `.bat` desktop
launchers select a map folder, use existing Python environments and choose an
available loopback port. Mac wrapper startup and folder-dialog console fallback
were checked; Windows execution remains unverified on this macOS workstation.
Implementation and this status proposal remain uncommitted for maintainer review.


### Repository migration consistency cleanup (DT-0104, 2026-11-15)

Maintainer-approved working branch: `main`; owner: Dai Yamazaki (maintainer),
Codex implements. Starting revision: `8d557898`. Scope: classify migration
references, correct confirmed active path/navigation errors, distinguish
historical records, remove the obsolete GitHub Actions configuration and
retain manual checks. Preserve the existing README edit. No physics, data,
reference outputs, new test framework, directory reorganization, package
assembler, commit or push is authorized. Acceptance: focused path/syntax and
existing component tests; local-link and history/data preservation checks;
no active workflow files. Implementation appeared in an external commit
`9f08956e` during validation; the agent did not commit/push. Focused root checks
and 29 existing unittest cases pass; completion records are appended for review.
Findings and manual checks are in
[the migration audit](migration_consistency_audit.md); evidence is in
[VR-0150](../research/records/validation_runs/VR-0150.md).

## Published migration baseline

Root src/gosh/adm relocation to tracked legacy/ and util consolidation into
tools/ were published in `29b889c4` (v5beta_initial_setup), inherited by current
main at `8d557898`. DT-0102 and DT-0103 documentation/research files are tracked.
Those completed moves are not pending work. Current model/configuration/run
paths are src_main/, config/, gosh_test/ and tools/. Optional etc/ and
map/src/ workflows remain legacy or require individual v5 review.

Automated GitHub Actions is temporarily disabled by this cleanup pending a
small, reproducible v5 regression suite. Tests and their reference inputs
remain; use [manual validation](migration_consistency_audit.md#manual-checks-retained-from-the-retired-workflow).

## Historical project and status snapshots

The following inherited task descriptions, old branch assignments, v4 Issues,
master refs and publication proposals describe their original coordination
context. They do not register current work on old feature branches or imply
that formerly uncommitted migrations or CI remain pending/active. Preserve
this evidence; current assignments and automation status are above.

### Development and distribution design documentation (DT-0103, 2026-11-15)

Maintainer-assigned bounded documentation task on the current `main` checkout;
owner: Dai Yamazaki (maintainer), Codex implements. Scope: install the supplied
[maintained design](development_and_distribution_design.md), align current
README/policy links and write concise external contribution guidance; append
evidence under research. Acceptance: preserve the supplied specification,
separate planned/current behavior, verify documented existing test commands,
check changed links and research records. No model/workflow implementation,
package assembler, data relocation, new tests, commit or push is authorized.
The pre-existing directory relocation and DT-0102 utility changes are preserved.
Documentation is prepared for review: original specification body preserved;
19 CTL and eight Mekong checks pass, map registry valid, local links and research
records checked. Packaging/regression acceptance choices remain in KG-0036.
See [ADR-0010](../research/records/decisions/ADR-0010-development-and-distribution.md)
and [VR-0149](../research/records/validation_runs/VR-0149.md).

### Shared utility consolidation (DT-0102)

Maintainer-assigned bounded v5-beta task on the current `main` checkout after
repository migration; owner: Dai Yamazaki (maintainer), Codex implements.
Scope: move root `util/Makefile` and `util/igetday.F90` directly into `tools/`,
update dependent tracked paths and documentation, preserve calendar logic and
research IDs, and record evidence. No commit or push is authorized. Acceptance:
compile with v5 `config/Mkinclude`, compare pre/post stdout and calendar results,
check dependent shell calls, clean/ignore behavior and stale path references.
Untracked legacy relocation and other existing work remain outside this task.
This is a task-specific work claim, not a re-registration of historical projects.
Completed implementation and focused validation: 108 exact pre/post cases and
eight actual caller invocations passed; executable cleaned; no commit/push.
Unmanaged legacy callers retain historical paths and remain outside scope.
See [the utility guide](../tools/README.md) and
[VR-0148](../research/records/validation_runs/VR-0148.md) for findings and validation.

### p02-f04 flood-depth visualization (2026-11-14)

The maintainer assigned this bounded addition to the existing
`manual-automation` branch. Owner: Dai Yamazaki (maintainer); Codex implements.
Scope: add f04a `flood_depth-raster` and f04b `flood_depth-downscale_1min` for
the 2001-09-01 `flddph` snapshot over 102–108°E, 9–15°N, reusing the existing
Tutorial guide01 downscaling workflow and displaying the 1-minute `flddif`
background in gray. Main files: `visualization/output_analysis/` f04 entry
point, plotting implementation, project README, catalog, and project-local
figures; no model or map-data generation changes. Acceptance: verify units,
time, dimensions, masks, output orientation, and the downscaler inputs; render
and visually inspect the two panels and assembled Figure. Gallery publication
is outside this assignment unless separately authorized.

Completed 2026-11-14: reused the existing 2001-09-01 `flddph` sample and ran
`downscale_flddph_trib.F90` for 102–108°E, 9–15°N at 1-minute resolution.
Saved the assigned 360 × 360 result as a dated NetCDF sample and rendered the
two panels plus a side-by-side Figure. Native and downscaled valid depths range
from 0 to 17.878 m and 0 to 17.526 m, respectively; the common 0–20 m scale
contains all values. Both panel PNGs have identical map and colorbar bounds;
the combined Figure was visually inspected. The existing downscaler compiled
with four REAL(8)-to-REAL(4) conversion warnings in coordinate calculations.
The maintainer subsequently authorized Gallery publication of p02-f01 through
p02-f04; the selected combined Figures and their README/catalog references
were synchronized.

### Subbasin Color and basin/network context (2026-11-13)

The maintainer assigned this bounded addition to `manual-automation` and
requested commit/push on completion. f01d reads the prepared Mekong
`subcol-30000.bin` directly with the same pastel palette as f01c; f01 defaults
to a four-panel 2x2 grid using the existing physical sizing/layout helpers.
The follow-up adds thin black original-basin-ID boundaries and a gray
`nextxy_noedge` missing-cell overlay, retaining finite terminal codes.
README/catalog describe display indices versus IDs and the upstream-area
increment threshold. Binary orientation/masks, categorical palette and layout
checks pass; the final Figure was visually reviewed. f01a-c scientific scripts,
f02, map generation, tutorials and Gallery snapshots are unchanged. Owner:
Dai Yamazaki (maintainer); Codex implements. See
[VR-0146](../research/records/validation_runs/VR-0146.md).

### Headless f02b trial (2026-11-12)

Maintainer requested this bounded trial on `manual-automation`, owned by
Dai Yamazaki with Codex implementation. f02b omits both local and curved
flexible arrowheads; thickness scaling, endpoints and extent are preserved.
The b panel and composite are regenerated; a/c PNGs remain byte-identical.
Five sizing scenarios pass. See
[VR-0144](../research/records/validation_runs/VR-0144.md).

### f02 option naming update (2026-11-12)

Maintainer-assigned naming follow-up on `manual-automation`, owned by Dai
Yamazaki with Codex implementation: a `connect_type`, b `enhance_tickness`,
c `enhance_color` (exact requested spelling). Filenames, titles, wrapper,
README/catalog and active examples now agree; all PNGs regenerated. Plotting
content is unchanged, verified by exact non-title pixel/source comparisons
and five three-panel sizing scenarios. See
[VR-0143](../research/records/validation_runs/VR-0143.md).

### Three-panel line river map revision (2026-11-12)

The maintainer assigned p01-f02's three-panel revision to the current
`manual-automation` branch, owned by Dai Yamazaki with Codex implementation,
and explicitly authorized commit/push after verification. Scope: f02 wrapper,
panel scripts/helpers, tracked project figures, README/catalog and necessary
naming examples; no Gallery publication. Acceptance: all panels use
102–109°E, 10–17°N; f02a has stronger black local/orange flexible arrows;
f02b has black area-scaled enhanced thickness; f02c uses shade-rainbow arrows
over categorical dark-gray bsncol; aligned canvases and readable exports.
All four PNGs are generated; five sizing scenarios pass across three panels,
including exact extent, full-link counts, foreground encodings and aligned
geometry. The composite was visually reviewed. See
[VR-0141](../research/records/validation_runs/VR-0141.md).

The maintainer's follow-up retains the current **99–109°E, 9–19°N** extent,
superseding the initial bounds above. Targeted refinements reduce orange
flexible-arrow heads and increase f02a curvature, keep f02b shaft scaling with
standard-size heads, and darken f02c's categorical background. All four PNGs
are regenerated; exact prior width/color/coordinate comparisons and five
three-panel sizing scenarios pass. See
[VR-0142](../research/records/validation_runs/VR-0142.md).


### Three-panel raster river map revision (2026-11-12)

The maintainer assigned this bounded task to `manual-automation`, owned by
Dai Yamazaki with Codex implementation, and requested commit/push after checks.
f01 now contains Upstream Area (`uparea`), original Basin IDs (`basin`), and
soft Basin Color indices (`bsncol`); the elevation and width panels are removed.
All three panels reuse the verified explicit colorbar-slot layout and have
identical map geometry. The README and catalog distinguish original IDs from
display indices and reference the actual regional-map preparation code.
Three f01 sizing scenarios and five f02 scenarios pass; f02 PNGs regenerated
byte-for-byte unchanged. Gallery and map/model sources remain unchanged. See
[VR-0139](../research/records/validation_runs/VR-0139.md) for evidence and limits.

The maintainer's follow-up requests a display-only pseudo-log categorical legend
for f01b: IDs 1–20 have individual expanded slots; higher IDs have compressed
intervals and representative labels. Map colors, raw IDs and geometry remain
unchanged. Three sizing checks pass with no overlapping legend labels; the map
pixels exactly match the prior Figure. See
[VR-0140](../research/records/validation_runs/VR-0140.md).

### Visualization method naming and discovery (2026-11-12)

The maintainer assigned this bounded refactor to `manual-automation`, owned by
Dai Yamazaki with Codex implementation, and requested commit/push on completion.
The development guide now defines stable method/option identifiers and semantic
discovery; the catalog, river-map entry points, six panels, titles, and eight
PNGs use consistent names. Both workflows and five f02 sizing scenarios pass;
six-panel baseline comparisons preserve scientific content and axes geometry.
Gallery, model/map tools, and historical evidence remain unchanged. See
[VR-0137](../research/records/validation_runs/VR-0137.md) for naming mappings,
semantic-discovery review, and validation details.

The maintainer subsequently clarified that f02 is **Line River Map**
(`line_river_map`); vector visualization is a distinct future method. Active
resources, titles, catalog and naming examples now use this corrected name;
the implementation and virtual-colorbar layout are unchanged. See
[VR-0138](../research/records/validation_runs/VR-0138.md).

### Bounded p01-f02 layout experiment (2026-11-12)

The maintainer explicitly assigned this task to `manual-automation`, owned by
Dai Yamazaki with Codex implementation, and authorized commit/push after checks.
Scope: shared f02 map/colorbar layout, river-map README, and three regenerated
project PNGs; preserve scientific plotting, Gallery, and the shared guideline.
The virtual-colorbar experiment passes five real-panel sizing/export scenarios:
both default map rectangles are 968x968 pixels on identical 1393x1188 canvases,
with aligned real/hidden colorbar axes. See
[VR-0136](../research/records/validation_runs/VR-0136.md) for evidence and limits.
This records the bounded assignment, not a change to other registered projects.

After reviewing the successful alignment, the maintainer approved promoting
virtual colorbars to the common visualization rules on 2026-11-12, on the same
`manual-automation` branch. The guideline and f02 documentation now agree;
plotting behavior and generated images are unchanged. See
[ADR-0009](../research/records/decisions/ADR-0009-virtual-colorbar-layout.md).

### Tutorial01 manual-authoring milestone (2026-11-08)

Tutorial01 now has a standalone educational GOSH script and beginner manual at [`tutorial/tutorial01-get_started/`](../tutorial/tutorial01-get_started/); manual design, reset tooling, assessment, original drafts, and developer-only manual-generation evidence are separated under `design/`. The standard beginner build command is `make all` from `src_main/`, for either a new or existing executable. The 40-day Mekong simulation completed in a disposable checkout, and reset preserved `config/Mkinclude`. The manual defines `cmf_root`, shows verified repository and data listings, explains setup prompts and required actions, and introduces the map/runoff/matrix before their GOSH settings. Tutorial01 now uses `PROJ` and isolates results under `out/${PROJ}/`; rerun and developer-reset checks preserved sibling projects, input data, and configuration. The shared agent instructions remain evolving defaults. Python package installation remains optional; the setup script was tested in diagnosis/decline mode. This is not release-package validation, scientific validation, or Linux portability evidence. See the [tutorial collection](../tutorial/README.md), [contributor guide](../tutorial/how_to_develop_tutorials.md), [development plan](tutorial_development_plan.md), DT-0083–DT-0088, and VR-0126–VR-0131.

The documentation reorganization project was completed and merged to `master` in PR #121; it is no longer active. Map modernization continues under Issue #122. Research logging is a separate, cross-project case-study activity; its current framework edits use `feature/map-data-tools` by maintainer instruction, but the research activity is not tied to that feature branch and has no dedicated Issue. Historical work is not reconstructed in this status table.

| Project / scope and coordination record | Owner | Persistent working branch | Main modules or files | Current progress | Potential conflicts | Next actions |
| --- | --- | --- | --- | --- | --- | --- |
| CaMa-Flood v5 model source and simulation workflow modernization — isolate legacy v4 code and establish independently buildable v5 model/run examples; no GitHub Issue by maintainer direction. | Dai Yamazaki (maintainer); Codex implements approved stages | `feature/gosh-refactor` | [Phase 0/1 plan and validation](model_source_workflow_plan.md); `src_main/`; `gosh_test/`; `inp/test-mek_1deg_nc/`. | Phase 0 and Phase 1A–1D plus individual Binary/NetCDF map-input support are implemented and locally validated on macOS. Separate Binary-only and NetCDF-enabled builds work. Mixed-map 40-day Mekong tests (one variable NetCDF, network-only NetCDF, and all nine core map inputs NetCDF) completed; all five output variables matched the all-Binary baseline bitwise. Converter output was read back and verified exactly. The clarified contract limits individual NetCDF input to variables already read through the legacy Binary path; ECMWF-specific `elevslope` / `mask_slope` remain consolidated-NetCDF-only and produce explicit errors in individual-file mode. The two legacy consolidated slope-reader handle defects have now been corrected: each read uses an open `CRIVPARNC` handle, without changing equations or the individual-file contract. These checks were rerun after the clarification. In three 40-day comparisons, Binary versus NetCDF runoff and Binary versus NetCDF output matched bitwise for `outflw`, `storge`, `sfcelv`, `flddph`, and `fldfrc`. The annual-NetCDF workflow completed 2000 (366 records) and 2001 (365 records), carrying the Binary restart into year two; 731 records total. Runoff conversion is exact for all 731 source float32 fields. Model output metadata was corrected for `cell_methods` and dimensionless `fldfrc` units. Restart variables are now documented in `variable_table/restart_variables.csv`; a separate two-year NetCDF-Restart run completed with exact `outflw`, `storge`, and `sfcelv` agreement against Binary-Restart output. Binary Restart CTLs are generated from the current Namelist and registry; Float64 files use an explicitly lossy Float32 visualization copy because standard GrADS Binary CTLs read 32-bit floats. Synthetic checks cover Float32/Float64, normal/storage-only, and optional restart fields. GrADS runtime reading could not be verified because the local OpenGrADS executable lacks a required dynamic library. These are operational/I/O checks, not scientific validation or broad platform support. Interactive workstation setup is now available through root `s01-setup_fortran.sh` and `s02-python_setup.sh`; both diagnose first, require confirmation for local changes, and leave `adm/Mkinclude` untouched. See the setup section in the project plan and VR-0119. The tutorial plan now requires interactive researcher review between source/data investigation and specification approval. Tutorial 02 has a researcher-approved four-experiment design at [the experiment spec](../tutorial/tutorial02-mekong_netcdf_4exp/tutorial_design.md): Default, No Bifurcation, Kinematic Wave, and No Floodplain; `DT=600`; adaptive stepping for Local Inertial and fixed stepping for Kinematic Wave. All four required annual runoff files (2000–2003) are Git-tracked; the branch currently tracks 2000–2005. Hydrograph and annual-maximum daily-mean discharge comparisons are specified. All four experiment scripts and visualization tools are implemented; all 16 annual segments (2000–2003) completed on macOS with NetCDF runoff, maps, output, and Restart handoffs. Each experiment produced 1,461 daily records with continuous represented dates; the selected-site hydrograph and annual-maximum figures were generated. Simulated reverse flow occurs at Prek Kdam in both Local Inertial cases; the Can Tho Default/No-Bifurcation series differ throughout 2001–2003. No observed discharge validation is claimed. The updated source evidence, result summaries, figures, and unresolved scientific interpretation questions are in [the experiment specification](../tutorial/tutorial02-mekong_netcdf_4exp/tutorial_design.md), DT-0078, DR-0062, and VR-0123. The beginner README and package assembly remain future work.| Legacy `src/` and `gosh/` remain unchanged. NetCDF build has only been exercised on macOS/Homebrew; Linux portability, MPI, `heatlink/`, `sediment/`, and `ICI/` remain unvalidated. The derived NetCDF sample's inclusion in a future v5 downloadable package is undecided because a v5 packaging workflow is not established. No suitable consolidated NetCDF fixture is available, so runtime use of `LSLOPEMOUTH` / `LSLPMIX` in legacy mode remains unverified despite the handle fixes. The current-outflow reader discrepancy was corrected in commit `87abfddf`; the post-fix diagnostic effect has not been runtime-validated (KG-0029). | Retain a fixture-based test of the legacy consolidated route and optional groundwater, mean-sea-level, and MPI paths for a later task (KG-0027); review the Float32 visualization-copy behavior for Float64 Restart (KG-0030); no separate post-fix runtime check is planned per maintainer decision; source-level alignment is documented in KG-0029; decide whether to include `inp/test-mek_1deg_nc/` in a future downloadable v5 package; validate the build on Linux when available. Future Driver/Coupler design goals and open execution-order questions are recorded in [the model-source plan](model_source_workflow_plan.md#future-work-driver-and-coupler-architecture); no interface change is authorized. |
| Runoff input data tools modernization ([Issue #126](https://github.com/global-hydrodynamics/CaMa-Flood_v4/issues/126); [PR #127](https://github.com/global-hydrodynamics/CaMa-Flood_v4/pull/127)) — improve runoff workflow reproducibility, metadata, tests, and usability. | Dai Yamazaki (maintainer); Codex implements explicitly assigned phases | `feature/runoff-data-tools` | ERA5-Land workflow: `inp/ERA5-Land_download/`; product registry: `inp/runoff_datasets.csv`; user guide: `inp/README.md`; phase evidence: `docs/runoff_data_inventory.md`; model contract: `src/cmf_ctrl_forcing_mod.F90`. | The approved Runoff Input Data Tools changes from `feature/runoff-data-tools` were merged to `master` in PR #127. The registry, reproducible ELSE_GPCC Mekong sample workflow, ERA5-Land download/conversion tools, and associated examples are integrated. Follow-up local v5 work adds the derived annual NetCDF Mekong sample under `inp/test-mek_1deg_nc/`; it is registered separately and reuses the `test-mek_1deg` grid/input matrix. End-to-end model validation of new products is recorded in the model-source project, not treated as completion of every runoff science question. KG-0019 and the ERA5-Land source/metadata questions KG-0022–KG-0024 remain as recorded. | Historical `feature/runoff-data-tools` work is merged; current v5 model I/O work is tracked under `feature/gosh-refactor`. Scientific interpretations in the open knowledge gaps remain unresolved unless explicitly stated in their records. | Resolve the open runoff source/metadata questions when authoritative evidence is available; decide v5 distribution packaging for the derived annual NetCDF sample with the model-source project. |
| Map data/tools modernization ([Issue #122](https://github.com/global-hydrodynamics/CaMa-Flood_v4/issues/122)) — map metadata, conversion, and processing tools. | Dai Yamazaki (maintainer); Codex implements assigned tasks | `feature/map-data-tools` | Map project plan: `docs/map_data_tools_plan.md`; migration details: `docs/map_params_migration_plan.md`; map metadata and conversion files under `map/`. | Standard channel parameter, permanent-water area, non-MPI bifurcation, and MPI map-preprocessing workflows are implemented in v5 `map/tools/`; the permanent-water migration preserves legacy output on the Mekong sample and is intended for post-processing, not current simulation input. Normal and `MaxMPI` Mekong basin groups plus 4/8/16 region maps matched legacy outputs byte-for-byte. The independent partition diagnostic follows model-local vector membership. s04 can now optionally write `check_bif_bsnmod_mpi.bin` with the legacy basin-change and bifurcation-endpoint classifications before MPI region assignment; focused regression compares both records with the legacy outputs. It writes `bifcol_mpi.bin` from MPI-aggregated basin IDs (independent of process count N, but dependent on `normal`/`MaxMPI` aggregation mode), plus only numbered `mpireg-N.bin` region maps. It runs `analysis_check_mpi_bifurcation` on the numbered `DEFAULT_MPI` map. The optional `analysis_mpi_region_color` can manually create `bsncol_mpi-N.bin` from a selected region map; s04 does not invoke it. No `mpireg.bin` alias is generated. s01-s05 use consistent STEP/SUCCESS/ERROR banners with simulated failure-path coverage. Model execution through `gosh/` and changes to `src/` are outside the current map-tools construction milestone. An incidental build-only probe is recorded in VR-0044; it does not block this milestone. The maintainer confirms `map/src/` is historical v4 and must be preserved; legacy workflows retain `diminfo_` names. v5 uses `ROFFTAG` for paired `diminfo_`/`inpmat_` names and `HIRES_TAG` for high-resolution selection. Allocation Phase B migrated the flow-gauge, dam, and level-gauge allocation tools into `map/tools/` with shared map I/O, explicit single-area `HIRES_TAG` selection, and v4 regression baselines; committed and pushed as `ef9fec9`; see `docs/map_allocation_migration_plan.md`. All five GRDC, GRanD, and MLIT list CSVs present in `map/data/` are designated for Git tracking under their existing names. This does not include source workbooks or unrestricted source databases. `GRanD_alloc+Mekong.csv` supplements the GRanD list with several recently constructed Mekong dams added through Yamazaki Laboratory research; row-level sources and review date are not documented; the v5 level-gauge wrapper now uses the approved `MLIT_LevelGauge_allocated.csv`, while the legacy v4 wrapper remains unchanged. | Legacy v4 interfaces and v5 workflows must remain distinct. Any future model-source or `gosh/` integration is a separate task. | Consider any future scientific changes to legacy thresholds only under separate approval and validation; recover row-level provenance for Mekong GRanD additions if needed. Multi-area allocation is not a required follow-up for the initial migration. Matrix and permanent-water tools process multiple areas by source inspection; full package-scale integration remains pending. Model-side bifurcation integration is now implemented on `feature/gosh-refactor`: simulation accepts the authoritative map-root `bifprm.csv`, NetCDF-enabled builds also accept `<MAPDIR>/netcdf/bifprm.nc`, and legacy `bifprm.txt` remains supported; focused I/O and Restart checks are recorded in VR-0115. Row-level sources for the added Mekong dams remain unresolved. Independent scientific validation is not part of Phase B. The five current list CSVs are designated for tracking. MPI model-runtime pairing with `mpireg-N.bin` and process count belongs to a separately scoped future simulation-workflow task; the model-side bifurcation-table integration is complete as recorded in VR-0115. Preserve `map/src/` and reconcile this branch-local status when publishing. |
| CaMa-Flood v4-to-v5 research case study (cross-project activity; no dedicated Issue) — evidence-linked record of discussions through validation across successive projects. | Dai Yamazaki (maintainer; primary framework user); Codex assists with record maintenance | No research-specific branch. Current framework update: `feature/map-data-tools`, by explicit maintainer instruction. | Canonical record set: `research/`; policy: `AGENTS.md`; protocol: `research/study_protocol.md`. | Framework approved. Git-based documentation and map-tools stage narratives are recorded; the pre-documentation parent commit is tagged. `EV-0001` and the current task are in the event log. Earlier ChatGPT discussion details remain queued for maintainer-supplied sources. | Research records span project boundaries; preserve the same `research/` history when branches change or merge. Initial use is single-maintainer, with ordinary Git handling and no locking system. | Continue significant event logging across projects. Review the pending stage/branch-name caveat and discussion summaries; specify concrete v4/v5 task comparisons and resolve package-baseline identity and human-participant ethics before formal evaluation. The map-tools project remains ongoing. |

## Coordination requiring maintainer decisions

| Decision | Current state | Next action |
| --- | --- | --- |
| Comparative study protocol | Four evaluation dimensions are maintainer-approved; concrete comparable tasks, rubrics, and v4 package identity remain to be specified | Define task-based evidence and baseline before comparative claims or participant evaluation |
| Dashboard publisher | Maintainer responsibility; named publisher not yet assigned | Assign the person responsible for reconciling and publishing rows to `main` |
| Supported validation configurations | Baseline version, compiler matrix, and required datasets not yet agreed | Record acceptance checks in the project plan and status, or in an Issue if one is used |

## Approved updates awaiting publication

The v4/v5 build configuration separation is implemented on `feature/gosh-refactor`: legacy Makefiles retain `adm/Mkinclude`, while v5 model and map-tool Makefiles require `config/Mkinclude`. The default v5 templates and setup guide are in `config/`. GitHub Actions now creates the ignored active configuration from the tracked GNU template in its disposable checkout, installs GNU Fortran and NetCDF-Fortran, and requires the v5 model and regional map-tool builds plus existing map checks; a local clean-checkout build passed. The active configuration remains untracked. See the build setup section in `docs/model_source_workflow_plan.md`.

Map data/tool work is tracked by Issue [#122](https://github.com/global-hydrodynamics/CaMa-Flood_v4/issues/122). Research logging is a cross-project activity with no dedicated Issue. This dashboard copy is an uncommitted proposal until reconciled with `origin/main`. The B2.4 migration records MPI preprocessing and diagnostics; historical `map/src/` tools and tracked Mekong binaries were not modified. Phase C exposes four shared analysis tools under descriptive names (`analysis_river_point_info`, `analysis_upbasin`, `analysis_subbasin`, `analysis_river_node_latlon`) and a portable, explicitly prepared `script_analysis/` bundle alongside independent standard s06/s07 workflows. The Mekong sample uses a 30,000 km2 subbasin threshold, ID 0 for modeled cells below threshold, and station-labeled `upbasin-<GRDC_ID>.bin`; the historical `map/src/` source tree remains unchanged. The Phase C specification update and its 65-test validation are recorded in DR-0043 and VR-0070; the earlier migration and sample-output milestones remain in VR-0068 and VR-0069.

High-resolution area handling contracts are documented in `docs/map_data_tools_plan.md`: allocation is intentionally single-area; matrix and permanent-water aggregation support multiple areas by source inspection. Multi-area package-scale integration validation is pending and is not claimed as completed. The previous wording that treated multi-area allocation itself as an unresolved defect has been narrowed; see `research/records/knowledge_gaps/KG-0014.md`.


DT-0121 branch-local scope: maintainer authorizes WSL launcher and session Pins,
comparison/CSV, automated and actual Mekong GUI verification, commit/push on existing
feature/package-builder. Owner Codex; implementation complete,305 tests plus3 subtests PASS and1 Windows
end-to-end SKIP. Actual Mekong/browser/PNG/CSV verified;248 protected hashes unchanged.
See visualization/map_explorer/DESIGN.md and VR-0167. Publication is to this project
branch only; Windows end-to-end still requires a Windows host.

DT-0121 published on feature/package-builder in `1e2b472e3d4749b2f5cbee4f4bd7f98be801663b`; EV-0545 records normal
push. Windows real-host QA remains unverified; unrelated TE-Japan deletions excluded.

DT-0122: maintainer authorizes investigation/fix of background Auto limits to valid
P5/P95, including Gallery/legacy entry paths, and nonpositive-only Log fallback0.01.
Owner Codex on existing feature/package-builder; scientific inputs read-only. Plan
and scope in visualization/map_explorer/DESIGN.md; inherited attributes remain distinct
from native pixels, manual limits and River coloring preserved.

DT-0122 completed:315 tests plus3 subtests PASS;1 existing Windows SKIP. Ordinary,
Gallery preset and old-JSON Auto now use the same P5/P95 valid reference. Actual
Mekong/browser/PNG verified;248 protected hashes unchanged. See VR-0168 for root
cause (legacy forced minimum), exact ranges and retained masks/units/manual bounds.

DT-0122 published on feature/package-builder in `d77ae9da3b2a73aa8dfb176bcf282894b55f2b4b`; EV-0549 records
normal push. Existing5010 session was preserved; verified preview uses5011.

DT-0123: maintainer authorizes initial p01-f04b + Overland ON on existing
feature/package-builder. Codex owns app startup/tests/docs; canonical preset and
scientific inputs unchanged. Acceptance: startup/fallback/save-load and actual GUI.

DT-0123 complete:28 focused tests PASS and actual fresh Mekong browser verifies
p01-f04b + Overland ON. Missing inputs retain usable map; saved settings unaffected.
See VR-0169. Canonical preset/scientific data unchanged; unrelated deletions excluded.

DT-0124 (maintainer-approved extension on feature/package-builder): f04a Channel
only; f04b Channel + Overland. All p01 River Map/Explorer display sources now use
complete nextxy. Blue→Navy exactly matches Gallery anchors and defaults in
p01-f03a/f04b. Regenerated f02–f05 and Gallery copies; updated docs/catalog and
legacy JSON migration. Codex owns these visualization files; scientific inputs
read-only, unrelated23 TE-Japan deletions excluded. Final evidence: VR-0170.

DT-0124 complete:332 tests +15 subtests PASS,1 Windows SKIP; final74 palette
checks PASS. Actual Mekong/browser and four combined figures visually checked.
213 protected hashes unchanged. Research retains10 pre-existing broken links.

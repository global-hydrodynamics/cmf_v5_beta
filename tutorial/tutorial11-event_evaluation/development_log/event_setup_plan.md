# Tutorial 11 — July 2021 Flood Event Setup Plan

**Status:** Planning draft; no Rhine simulation or new satellite acquisition has been run.

## Objective

Prepare a reproducible CaMa-Flood v5 evaluation of the July 2021 western European floods. The domain must represent the complete target watershed and its routed network. Reported damage localities identify observation priorities; they do not define the simulation boundary.

## Standard setup sequence

1. **Identify the hydrologic target.** Inspect CaMa-Flood Basin IDs, `nextxy` topology, upstream area and outlet cells on the selected map. Compare the model representation with authoritative watershed information. Record any basin IDs that combine distinct natural rivers.
2. **Choose the simulation domain.** Include the complete model-represented watershed, upstream boundary, downstream outlet and enough neighboring cells for boundary conditions. If the executable requires a rectangle, derive it from the full watershed plus a documented margin. Record its bbox and rationale in [evaluation_domain.md](../evaluation_domain.md).
3. **Set separate observation domains.** Use report-documented impact localities, station locations, satellite scene coverage and valid-pixel availability to plan smaller flood-observation AOIs. Do not assume these equal the simulation domain.
4. **Inventory evidence and data.** Record source, date/time meaning, units, coordinate reference, quality masks, licence and processing history for discharge, model and satellite data. Keep observed inundation polygons distinct from town-centre markers.
5. **Prepare and review the two maps.** Maintain `../figure/event_basin_overview.png` for whole-basin/domain decisions and `../figure/event_flood_impact_area.png` for impact/AOI planning. The impact map may have detail panels. Any candidate boundary must be visibly labelled as provisional.
6. **Confirm before simulation.** Resolve map-version and basin-topology issues, domain mask and boundary conditions, forcing/initialization, observation time conventions, and data rights. Only then approve a simulation and evaluation protocol.

## Required figures

- **Basin Overview:** full model basin class and routed network, named rivers, stations, reported impact localities, candidate simulation rectangle and separate candidate GFM AOIs.
- **Flood Impact Area:** OSM background, routed network, categorized impact localities, available model-basin boundaries, in-range stations, candidate GFM AOIs and optional model grid.

See [evaluation_domain.md](../evaluation_domain.md) for current candidate extents and limits. The River Map development example [f06 — OSM_background](../../../visualization/river_map/README.md#f06--osm_background) illustrates a basin overview and a local impact map; it is not a substitute for these event-planning figures.

## Map Explorer capability assessment

Map Explorer already reads model basin/uparea rasters and `nextxy`, renders river networks, displays an online OSM background and supports manually placed Pins. It does not currently import impact-location CSV/GeoJSON, choose a complete watershed by Basin ID as a domain operation, display imported simulation/GFM rectangles, or include OSM in its standard PNG export. Its standard PNG exporter deliberately excludes online tiles. The figures here reuse the source map products and river geometry; no broad GUI extension was needed. A future generic CSV/GeoJSON overlay and extent-box layer could improve repeatability, but should be a separately scoped feature.

## Completion criteria

- The two figures exist, have source/attribution notes, and distinguish candidates from verified observations.
- Domain bboxes, map/version, basin IDs, rivers and selection rationale are recorded.
- Impact points include source and location confidence in `../impact_locations.csv`.
- No town markers are presented as flood polygons; no candidate AOI is presented as confirmed satellite coverage.
- No simulation or new GFM download is claimed unless it was actually performed.

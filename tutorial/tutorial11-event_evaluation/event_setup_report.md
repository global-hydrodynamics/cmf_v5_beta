# Tutorial 11 — Event Setup Findings

**Prepared:** 2026-11-21
**Status:** Candidate setup only; no model simulation or new GFM acquisition was performed.

## Result

Two planning figures now separate whole-watershed simulation planning from localized flood-observation planning:

- [Basin overview](figure/event_basin_overview.png): CaMa-Flood 0.25° basin class and routed links, candidate simulation rectangle, separate candidate GFM AOIs, impact localities and supplied stations.
- [Flood impact areas](figure/event_flood_impact_area.png): OSM context with CaMa links, report-based localities, gauge markers, model basin outline, and separate detailed panels for Ahr/Erft-Swist, Kyll/Prüm and Meuse/Vesdre/Gete/Dyle.

The marks show reported affected towns with approximate town-centre coordinates, **not observed inundation polygons**. Candidate satellite rectangles do not confirm acquisition or valid-pixel coverage. OSM © OpenStreetMap contributors; see the figure and [copyright notice](https://www.openstreetmap.org/copyright).

## Domain recommendation

Start domain review from CaMa map `glb_15min` Basin ID 74 and its `nextxy` network, then validate the hydrologic identity against higher-resolution basin/topology data. At 0.25°, the modeled outlet group combines Rhine and Meuse/Vesdre routing; it cannot be called a pure Rhine natural basin. ID 1299 captures nearby Gete/Halen and Dyle/Wavre cells. A provisional 3.125–12.125°E, 45.875–52.375°N simulation rectangle contains the full ID 74 group with a two-cell margin. Confirm model mask, forcing, upstream/outlet boundaries and whether distinct basins should be simulated together before execution.

Use smaller observation AOIs around Ahr–Erft–Swist/Moselle tributaries and separately around Meuse–Vesdre–Gete–Dyle. The previously inspected GFM sample extent omits the western comparison area and gauges Speyer/Maxau; its valid cells cover only part of the target grid. Acquire no further imagery until scene availability, quality masks and licences have been checked.

## Map Explorer assessment

Reusable functionality includes CaMa rasters/network, online OSM and manual Pins. CSV import, domain-box overlays, basin extraction as a domain tool, and OSM-included PNG export are absent. The standard exporter explicitly excludes online tiles. Static plotting reused existing map data and river geometry; a future generic CSV/vector and extent overlay could be useful but is not required to deliver these planning figures.

## Evidence and remaining decisions

Public reports document severe impacts in the Ahr, Erft/Swist, Kyll/Prüm, Vesdre and other regional rivers; see [GEER](https://www.geerassociation.org/components/com_geer_reports/geerfiles/GEER%20Report%202021%20Western%20European%20Floods%20Final%20w%20GPS%20coordinates_comp.pdf), [Rhineland-Palatinate LfU](https://lfu.rlp.de/fileadmin/lfu/Startseitenbeitraege/2022/Hochwasser_im_Juli2021_1_.pdf), [Erftverband](https://www.erftverband.de/wp-content/uploads/2021/08/20210820_ev_auswertung_hw_20210714.pdf) and [Mohr et al. (2023)](https://nhess.copernicus.org/articles/23/525/2023/). Coordinates in the map are approximate locality markers rather than source geocoded inundation limits.

Before simulation/evaluation, decide whether the target is Rhine-only or a combined model outlet group; validate natural watershed boundaries, grid/map version, domain mask and boundary conditions; select event period and forcing/initialization; reconcile six-hour discharge metadata; and verify dated satellite coverage, valid masks, processing versions and rights. Historical sources and data inventories remain in [flood_event_overview.md](flood_event_overview.md), [GFM inventory](gfm_data_inventory.md), and [observation inventory](observation_data_inventory.md).

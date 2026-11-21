# Tutorial 11 — Candidate Evaluation Domains

**Status:** Provisional planning; basin representation and satellite coverage need further review.

Simulation and flood-observation domains serve different purposes. The simulation domain covers the full target watershed represented by the selected model map. Observation domains focus on reported impacts and usable observation coverage; they can be smaller and non-contiguous.

## Simulation domain

**Map inspected:** CaMa-Flood v5 `map/glb_15min/` (0.25°; COG `basin`, `uparea`, `nextxy`). The candidate model basin group is Basin ID **74**. Its basin-raster cells and routed links extend approximately to 3.625–11.625°E and 46.375–51.875°N. A neighboring Basin ID **1299** includes cells around the Gete/Halen and Dyle/Wavre area.

At this map resolution, the Rhine and Meuse/Vesdre routing joins the same model outlet group. Thus ID 74 is a model-grid routing class, **not a pure natural Rhine watershed polygon**. Use it as evidence of the model-represented drainage group, not as an independently verified catchment boundary. Verify the appropriate model river and watershed interpretation against a higher-resolution/native basin source before finalizing the event's hydrologic scope.

| Domain | west | south | east | north | Status and rationale |
| --- | ---: | ---: | ---: | ---: | --- |
| Candidate simulation rectangle | 3.125 | 45.875 | 12.125 | 52.375 | Provisional rectangle containing all ID 74 cells plus two 0.25° cells of margin. Includes the complete coarse model group, not just impact locations. Check domain mask, upstream inflow, outlet, and boundary conditions before use. |

This bbox is a candidate computation window, not a final mask. Confirm `diminfo`, the active map, forcing coverage, upstream and downstream boundary handling, and whether the model configuration supports the intended full-basin experiment. Do not use the impact AOIs below as the simulation domain.

## Flood observation domains

Coordinates are W/S/E/N. These AOIs guide observation inventory and acquisition review; they do not assert that a satellite scene or valid water observation exists.

| Observation AOI | west | south | east | north | Rivers / locations | Rationale |
| --- | ---: | ---: | ---: | ---: | --- | --- |
| Ahr–Erft–Swist and Moselle tributaries | 6.0 | 49.4 | 7.8 | 51.1 | Ahr, Erft, Swist, Kyll, Prüm; Schuld, Altenahr, Bad Neuenahr-Ahrweiler, Sinzig, Euskirchen, Blessem/Erftstadt, Kordel, Prümzurlay | Focuses on documented destructive tributary impacts while including the adjacent river reaches. Review with actual scene footprints and valid-pixel masks. |
| Meuse–Vesdre–Gete–Dyle comparison | 4.2 | 49.5 | 6.3 | 51.4 | Meuse, Vesdre, Gete and Dyle; Verviers, Pepinster, Valkenburg, Halen, Wavre | Keeps distinct western comparison rivers visible and includes separate model cells around Gete/Halen and Dyle/Wavre. These rivers must not be described as Rhine tributaries. |

The existing GFM test window (5.6–10.0°E, 49.5–52.9°N) does not cover the western Meuse/Vesdre/Gete/Dyle area and excludes Speyer/Maxau south of 49.5°N. The inspected 2021-07-15 sample had valid input in about 44% of its requested target cells; this is not evidence of coverage at every impact locality. Check each acquisition footprint, quality/exclusion flags and valid pixels before choosing observation AOIs. No new acquisition was performed for this planning task.

## Stations and impact locations

The supplied gauges are Lobith (6.10833°E, 51.84444°N), Speyer (8.44876°E, 49.32379°N), and Maxau (8.30561°E, 49.03896°N). Speyer and Maxau are south of the current GFM test window. Their six-hour means are not measurements of Ahr or Erft discharge. The source inventory records unresolved unit/time-zone metadata.

Impact markers are approximate town-centre coordinates used to locate report-documented affected places. They are not georeferenced flood extents. See [impact_locations.csv](impact_locations.csv) for source links, confidence and notes.

## Map Explorer

Explorer supports model rasters, river network, online OSM and manually clicked Pins. It does not import the impact CSV or domain rectangles, select complete basins as an operation, or export OSM tiles in standard PNGs. The static figures therefore use a reproducible plotting script and documented source map products; no general GUI redesign is included.

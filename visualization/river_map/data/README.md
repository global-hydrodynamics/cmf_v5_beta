# f06 OSM Map Overlay Data

The f06 scripts keep Rhine 2021-specific plotting settings and event locations
outside the drawing code.

- `f06_settings.json` contains each panel's extent, labels, tick intervals,
  OSM/mask styling, basin ID and point-group styling. Required settings are
  read directly; a missing or malformed file produces a clear error rather
  than silently writing a substitute.
- `f06b_zoomup.csv` stores the f06b extent and two candidate observation
  domains documented in `../../../tutorial/tutorial11-event_evaluation/02_analysis_domain_design.md`.
  The f06b extent is 4.0–8.0°E, 49.0–52.0°N. The regional rectangles are
  candidate observation AOIs, not observed flood boundaries.
- `f06b_plot.csv` copies report-based localities and source notes from
  `../../../tutorial/tutorial11-event_evaluation/impact_locations.csv`, adding
  short plot labels, symbol groups and label offsets. Coordinates identify
  approximate town centers; they are not georeferenced inundation limits.
  Halen retains its lower coordinate confidence and is marked `(?)` on the
  map.

The Ahr/Erft/Kyll/Prüm group and the Meuse/Vesdre/Gete/Dyle comparison group
are shown separately. The latter rivers are not Rhine tributaries. Keep source
URLs, confidence and notes with each plotted locality when updating this file.

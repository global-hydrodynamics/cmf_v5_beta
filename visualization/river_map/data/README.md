# f06 OSM Map Overlay Data

These small CSV files provide editable plotting data for River Map panels f06a
and f06b.

- `f06b_zoomup.csv` stores the f06b map extent and the two candidate observation
  domains documented in `../../../tutorial/tutorial11-event_evaluation/evaluation_domain.md`.
  The f06b extent (4.0–8.0°E, 49.2–51.6°N) is the union of those domains with a
  0.2° margin. The two regional rectangles are candidate observation AOIs, not
  observed flood boundaries.
- `f06b_plot.csv` copies report-based localities and source notes from
  `../../../tutorial/tutorial11-event_evaluation/impact_locations.csv`, adding short plot
  labels, symbol groups and label offsets. Coordinates identify approximate
  town centers; they are not georeferenced inundation limits. Halen retains its
  lower coordinate confidence and is marked with `(?)` on the map.

The Ahr/Erft/Kyll/Prüm group and the Meuse/Vesdre/Gete/Dyle comparison group are
shown separately. The latter rivers are not Rhine tributaries. Keep source URLs,
confidence and notes with each plotted locality when updating this file.

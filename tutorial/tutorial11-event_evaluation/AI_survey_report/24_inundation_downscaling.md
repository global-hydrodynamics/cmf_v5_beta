# Step24 — Preliminary simulated inundation at the S1A acquisition

The single Sentinel-1A orbit 038784 acquisition spans 2021-07-15
05:49:37.397–05:51:42.396 UTC. Its midpoint (05:50:39.8965 UTC) is nearest
to the existing Rhine2021 **06:00 UTC** output, **9 min 20.1035 s later**.
The existing tributary-aware CaMa-Flood method downscales that floodplain-depth
snapshot to 1 arcmin over the Step02 satellite analysis region, 4–8°E, 49–52°N.

![Preliminary simulated inundation](../figure/f24-inundation_1min.png)

Figure24. One simulated depth snapshot, not a satellite observation or agreement
map. Dry cells are beige; missing/unmapped cells gray. Positive depth uses a
0–10 m scale with an upper extension. The existing permanent-water option imposes
a 0.1 m minimum at river-width pixels, so positive depth includes permanent water.

The grid has 180×240 cells; 42,960 are valid, including 37,429 dry and 5,531
positive-depth cells. The 240 missing cells coincide with invalid high-resolution
catchment indices. Valid depth ranges from 0 to 10.874 m. The mapped pattern is
concentrated along the river network, establishing feasibility and a preliminary
spatial diagnostic; it does not demonstrate event inundation accuracy.

The internal buffer extends beyond the regional map at west/north, which may
affect boundary behavior. Forcing attribution KG-0019 and local downscaling
accuracy remain unvalidated. GFM comparison, accuracy metrics and finer resolution
are deferred. See the [execution report](../AI_work_report/24_inundation_downscaling.md)
and [machine-readable handoff](../metadata/24_downscaling_verification.json).

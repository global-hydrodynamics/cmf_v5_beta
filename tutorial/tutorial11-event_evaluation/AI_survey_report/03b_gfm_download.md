# GFM Native Data Acquisition — Survey Report

## Executive Summary

The selected pass `S1A_o038784_dt049389` (Sentinel-1A, 15 July 2021, descending) has a retained download manifest recording 11 selected STAC Items, 44 item-layer references for four GFM layers, and 37 unique local COG files. The summary reports all 37 files verified, no missing or failed files, and a total of **52,333,157 bytes (49.91 MiB)**. It marks the handoff `ready_for_p03c: true`.

## Investigation and Results

The acquisition was limited to `ensemble_flood_extent`, `ensemble_water_extent`, `reference_water_mask`, and `exclusion_mask`. The 44 manifest rows represent requested Item/layer associations; repeated assets are deduplicated into 37 unique COG paths. These native assets are held under the ignored Tutorial-local `Atlantis/` working tree, not as Git-managed observations.

The handoff consists of a pass-specific `download_manifest_S1A_o038784_dt049389.csv` and `download_summary_S1A_o038784_dt049389.json` beneath the local Atlantis catalogue metadata. Paths are rooted at the Atlantis dataset root. The summary includes the readiness result based on item-layer mapping, file presence, size/checksum and GeoTIFF readability.

## Figures and Interpretation

No separate figure is required for this acquisition inventory. Acquisition metadata and spatial context are presented in [Figure 3a](03a_satellite_availability.md#figures-and-interpretation). The downloaded files are GFM classification products; their presence does not mean every pixel is valid or that the pass fully observed the flood.

## Findings and Limitations

- The recorded download outcome supports the next classification workflow for the selected pass and requested four layers.
- This is one pass and does not provide a complete event timeline or all candidate satellite observations.
- The input COGs remain in ignored local storage, so another checkout does not receive them through Git.
- No claim is made here about flood detection quality or independent validation against truth.

## Recommendations / Next Steps

Use the manifest as the authoritative p03c file list; do not repeat STAC search or download when the files remain present. Preserve the four layer semantics and exclusion/reference information during classification. Confirm local manifest paths and file availability before processing in another environment.

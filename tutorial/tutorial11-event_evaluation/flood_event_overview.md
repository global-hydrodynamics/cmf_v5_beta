# Tutorial 11: July 2021 Rhine Flood Event Overview

Prepared: 2026-11-20

Status: Background documentation for a future event-evaluation tutorial

This document summarizes the July 2021 western European flood event considered
in the ECMWF–CaMa-Flood collaboration, the proposed evaluation targets, and
candidate datasets. It does not define evaluation metrics or an implementation.

Two evidence sources are kept separate:

- **ECMWF correspondence:** information supplied by the maintainer from the
  email thread **“D2 report and deliverable,” 3–13 November 2026**. The original
  emails and attachments have not been inspected for this documentation task.
- **Public documentation:** information checked against the provider and
  research references linked below on 20 November 2026. Product descriptions do
  not establish that particular event files have already been obtained.

## 1. Event overview

The July 2021 western European floods affected Germany, Belgium, Luxembourg and
the Netherlands. Intense rainfall over **13–15 July**, particularly in the
**Eifel and Ardennes** region, caused rapid and destructive flooding. The
**Ahr and Erft**, tributaries of the Rhine, suffered especially severe damage.
Flooding also affected the **Moselle system and its tributaries**, including
rivers such as the Kyll and Prüm, and the **Meuse basin**. These affected systems
provide the wider regional context; the Meuse is a separate river basin, not a
Rhine tributary. See the [event analysis by Mohr et al. (2023)](https://nhess.copernicus.org/articles/23/525/2023/)
and the [Copernicus account of the July floods](https://mapping.emergency.copernicus.eu/news/the-copernicus-emergency-management-service-forecasts-notifies-and-monitors-devastating-floods-in-germany-netherlands-belgium-and-switzerland/).

The **Rhine main stem also experienced elevated flows and water levels**. The
Rhineland-Palatinate environmental authority's [July 2021 flood report](https://lfu.rlp.de/fileadmin/lfu/Startseitenbeitraege/2022/Hochwasser_im_Juli2021_1_.pdf)
documents the main-stem flood wave. Main-stem behaviour should be distinguished
from the much more localized destructive tributary floods: the three supplied
Rhine stations do not directly measure discharge in the Ahr or Erft.

A **candidate analysis period is 2021-07-10 to 2021-07-25**, allowing the event
and its surrounding conditions to be examined. This window is a collaboration
proposal, not a finalized computational interval. Exact endpoint handling,
time zone, and any required initialization period remain to be confirmed.

## 2. River discharge data

### 2.1 Information shared by ECMWF

According to the maintainer's summary of the correspondence, **Cinzia Mazzetti**
provided the archive **`stations_data.tar.gz`**, containing 2021 discharge series
in **CSV and NetCDF** and coordinates corresponding to the CaMa-Flood grid.
The archive itself was not opened or added to this repository in this task.

| Identifier in the supplied data | Station | Country | Reported period | Reported time resolution |
| --- | --- | --- | --- | --- |
| `153` | Lobith | Netherlands | 2021 | 6 hours |
| `6` | Bonn | Germany | 2021 | 6 hours |
| `28` | Maxau | Germany | 2021 | 6 hours |

These identifiers are those reported for the supplied archive; they are not
assumed to be universal national station identifiers.

The values are **six-hour mean discharge**, and each timestamp denotes the
**end of the aggregation interval**. Thus, a value labelled by time `t`
represents the preceding six-hour interval, not an instantaneous measurement
at `t`. The precise time zone and file metadata still require inspection.

### 2.2 Provenance and interpretation to confirm

The transfer of files by ECMWF does **not** establish that these series are
observations or that ECMWF is their original producer. Before treating them as
an evaluation reference, confirm:

- Whether each series is observed discharge, simulated discharge, a forecast,
  or another processed product; identify the original provider and processing.
- Discharge units, missing values, quality flags, temporal coverage and time
  zone, and consistency between the CSV and NetCDF representations.
- The meaning and coordinate reference system of the supplied coordinates,
  including whether they identify a station, a model-cell centre or an outlet,
  and which CaMa-Flood grid/version they refer to.
- The licence, attribution requirements, access restrictions and permission to
  redistribute the archive or derived extracts.

No observation status, open-data licence or redistribution permission is
asserted here. The tutorial's intended use of open observational discharge data
remains a future objective, not an established property of this archive.

## 3. ECMWF CaMa-Flood simulations

The following experiment information was introduced by **Gianpaolo Balsamo** in
the correspondence, as summarized by the maintainer. It has not been verified
by retrieving MARS fields or inspecting experiment metadata.

| Item | `j1ee` — recommended | `j1w9` — alternative |
| --- | --- | --- |
| Experiment description | Offline TCo1279 | Offline TCo399 |
| CaMa-Flood resolution | 1 arcmin | 15 arcmin |
| Reported output interval | 3-hourly | 6-hourly for 2021 |
| MARS experiment identifier | `expver=j1ee` | Experiment name `j1w9`; confirm the complete MARS request |
| Reported availability | From July 2016 onward | 1980–2025 |
| Flooded fraction | Parameter `235275`, as reported in the correspondence | Parameter/request details to confirm |

TCo1279/TCo399 and the CaMa-Flood river-grid resolutions describe different
parts of the experiment and must not be used interchangeably. The preferred
candidate for the satellite comparison is the reported **1-arcmin `j1ee`** run.

Before use, confirm access rights, actual July 2021 field availability, model and
map versions, runoff forcing, the full MARS request, variable units and masks,
and whether outputs are instantaneous or averaged. In particular, **3-hourly
output does not by itself specify a three-hour mean**, and the end-of-interval
convention of the supplied discharge files must not be assigned to MARS output
without evidence. Availability dates reported in an email are not a guarantee
of current download access. Redistribution terms remain unconfirmed.

## 4. Satellite-derived flood extent

The following products are candidates, not a finalized selection. Spatial
sampling, image acquisition time, composite windows and delivery latency are
different concepts. None of these products should automatically be interpreted
as a continuous record of the event maximum.

| Candidate and public source | Spatial resolution / representation | Temporal resolution / support | Characteristics and limitations |
| --- | --- | --- | --- |
| **Copernicus Global Flood Monitoring (GFM)** — [product documentation](https://extwiki.eodc.eu/GFM/PUM/Products) and [official archive overview](https://global-flood.emergency.copernicus.eu/media/events/4/the_new_gfm_archive.pdf) | 20 m pixel sampling of processed Sentinel-1 SAR products. | Acquisition-driven, with irregular local revisits; not a fixed daily observation. Near-real-time delivery latency is not the revisit interval. | Radar-based flood/water layers include reference water and exclusion information. Gaps between acquisitions can miss short-lived peaks; exclusion masks and detection limitations must be retained. Check the actual July 2021 scenes, processing version and coverage rather than inferring them from the general archive description. |
| **NASA MODIS `MCDWD_L3` family** — [LAADS product entry](https://ladsweb.modaps.eosdis.nasa.gov/missions-and-measurements/products/MCDWD_L3), [NASA product overview](https://www.earthdata.nasa.gov/global-flood-product) and [user guide](https://www.earthdata.nasa.gov/s3fs-public/2024-04/MCDWD_UserGuide_RevD.pdf) | Approximately 250 m for the MODIS flood product family. | Daily products, including 1-, 2- and 3-day flood composites; exact layer and temporal support must be recorded. | Optical Terra/Aqua observations are affected by clouds and cloud shadows. Multi-day composites improve opportunities for detection but do not represent a single acquisition. Confirm the exact archive short name, collection and July 2021 files; `MCDWD_L3` and `MCDWD_L3_NRT` should not be silently treated as identical archive selections. |
| **Kuro Siwo**, candidate events **518 and 520** — [maintainer repository](https://github.com/Orion-AI-Lab/KuroSiwo) and [publisher dataset card](https://huggingface.co/datasets/orion-ai-lab/Kuro-Siwo-Webdataset) | 10 m annotation resolution reported by the publisher. | Event-based multi-temporal samples with two pre-flood images and one post-flood image; no regular daily cadence. | Expert-interpreted SAR labels distinguish flood and permanent water, with valid-pixel masks. Event IDs 518 and 520 are collaboration-supplied candidates: their version-specific identities, geographic footprints, scene dates and correspondence to this event remain unverified. Check the selected GeoTIFF/annotation release rather than substituting arbitrary training patches. |
| **Copernicus EMS Rapid Mapping `EMSR517`** — [activation: Flood in Western Germany](https://mapping.emergency.copernicus.eu/activations/EMSR517/) | AOI- and product-dependent mapped/vector results; no single raster resolution for the activation. Confirm each product's source-image resolution and mapping specification. | Event-driven delineation, monitoring and grading products; no fixed observation interval. The activation began on 13 July 2021. | Targeted coverage rather than a wall-to-wall basin time series. Use each product's image acquisition time, not its delivery date, as observational timing. Delineation and damage grading are different outputs. Product polygons and underlying satellite imagery have distinct access/rights considerations. |

The [Rapid Mapping FAQ](https://mapping.emergency.copernicus.eu/about/faqs/)
explains that different imagery-resolution classes are used; it does not assign
one common resolution to EMSR517. Exact scenes and AOIs for all four candidates
remain to be reviewed. No satellite data were downloaded for this task.

## 5. Data processing tools: Atlantis

The correspondence identifies **Atlantis**, developed through **ECMWF Code for
Earth**, as a candidate tool for obtaining satellite inundation data and
converting them to the **CaMa-Flood 1-arcmin grid**:

[ECMWFCode4Earth/atlantis](https://github.com/ECMWFCode4Earth/atlantis)

The proposed use is to prepare satellite-derived flood information on the grid
of the recommended ECMWF experiment for later comparison. This is a reported
intended use, not a verified statement that a particular Atlantis version
supports every candidate product or an already implemented tutorial workflow.
The supplied repository URL returned **404 / Not Found** during this review;
access status, current location, code version, supported data sources and
licence therefore remain to be confirmed with the collaborators. No alternative
repository is assumed to be equivalent.

The example domain and satellite observation window supplied for exploration are:

| Setting | Candidate value |
| --- | --- |
| Longitude bounds | 5.6–10.0°E |
| Latitude bounds | 49.5–52.9°N |
| Satellite observation period | 2021-07-13 to 2021-07-20 |
| Intended target grid | CaMa-Flood, 1 arcmin |

This bounding box is a regional subset, not the entire Rhine catchment. It is
also distinct from the broader candidate discharge-analysis window in Section 1.
The exact target-grid alignment, treatment of invalid/unobserved pixels,
representation of permanent water, temporal correspondence and conversion
method remain future decisions. Conversion to a model grid does not remove
satellite uncertainty or create observations where coverage is missing.

## 6. Relevance to Tutorial 11

Tutorial 11 is intended eventually to cover:

1. **Sub-daily river discharge event evaluation**, using documented reference
   discharge and corresponding CaMa-Flood simulations.
2. **Satellite-based flood extent evaluation**, using appropriately documented
   satellite products and the corresponding model grid and output times.

This documentation establishes context and data questions only. Specific
metrics, event-selection rules and implementation design are **not decided**.
Neither evaluations nor data-processing code have been implemented here.

## 7. References and data provenance

### 7.1 Collaboration information

**Email subject:** “D2 report and deliverable”

**Correspondence period:** 2026-11-03 to 2026-11-13

**Basis for this document:** the maintainer's supplied summary, not independent
inspection of the original email thread or attachments.

This source supplies the station/archive details attributed to Cinzia Mazzetti;
the experiments attributed to Gianpaolo Balsamo; the recommended experiment;
the candidate dates/domain; the Kuro Siwo event identifiers; and the proposed
Atlantis use. Public dataset documentation does not independently verify those
collaboration-specific details. No raw email, attachment or contact details
beyond the named contributors are reproduced.

### 7.2 Public references

- Mohr et al. (2023), [A multi-disciplinary analysis of the exceptional flood event of July 2021 in central Europe – Part 1: Event description and analysis](https://nhess.copernicus.org/articles/23/525/2023/).
- Copernicus EMS, [contemporaneous overview of the July 2021 floods](https://mapping.emergency.copernicus.eu/news/the-copernicus-emergency-management-service-forecasts-notifies-and-monitors-devastating-floods-in-germany-netherlands-belgium-and-switzerland/).
- Landesamt für Umwelt Rheinland-Pfalz, [Hochwasser im Juli 2021](https://lfu.rlp.de/fileadmin/lfu/Startseitenbeitraege/2022/Hochwasser_im_Juli2021_1_.pdf).
- GFM, [output-layer documentation](https://extwiki.eodc.eu/GFM/PUM/Products) and [archive overview](https://global-flood.emergency.copernicus.eu/media/events/4/the_new_gfm_archive.pdf).
- NASA, [MODIS `MCDWD_L3` product entry](https://ladsweb.modaps.eosdis.nasa.gov/missions-and-measurements/products/MCDWD_L3), [global flood products](https://www.earthdata.nasa.gov/global-flood-product) and [MODIS product user guide](https://www.earthdata.nasa.gov/s3fs-public/2024-04/MCDWD_UserGuide_RevD.pdf).
- Kuro Siwo, [project repository](https://github.com/Orion-AI-Lab/KuroSiwo), [publisher dataset card](https://huggingface.co/datasets/orion-ai-lab/Kuro-Siwo-Webdataset) and [dataset paper](https://arxiv.org/abs/2311.12056).
- Copernicus EMS, [EMSR517 activation](https://mapping.emergency.copernicus.eu/activations/EMSR517/) and [Rapid Mapping FAQ](https://mapping.emergency.copernicus.eu/about/faqs/).
- Atlantis, [collaboration-supplied repository URL](https://github.com/ECMWFCode4Earth/atlantis); unavailable during this review, as noted in Section 5.

Public sources were consulted on **2026-11-20**. Their current descriptions may
reflect processing versions newer than those used for July 2021.

### 7.3 Licence and redistribution status

The supplied station archive and ECMWF experiments have **unconfirmed origin
and/or usage terms**. Do not label them open observational data or include them
in a tutorial distribution without confirming those points.

The Kuro Siwo repository states a CC BY dataset licence, and the linked publisher
card specifies CC BY 4.0. Confirm the chosen dataset version and assets, retain
required attribution, and distinguish dataset rights from a software licence.
For GFM, NASA MODIS and EMSR517, consult the provider-specific terms and required
acknowledgements before redistribution; these conditions have not been reviewed
for a tutorial package. In particular, access to a derived flood map is not
permission to redistribute its source satellite imagery. Atlantis's licence
could not be checked. Public availability of a webpage alone is not evidence
that every linked input or derived asset can be redistributed.

The immediate next step is a review of the actual files, metadata, coverage and
permissions, followed by a separately agreed event-evaluation workflow.

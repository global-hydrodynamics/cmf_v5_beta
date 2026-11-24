# July 2021 Western European Floods — Survey Report

## Executive Summary

The July 2021 event affected western Germany, Belgium, Luxembourg and the Netherlands. Intense rainfall during 13–15 July over the Eifel and Ardennes produced destructive flooding in tributaries including the Ahr and Erft; flooding also affected the Moselle system and the separate Meuse basin. The Rhine main stem experienced elevated flow, but that response should not be conflated with the rapid, locally destructive tributary floods.

The event overview identifies candidate observations and uncertainties; it does not define a completed model evaluation. Figure 1 retains 14 reported towns/localities from the event inventory and adds sourced, river/gauge-level timing context in its legend. Their plotted coordinates are approximate locality positions, not surveyed flood extents.

## Investigation and Results

### Event and hydrologic context

The core rainfall/event context used here is 13–15 July 2021. A broader 10–25 July window was proposed for later event analysis, while Step 14 separately records the July 1–August 1-exclusive simulation. The Ahr and Erft are Rhine tributaries; Kyll and Prüm belong to the Moselle system; the Meuse is a separate basin. This distinction matters when relating impact reports and observations to a model routing network.

Public sources retained with the event review include Mohr et al. (2023), the Copernicus Emergency Management Service event account, and the Rhineland-Palatinate environmental authority report on the July 2021 flood. Product and event references are listed below and in the retained research record.

### Reported locations

The inventory contains 14 mapped localities, including affected reaches in the Ahr/Erft, Moselle and Meuse systems. The list is a selected set of documented locations, not an exhaustive damage inventory. See [`metadata/01_impact_locations.csv`](../metadata/01_impact_locations.csv) for coordinates, group, display labels, source fields and location confidence. The CSV supports plotting and spatial handoff; it does not turn a town-centre coordinate into a measured inundation boundary.

### Flood Timing and Detailed Locations

The new [`metadata/01_reported_flood_timing.csv`](../metadata/01_reported_flood_timing.csv) keeps one row per locality report or distinct gauge/system timing record. The original 14 impact IDs and their plotted town/locality coordinates are retained. Locality-level rows with no source-supported onset or peak have blank UTC fields. Additional gauge coordinates are stored separately in this ledger; they do not replace the approximate Fig. 1 locality markers. Coordinate precision and timing confidence are recorded independently.

| River system / timing evidence | Source-supported timing | Interpretation and limitation |
|---|---|---|
| Ahr | Müsch gauge: about 14 Jul 22:00; Altenahr gauge: about 15 Jul 02:00; Bad Bodendorf gauge: 15 Jul 04:30 CEST | LfU Table 5 labels the source times MESZ/CEST. These are station-level peak estimates, not onset/impact times for all four Ahr towns; the Ahr peak discharge estimates are substantially uncertain. |
| Erft / Swist | Bliesheim gauge exceeded HQextrem about 06:30 and reached its maximum water level at 10:40 on 15 Jul | Erftverband does not specify a time zone in the cited text. Bliesheim is a distinct gauge; the time is not transferred to Blessem or other towns. The report describes attenuation of the wave around the Blessem gravel pit. |
| Kyll | Kordel gauge maximum: 15 Jul 10:30 CEST | LfU station-specific level/discharge maximum; not a general impact time for the whole Kyll valley. |
| Prüm | Prümzurlay gauge maximum: 15 Jul 12:30 CEST | LfU station-specific maximum; not a general impact time for the whole Prüm valley. |
| Vesdre | Reconstructed Eupen reservoir-outlet peak: 15 Jul 01:30; source time-zone convention not stated | This is an outlet release and downstream-wave context, not a measured peak at Verviers or Pepinster. No UTC conversion is made. |
| Meuse basin / Geul | Geul peak in Valkenburg: 15 Jul 05:30; time zone not stated by the cited report | Waterschap Limburg reports 100 m³/s. This is the Geul, a Meuse-basin tributary, not the Meuse main stem; no UTC conversion is made. |
| Gete | Halen centre is reported flooded under influence of Gete and Velpe; exact onset/peak not found | The basin report notes a controlled Gete dike opening on 16 Jul; that response action is not the onset or peak. |
| Dyle | Wavre municipal source describes 15–16 Jul impacts, date resolution only | No clock time or local peak was identified in the retained source. |

For the LfU entries, the report explicitly labels the table column “Datum Uhrzeit [MESZ]”; UTC values in the CSV are therefore two hours earlier and original CEST text is retained. For the Erftverband, Waterschap Limburg and Eupen thesis records, source time-zone notation was not confirmed, so their original time labels are preserved and UTC fields remain blank. Figure 1’s legend uses concise local-source times and explicitly identifies gauge/river context; it does not claim that every town had the listed peak time.

Detailed station locations that were source-supported include the Kordel gauge (WGS84 6.643061°E, 49.834920°N), Prümzurlay gauge (6.4368°E, 49.8676°N), Bliesheim gauge (6.82577°E, 50.77912°N), and Altenahr gauge (6.9886168°E, 50.5166311°N). The Müsch and Bad Bodendorf station listings also provide coordinates, retained with medium confidence. These station positions are distinct from town-centre coordinates and are stored in the timing CSV rather than moving the 14 map markers. Precise damage points for most of the other locality markers were not established in this bounded review.

The Ahr gauges were destroyed or lost observations during the event, and peak discharge reconstruction carries uncertainty. Do not align model outlet peaks directly with a town’s impact time: use the station/reach identity, travel time, source time convention, and the distinction between water-level peak, discharge peak, inundation maximum and response/report time. No gauge allocation or model comparison was performed here.

### Candidate observations

Three supplied discharge series are Lobith (153), Speyer (63) and Maxau (28), at six-hour intervals. Provider correspondence describes the values as six-hour means and timestamps as interval ends; these semantics are not encoded explicitly in the files. Bonn/6, named in an initial correspondence summary, is absent from the inspected files. Units, source timezone and original observing agency remain unresolved. Candidate satellite/event products include GFM, NASA MODIS MCDWD, Kuro Siwo event samples 518/520, and Copernicus EMSR517; availability and suitability for this event must be verified product by product.

A collaboration summary also identifies ECMWF experiments `j1ee` and `j1w9` as possible model sources. This information was supplied second-hand and was not verified against MARS fields or experiment metadata. It must not be treated as confirmed availability.

## Figures and Interpretation

![Figure 1 — Reported flood impact localities](../figure/f01-reported_flood_impacts.png)

*Figure 1. Reported flood-impact localities and river context. Markers show approximate named places; they do not delineate observed floodwater.* The map helps relate the literature review to later basin/domain analysis. OSM and mapped river context are geographic orientation aids, not independent evidence of flood extent.

## Findings and Limitations

- The event is a multi-basin regional flood; a Rhine-only interpretation does not cover all documented affected systems.
- Three supplied gauges describe Rhine main-stem context but do not directly observe Ahr or Erft tributary discharge.
- Gauge units, time zone, source agency and coordinate convention need confirmation before quantitative matching. The maintainer confirmed permission to redistribute the supplied station files, but no named open-data licence was identified.
- Candidate satellite products differ in sensor, acquisition/composite timing, resolution, validity masks and coverage. None should automatically be interpreted as a complete event-maximum map.
- Kuro Siwo identifiers and the ECMWF experiment details remain collaboration-supplied candidates rather than independently confirmed source records.

## Recommendations / Next Steps

Use the reported river/locality inventory as Step 2 input. Trace the relevant reaches and upstream networks on the selected CaMa-Flood map; keep Meuse distinct from Rhine tributaries. Before evaluation, resolve gauge units/time convention and verify any candidate simulation product and satellite acquisitions. Do not infer missing observations as dry conditions.

### Key sources

- [Mohr et al. (2023), Natural Hazards and Earth System Sciences](https://nhess.copernicus.org/articles/23/525/2023/)
- [Copernicus EMS account of the July floods](https://mapping.emergency.copernicus.eu/news/the-copernicus-emergency-management-service-forecasts-notifies-and-monitors-devastating-floods-in-germany-netherlands-belgium-and-switzerland/)
- [Rhineland-Palatinate environmental authority, July 2021 flood report (PDF)](https://lfu.rlp.de/fileadmin/lfu/Service/Publikationen/Bestellkatalog/Hochwasser_im_Juli2021_barrierefrei.pdf)
- [Erftverband, flood in the Erft catchment, 14–16 July 2021 (PDF)](https://www.erftverband.de/wp-content/uploads/2021/08/20210820_ev_auswertung_hw_20210714.pdf)
- [Waterschap Limburg, evaluation of the July 2021 water crisis (PDF)](https://www.waterschaplimburg.nl/publish/pages/5867/waterschap_limburg_-_leerevaluatie_watercrisis_juli_2021_1.pdf)
- [Delft University thesis, flood event of July 2021 (Vesdre reservoir and gauge analyses)](https://repository.tudelft.nl/file/File_c9e6518e-3d11-4b32-a3fa-03e392a927fe)
- [Demer Basin, July 2021 flood assessment (PDF)](https://cdn.nimbu.io/s/3putlmp/assets/Overstromingen%20juli%202021%20Demerbekken_aan%20een%20catastrofe%20ontsnapt.pdf)
- [GFM product documentation](https://extwiki.eodc.eu/GFM/PUM/Products); [NASA MCDWD product](https://ladsweb.modaps.eosdis.nasa.gov/missions-and-measurements/products/MCDWD_L3); [Kuro Siwo](https://github.com/Orion-AI-Lab/KuroSiwo); [Copernicus EMSR517](https://mapping.emergency.copernicus.eu/activations/EMSR517/)

See also the [observation data guide](../observation/README.md), the [Step 4 discharge report](04_discharge_observations.md), and the [Step 3a availability report](03a_satellite_availability.md).

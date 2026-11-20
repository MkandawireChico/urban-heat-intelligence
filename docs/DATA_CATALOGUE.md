# Data catalogue: Blantyre heat adaptation baseline

Status: initial source assessment, 19 November 2026

This catalogue records candidate datasets before ingestion. Inclusion does not mean a dataset has been downloaded, validated for Blantyre, or approved for a particular analysis. Each dataset must pass the checks below before use.

## Candidate datasets

| Theme | Candidate source | Coverage and resolution | Intended use | Main limitations and checks |
|---|---|---|---|---|
| Land-surface temperature | USGS Landsat Collection 2 Level-2 Surface Temperature | Global scene-based archive; Landsat 8 from 2013 and Landsat 9 from 2022 | Historical and seasonal patterns in daytime land-surface temperature | Not air temperature, indoor temperature, personal exposure, or clinical heat risk. Apply the published scale factor and mask fill, cloud, cloud-shadow and quality-flagged pixels. Check emissivity/atmospheric caveats and scene dates. |
| Vegetation and land cover | Copernicus Sentinel-2 Level-2A / Level-1C | Global Level-1C since July 2015; multispectral bands include 10 m and coarser resolutions | Vegetation cover, built-up context and land-cover classification | Optical imagery is affected by clouds, haze, seasonal vegetation and classification error. Confirm product coverage and processing level for every acquisition. Do not infer cooling causality from NDVI alone. |
| Population | WorldPop Global2 R2025A, 3 arc-second population counts | Approximately 100 m at the equator; annual estimates 2015–2030 | Population distribution and population-weighted screening | Modelled estimates, not census counts. The v3 API supports polygon aggregate queries; those totals do not provide cell-level values. Record release, year, query geometry and API source. CC BY 4.0. |
| Population cross-check | GHSL population grids and WorldPop 1 km Global2 product, where suitable | Product- and epoch-dependent | Independent sensitivity analysis | Confirm the exact release, epoch, resolution and licence before selection. Do not mix products without documenting methodological differences. |
| Built environment | Copernicus Global Human Settlement Layer (GHSL) | Multiple products, epochs and resolutions, including population, built-up surface/volume and building attributes | Built-up intensity and settlement context; cross-check against local mapping | Product-specific resolutions and epochs differ. Select exact product and epoch; cite European Commission and check reuse conditions. |
| Buildings, roads and amenities | OpenStreetMap Malawi extract via Geofabrik | Country-wide vector extract; PBF, Shapefile and GeoPackage options | Building footprints, road network, mapped facilities, green spaces and other tagged features | Completeness varies by place and feature. Absence from OSM is not evidence of absence on the ground. ODbL attribution and share-alike obligations apply. Record extract date and tags used. |
| Administrative boundaries | National Geospatial Information Authority / National Spatial Data Centre, distributed through UN SALB | Validated administrative-unit polygons; temporal validity listed through 2022-10-27 | Candidate official administrative framework and boundary cross-check | Confirm the exact administrative level, current legal status, metadata and permitted reuse. A district boundary is not interchangeable with a city or planning boundary. |\n| City and ward boundaries | World Bank Malawi City Extents | Blantyre City polygon and ward polygons; underlying Blantyre file last updated 2018-02-24 | Candidate city study extent and ward-level aggregation, pending comparison with current national boundaries | Public CC BY 4.0, but the file is dated. Treat as a candidate only, not a current legal boundary, until confirmed with the national custodian or Blantyre City Council. |
| Weather context | Copernicus ERA5-Land | Historical land reanalysis; approximately 9 km grid, hourly time series | Regional meteorological context and temporal comparison | Too coarse to resolve neighbourhood heat differences in Blantyre. Reanalysis is not a local station observation. Use as contextual data, not street-level exposure. |

## Source links and attribution

- USGS Landsat Collection 2 Surface Temperature: https://www.usgs.gov/landsat-missions/landsat-collection-2-surface-temperature
- Copernicus Sentinel-2 collection: https://dataspace.copernicus.eu/data-collections/copernicus-sentinel-missions/sentinel-2
- WorldPop Global2 R2025A API and documentation: https://api.worldpop.org/v3/documentation
- WorldPop Global2 R2025A population counts DOI: https://hub.worldpop.org/doi/10.5258/SOTON/WP00839
- GHSL download and reuse conditions: https://human-settlement.emergency.copernicus.eu/downloadWizard.php
- Geofabrik Malawi OSM extract: https://download.geofabrik.de/africa/malawi.html
- OpenStreetMap licence: https://www.openstreetmap.org/copyright
- UN SALB Malawi validated administrative units / National Spatial Data Centre: https://salb.un.org/en/data/mwi\n- World Bank Malawi City Extents (Blantyre City and wards; CC BY 4.0): https://datacatalog.worldbank.org/search/dataset/0042046/malawi-city-extents
- ERA5-Land dataset: https://cds.climate.copernicus.eu/datasets/reanalysis-era5-land-timeseries
- ERA5-Land documentation: https://confluence.ecmwf.int/pages/viewpage.action?pageId=462906181

## Data selection rules

1. Keep source files immutable. Store derived outputs separately.
2. Record source URL, retrieval date, product identifier, version, acquisition date or epoch, licence, checksum, coordinate reference system, resolution and processing steps.
3. Preserve native spatial resolution during ingestion. Resampling must be explicit and justified for each analysis.
4. Do not treat raster pixels as independent observations when the source is modelled or spatially autocorrelated.
5. Align population and exposure data only after documenting grid, projection, pixel-area and temporal compatibility.
6. Keep observed, modelled, derived and user-supplied fields distinguishable in both data and interface.
7. Do not fill missing local cost, land access, water, maintenance or implementation responsibility fields with invented values. Mark them unknown and prevent unsupported feasibility claims.
8. Do not publish sensitive household-level or personally identifying field data. Prefer aggregated spatial units and review disclosure risk.

## Blantyre boundary decision

Blantyre City Council's Town Planning page identifies the Blantyre Urban
Structure Plan 2024–2039 as its strategic planning framework. The linked April
2024 document is labelled a draft. In that draft, the current city boundary is
used as the urban edge, while five proposed extension areas totalling 2,863 ha
are described separately. The draft states an intention to begin the extension
process in 2025 with a target completion in 2030.

This distinction matters for the study design. Do not combine the existing
city boundary and proposed extension areas into one polygon. The baseline
analysis should use the current legally recognised city boundary. Proposed
extension areas should be a separate future-planning scenario if the Council
confirms their status and provides usable geometry.

The World Bank Malawi City Extents dataset is a useful candidate because it
includes Blantyre City and ward polygons, but its Blantyre file dates to 2018.
Compare it with the boundary and ward data held by Blantyre City Council and
the National Spatial Data Centre before adopting it. Blantyre City Council's
planning page also states that the Council holds a city-wide GIS database and
provides geospatial information for planning purposes.

Sources:
- Blantyre City Council Town Planning: https://bccmw.com/planning.html
- Draft Blantyre Urban Structure Plan 2024–2039:
  https://bccmw.com/assets/uploads/2024/04/Draft-Blantyre-Urban-Structure-Plan.pdf
- World Bank Malawi City Extents:
  https://datacatalog.worldbank.org/search/dataset/0042046/malawi-city-extents
- National Spatial Data Centre administrative units:
  https://salb.un.org/en/data/mwi

## Local evidence still required

Remote sensing and global datasets cannot establish the local delivery conditions needed for credible intervention planning. A later fieldwork or partner-validation phase must collect or verify:

- Which organisation controls or has authority over candidate sites.
- Whether the site is available for the proposed intervention.
- Water access and seasonal reliability where relevant.
- Installation, labour, transport and material costs with date and source.
- Annual maintenance requirements, responsible party and expected replacement cycle.
- Existing tree survival, shade use, drainage, building use and public access where relevant.
- Community priorities and potential displacement or access impacts.

Every local value must have a source, date, geographic scope and confidence note. Where no evidence exists, the decision engine must expose the gap rather than silently assume feasibility.

## Initial ingestion order

1. Acquire and inspect the authoritative study boundary and compare it with OSM and GHSL settlement extents.
2. Download a dated Malawi OSM extract and clip it only after the study boundary is agreed.
3. Inspect WorldPop 3 arc-second and GHSL population/built-up products; select one primary population layer and retain the other as a sensitivity check.
4. Select a consistent set of cloud-screened Landsat scenes across relevant seasons and years.
5. Add Sentinel-2 land-cover features after validating classification quality.
6. Add ERA5-Land only as regional temporal context.
7. Build a data-quality report before computing any neighbourhood ranking.

## Decision gate

Do not publish neighbourhood rankings until the project has:
- A documented study boundary and spatial unit.
- A quality-reviewed temperature time series with cloud and quality masking.
- A population layer with its version and uncertainty limitations documented.
- A reproducible alignment and aggregation method.
- Explicit treatment of missing data and confidence.
- A clear statement that the resulting map is a screening baseline, not a validated measure of personal heat exposure or health risk.


## Blantyre boundary ingestion update (20 November 2026)

The user-supplied World Bank archive has now been inspected. It contains one polygon layer (`MWI_BlantyreCity`) with 26 ward polygons in EPSG:32736. The source archive does not contain a separate city-outline feature. The project derives a provisional city outline by dissolving all 26 ward polygons and retains the original ward layer for ward-level aggregation.

All 26 geometries are non-null, non-empty and structurally valid. Ward names and source IDs are unique. No positive-area overlaps were detected. The dissolved polygon is one connected geometry with an area of approximately 236.38 km². These checks do not establish completeness, absence of gaps, positional accuracy or legal authority. The source `TOTAL` field is zero for every ward and must not be used as population data.

The boundary QA report and source provenance are recorded in `data/boundaries/BOUNDARY_QA_REPORT.json` and `data/boundaries/world_bank/blantyre_city_2018.json`. Processed GeoJSON and GeoPackage outputs were supplied in the boundary delivery package. Compare the geometry with current Blantyre City Council and National Spatial Data Centre records before policy-facing use.

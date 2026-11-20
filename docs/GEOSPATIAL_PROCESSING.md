"""Initial satellite processing contract

This project begins with small, independently testable pixel transformations.
Raster reading, reprojection, spatial masking, compositing and export are
implemented as separate pipeline stages.
"""

## Landsat Collection 2 Level-2 surface temperature

For Landsat Collection 2 Level-2 surface-temperature bands, convert digital
numbers to Kelvin using:

`temperature_K = DN * 0.00341802 + 149.0`

Convert Kelvin to Celsius by subtracting 273.15. Collection 2 fill value is 0.
The implementation masks fill pixels and the following QA_PIXEL flags:
fill, dilated cloud, cirrus, cloud, cloud shadow and snow. If QA_RADSAT is
supplied, non-zero values are masked as well.

The selected QA flags are conservative screening choices. Scene-level quality
control must also inspect ST_QA uncertainty, cloud distance, missing pixels,
scene metadata and acquisition conditions. Do not interpret masked pixels as
zero temperature.

Surface temperature is a satellite-derived land-surface property at the
satellite overpass time. It is not air temperature, indoor temperature,
personal heat exposure or a direct measure of health risk. Compare scenes
within suitable seasonal and acquisition windows. Avoid interpreting one
clear-sky overpass as a complete description of local heat conditions.

## Optical vegetation indicators

NDVI is calculated from pre-scaled surface reflectance:

`NDVI = (NIR - Red) / (NIR + Red)`

The helper in `heatadapt.landsat.ndvi` accepts reflectance values that have
already been scaled and quality-masked. It does not apply sensor scaling,
cloud masking or atmospheric correction. Those steps belong in the raster
ingestion pipeline.

NDVI is a vegetation greenness indicator. It does not measure shade access,
tree species, canopy height, water availability, maintenance capacity or
cooling caused by a proposed intervention.

## Per-area raster summaries

`heatadapt.zonal.summarise_raster_by_area` calculates per-polygon summaries
from a single-band indicator raster. It reprojects planning polygons to the
raster CRS, uses the raster cell-centre inclusion rule, excludes masked and
non-finite pixels, and reports:

- Number of raster pixels falling inside each polygon.
- Number and fraction of valid pixels.
- Mean, median, 90th percentile, minimum and maximum of valid pixel values.
- Raster CRS used for the calculation.

A polygon with no valid pixels receives null statistics rather than zeros.
The valid fraction is a coverage diagnostic, not a measure of data accuracy.
The function does not resample the raster, estimate missing values, weight
pixels by partial polygon overlap or convert pixel counts to area. For
geographic rasters, pixel areas vary with latitude; use a suitable projected
grid before area-based comparisons.

Example after installing the geo extra:

```python
import geopandas as gpd
from heatadapt.zonal import summarise_raster_by_area

wards = gpd.read_file("data/boundaries/processed/blantyre_wards.geojson")
summary = summarise_raster_by_area(
    "data/processed/landsat_lst_celsius.tif",
    wards,
    id_field="ward_id",
)
```

Confirm the ward identifier field in the source data before running the
example. The current Blantyre boundary archive has not yet been retrieved, so
this example is a pipeline template, not a completed city analysis.

## Planned raster pipeline

1. Search scene catalogues using a confirmed study geometry and time window.
2. Record product IDs, acquisition dates, processing levels, cloud cover and
   retrieval metadata.
3. Download only the required tiles and bands. Preserve source files unchanged.
4. Apply provider-specific fill values, scale factors and quality masks.
5. Reproject to a documented local projected CRS suitable for area calculations.
6. Align grids only after selecting and documenting a target resolution.
7. Clip to the approved boundary, retaining a boundary buffer during processing
   to avoid edge artefacts.
8. Derive per-scene indicators and multi-scene seasonal summaries.
9. Summarise valid raster pixels by ward or planning area and retain coverage
   diagnostics alongside every statistic.
10. Review maps and summary statistics before using any indicator in a decision
    model.

## STAC scene discovery

The optional STAC client searches a catalogue by collection, date interval and
approved study geometry. It returns item identifiers, acquisition metadata,
cloud-cover metadata and asset links. It does not download imagery or imply
that a scene is suitable for analysis.

The default endpoint is the Copernicus Data Space STAC API. Its current
documented endpoint is
https://stac.dataspace.copernicus.eu/v1/ and the Sentinel-2 Level-2A collection
is sentinel-2-l2a. The client also accepts another STAC endpoint and collection
IDs, so provider choice stays explicit.

Example after installing the geo extra:

```python
from heatadapt.stac import search_stac_scenes

scenes = search_stac_scenes(
    collection_ids=["sentinel-2-l2a"],
    intersects=approved_boundary_geometry,
    datetime_range="2025-10-01/2025-11-01",
    max_cloud_cover=20,
    limit=100,
)
```

Use an approved GeoJSON Polygon or MultiPolygon in WGS84 coordinates. Choose
the date interval to match the research question and season. Review scene
footprints, cloud cover, valid-pixel coverage, acquisition time and processing
metadata before selecting assets. Cloud cover is a scene-level screening field,
not a substitute for pixel-level QA.

The STAC client returns asset URLs as metadata only. Some providers protect
asset downloads or require signed URLs and authentication. Do not commit
credentials, tokens or downloaded source imagery to the repository.

## Known source rules

- Landsat Collection 2 surface temperature scale and offset: USGS documentation.
- Landsat QA_PIXEL and QA_RADSAT bit fields: USGS quality assessment documentation.
- Sentinel-2 Level-2A product discovery: Copernicus Data Space STAC API.
- WorldPop population grids: use the current product release and record its
  version, licence and estimation method. Do not mix beta/alpha releases without
  explicit version control.

The project does not yet claim to have downloaded, processed or validated
Blantyre scenes or population rasters.

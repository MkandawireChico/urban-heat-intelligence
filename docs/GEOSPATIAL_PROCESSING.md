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

wards = gpd.read_file("data/boundaries/processed/blantyre_wards_2018.geojson")
summary = summarise_raster_by_area(
    "data/processed/landsat_lst_celsius.tif",
    wards,
    id_field="source_id",
)
```

The processed 2018 ward GeoJSON uses `source_id` as the stable source identifier and `ward_name` as the display name. The geometry is provisional. The example is a processing template until suitable imagery has been downloaded and quality-checked.

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

The default endpoint is the Microsoft Planetary Computer STAC API at
https://planetarycomputer.microsoft.com/api/stac/v1. Use the `landsat-c2-l2`
collection for Landsat Collection 2 Level-2 data, including surface temperature
and surface reflectance assets. The client accepts another STAC endpoint and
collection IDs, so provider choice stays explicit.

Example after installing the geo extra:

```python
from heatadapt.stac import search_stac_scenes

scenes = search_stac_scenes(
    collection_ids=["landsat-c2-l2"],
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
Blantyre satellite scenes, population rasters or live WorldPop ward estimates.
The WorldPop client is implemented and covered by mocked tests; live API
execution remains pending. The processed boundary files are available in the
boundary delivery package and are not yet committed as full-resolution vector
files in this repository.


## Multi-scene indicator composites

`heatadapt.composite.median_composite` creates a per-pixel median from two or
more already quality-masked, single-band GeoTIFFs. All inputs must have the
same dimensions, CRS and affine transform, and each must declare nodata.
The function writes two outputs:

- A float32 median raster, with pixels lacking valid observations marked nodata.
- A uint16 valid-observation count raster, showing how many input scenes
  contributed to each pixel.

The observation-count layer is essential context. A median based on one clear
observation is not equivalent in support to a median based on ten. Inspect
counts and spatial coverage before comparing areas.

The function does not harmonise different sensors, resample grids, choose
seasons, apply QA flags, or correct differences in acquisition time and
atmospheric conditions. Select comparable scenes and quality-mask them before
compositing. A multi-scene median is a temporal summary of the supplied
observations, not a daily maximum, heatwave statistic, air-temperature
estimate or measure of personal exposure.

Example:

```python
from heatadapt.composite import median_composite

median_composite(
    [
        "data/interim/scene_2025_10_03_lst.tif",
        "data/interim/scene_2025_10_19_lst.tif",
        "data/interim/scene_2025_11_04_lst.tif",
    ],
    "data/processed/seasonal_lst_median.tif",
    "data/processed/seasonal_lst_observation_count.tif",
)
```

Only combine scenes after verifying their seasonal relevance, sensor
compatibility, QA masks, spatial grid and acquisition metadata.


## WorldPop population queries

`heatadapt.worldpop.population_in_area` queries the WorldPop Global2 R2025A
API for a supplied WGS84 Polygon or MultiPolygon and year from 2015 through
2030. `heatadapt.worldpop.population_by_areas` submits a FeatureCollection of
up to 1,000 named, uniquely identified polygons to the batch endpoint. The batch
response returns each area's total, area, density, share of the submitted total
and rank. Requests use HTTPS and do not require an API key within the documented
public limits.

Example after installing the project:

```python
import geopandas as gpd
from heatadapt.worldpop import population_in_area

wards = gpd.read_file("data/boundaries/processed/blantyre_wards.geojson")
ward = wards.iloc[0]
estimate = population_in_area(
    ward.geometry.__geo_interface__,
    year=2025,
)
print(estimate.to_dict())
```

The `/population` and `/batch` endpoints return polygon aggregates. They do
not provide cell-level population values. Use the WorldPop `/raster` endpoint
or country GeoTIFF files when cell-level overlays and population-weighted pixel
analysis are required. Do not infer a ward-level population distribution from
an aggregate total.


For ward-level analysis, submit the 26 ward polygons in one batch request.
Use the preserved `source_id` as each feature ID and `ward_name` as the label:

```python
import geopandas as gpd
from heatadapt.worldpop import population_by_areas

wards = gpd.read_file("data/boundaries/processed/blantyre_wards_2018.geojson")
features = {
    "type": "FeatureCollection",
    "features": [
        {
            "type": "Feature",
            "id": str(row.source_id),
            "properties": {"name": row.ward_name},
            "geometry": row.geometry.__geo_interface__,
        }
        for row in wards.itertuples()
    ],
}
batch = population_by_areas(features, year=2025)
print(batch.to_dict())
```

The returned ranks and shares describe only the submitted ward set and the
requested WorldPop year. They are modelled estimates, not census counts. The
client has automated tests using mocked API responses; live estimates for
Blantyre have not yet been retrieved. Keep the API response and query geometry
with the analysis outputs so the estimates remain auditable.

WorldPop Global2 R2025A provides annual estimates for 2015–2030 at roughly
100 m at the equator and is licensed CC BY 4.0. Values are modelled estimates,
not census enumerations. Record the release, year, query geometry, returned
area and source string. Check the current API catalogue and rate limits before
large batch requests. A returned population density is the API's aggregate
density for the supplied geometry; it is not a uniform within-polygon
distribution.

Source and citation:
https://api.worldpop.org/v3/documentation
https://hub.worldpop.org/doi/10.5258/SOTON/WP00839


## Reproducible data-intake commands

Install the project with its geospatial dependencies:

```bash
python -m pip install -e ".[dev,geo]"
```

Extract the supplied Blantyre boundary package into `data/boundaries/`. The
package should provide the 26-ward file and the dissolved city-outline file
under `data/boundaries/processed/`.

Retrieve 2025 WorldPop modelled population aggregates for all 26 wards:

```bash
heatadapt-data-intake worldpop \
  --boundary data/boundaries/processed/blantyre_wards_2018.geojson \
  --year 2025 \
  --output data/processed/worldpop_blantyre_wards_2025.json
```

Discover Landsat Collection 2 Level-2 scenes intersecting the dissolved
Blantyre city outline. The following is an initial dry-season to early
rainy-season screening window, not a claim that any scene is suitable:

```bash
heatadapt-data-intake landsat \
  --boundary data/boundaries/processed/blantyre_city_2018.geojson \
  --start 2025-09-01 \
  --end 2025-11-30 \
  --max-cloud 20 \
  --output data/interim/landsat_blantyre_2025_scenes.json
```

The command records the boundary file SHA-256, retrieval timestamp, request
parameters and returned records. Existing output files are protected from
accidental replacement. Pass `--force` only when intentionally replacing an
earlier result. Asset query strings are removed from the saved STAC metadata
to avoid persisting temporary access tokens.

The WorldPop output contains polygon-level modelled aggregates. The Landsat
command performs discovery only. It does not download or process imagery.
Inspect scene dates, footprints, cloud cover, asset availability and pixel QA
before selecting scenes for the temperature and vegetation pipelines. Do not
treat scene-level cloud cover as pixel-level quality control.

Both commands require network access from the machine running them. Keep the
original boundary files and generated JSON outputs with the analysis record.

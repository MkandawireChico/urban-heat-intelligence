# Initial satellite processing contract

This project begins with small, independently testable pixel transformations.
Raster reading, reprojection, spatial masking, compositing and export will be
implemented as separate pipeline stages after the study boundary and source
scenes have been confirmed.

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
9. Export indicators with units, valid-pixel counts, observation dates and
   processing configuration.
10. Review maps and summary statistics before using any indicator in a decision
    model.

## Known source rules

- Landsat Collection 2 surface temperature scale and offset: USGS documentation.
- Landsat QA_PIXEL and QA_RADSAT bit fields: USGS quality assessment documentation.
- Sentinel-2 Level-2A product discovery: Copernicus Data Space STAC API.
- WorldPop population grids: use the current product release and record its
  version, licence and estimation method. Do not mix beta/alpha releases without
  explicit version control.

The project does not yet claim to have downloaded, processed or validated
Blantyre scenes or population rasters.

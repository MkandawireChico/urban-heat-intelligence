# Boundary intake and validation

## Provisional Blantyre study boundary

The project uses the World Bank Malawi City Extents Blantyre file as a provisional geometry for pipeline development and initial spatial screening. The user approved this use on 2026-11-20 and supplied the archive.

- Dataset page: https://datacatalog.worldbank.org/search/dataset/0042046/malawi-city-extents
- Direct archive: https://datacatalogfiles.worldbank.org/ddh-published/0042046/1/DR0052566/mwi_blantyrecity.zip
- Source layer last updated: 2018-02-24
- Shapefile metadata creation date: 2016-12-15
- Licence: Creative Commons Attribution 4.0 International
- Source layer: `MWI_BlantyreCity`
- Source CRS: EPSG:32736
- Features: 26 ward polygons

The supplied archive contains one ward layer. It does not contain a separate city outline. The project derives the city extent by dissolving the 26 ward polygons, while retaining the undissolved ward layer for neighbourhood analysis. Do not describe the derived outline as a separately supplied source feature.

This is not a current legally authoritative city or planning boundary. Keep proposed extension areas separate. Compare the geometry with current Blantyre City Council and National Spatial Data Centre records before policy-facing publication.

## Validation findings

- 26 polygon features; 26 unique ward names and source IDs.
- All geometries are non-null, non-empty and structurally valid.
- Source CRS EPSG:32736; GeoJSON outputs use WGS84 EPSG:4326.
- No positive-area overlaps were detected between ward polygons.
- Dissolved extent is one connected Polygon, approximately 236.38 km².
- WGS84 bounds: 34.963576, -15.891652, 35.125586, -15.697246.
- Source `TOTAL` attribute is zero for all 26 features. It is not population data.
- Some `NAME3_` values contain spelling/capitalisation differences. Use `TA_NAME` for display names and retain original attributes.

These checks do not prove boundary completeness, absence of gaps, positional accuracy, legal authority or current planning status.

## Reproduce conversion

Install the optional geospatial dependencies:

```bash
python -m pip install -e ".[geo]"
```

Inspect the archive layer:

```bash
heatadapt-prepare-boundary data/boundaries/world_bank/blantyre_city_2018.zip --list-layers
```

Convert the ward layer:

```bash
heatadapt-prepare-boundary data/boundaries/world_bank/blantyre_city_2018.zip \
  --layer "MWI_BlantyreCity" \
  --output data/boundaries/processed/blantyre_wards_2018.geojson
```

The delivered city outline was created by dissolving all ward polygons after conversion. Keep both products separate.

Validate the ward output:

```bash
heatadapt-validate boundary data/boundaries/processed/blantyre_wards_2018.geojson
```

The converter refuses missing CRS, null or empty geometries, invalid polygons and non-polygon layers. It reprojects to WGS84, preserves feature attributes, and runs the project's GeoJSON structural validator. It does not repair invalid geometries or guess a missing CRS.

## General intake checklist

1. Preserve the original source unchanged and record its checksum.
2. Record provider, URL, retrieval date, licence, version, CRS and administrative level.
3. Confirm the geography represents Blantyre City, not Blantyre District or a different planning extent.
4. Preserve ward polygons separately from the dissolved city outline.
5. Keep validation reports with each data version.
6. Do not publish rankings until study geography and analysis units have been reviewed.

## Catalogue validation

Run `heatadapt-validate catalogue data/catalogue.json` to check provenance fields, HTTPS source links, supported status values and unique IDs.

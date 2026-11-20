# Boundary intake and validation

## Provisional Blantyre study boundary

The project will use the World Bank Malawi City Extents Blantyre City layer as a provisional geometry for pipeline development and initial spatial screening. The user approved this use on 2026-11-20.

- Dataset page: https://datacatalog.worldbank.org/search/dataset/0042046/malawi-city-extents
- Direct archive: https://datacatalogfiles.worldbank.org/ddh-published/0042046/1/DR0052566/mwi_blantyrecity.zip
- Source layer last updated: 2018-02-24
- Licence: Creative Commons Attribution 4.0 International
- Attribution: World Bank. Malawi City Extents. Blantyre City shapefile, last updated 24 February 2018. Licensed under CC BY 4.0.

This is not treated as a current legally authoritative city or planning boundary. Keep proposed extension areas separate. Compare the geometry with current Blantyre City Council and National Spatial Data Centre records before policy-facing publication.

The archive has been identified, but has not yet been retrieved or validated in this repository. Download the ZIP archive manually from the direct archive link and save it as:

`data/boundaries/world_bank/blantyre_city_2018.zip`

Record retrieval date and SHA-256. Keep the original archive unchanged. Do not commit the archive until file contents and redistribution requirements have been checked.

## Inspect and convert the source

Install the optional geospatial dependencies:

```bash
python -m pip install -e ".[geo]"
```

List the layers in the archive:

```bash
heatadapt-prepare-boundary data/boundaries/world_bank/blantyre_city_2018.zip --list-layers
```

Inspect the layer names and attributes. Select the city boundary and ward layer explicitly. Do not assume the city outline is the same layer as wards.

Convert the selected city layer:

```bash
heatadapt-prepare-boundary data/boundaries/world_bank/blantyre_city_2018.zip \
  --layer "EXACT_LAYER_NAME" \
  --output data/boundaries/processed/blantyre_city_2018.geojson
```

The converter refuses missing CRS, null or empty geometries, invalid polygons and non-polygon layers. It reprojects to WGS84 longitude/latitude, preserves feature attributes, and runs the project's GeoJSON structural validator. It does not repair invalid geometries or guess a missing CRS.

Keep ward polygons in a separate GeoJSON file using the same process. Preserve ward IDs and names for disaggregated analysis.

Validate the output:

```bash
heatadapt-validate boundary data/boundaries/processed/blantyre_city_2018.geojson
```

Review feature count, geometry types and bounds against the source metadata and a trusted map. Structural validation does not prove legal authority, positional accuracy, topology, completeness or suitability for planning.

## General intake checklist

1. Preserve the original source unchanged.
2. Record provider, URL, retrieval date, licence, version, CRS and administrative level.
3. Confirm the geography represents Blantyre City, not Blantyre District or a different planning extent.
4. Preserve city outline and ward polygons as separate layers.
5. Keep validation reports with each data version.
6. Do not publish rankings until study geography and analysis units have been reviewed.

## Catalogue validation

Run `heatadapt-validate catalogue data/catalogue.json` to check provenance fields, HTTPS source links, supported status values and unique IDs.

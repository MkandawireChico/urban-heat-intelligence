# Blantyre boundary data

The user supplied the World Bank Malawi City Extents Blantyre archive, approved for provisional pipeline development and initial spatial screening. The archive is dated 2018 and is not treated as a current legally authoritative boundary.

The archive contains one polygon layer, `MWI_BlantyreCity`, with 26 ward polygons in EPSG:32736. It does not contain a separate city-outline feature. The delivered city outline is a dissolved union of the 26 wards. The ward layer remains separate so ward IDs and names are retained.

Source provenance, SHA-256, licence, feature counts, processing summary and limitations are recorded in `world_bank/blantyre_city_2018.json`. Download the boundary delivery ZIP and extract it into `data/boundaries/` from the repository root. The `processed/` directory will then match the paths used in the processing examples. The full-resolution vectors and GeoPackage are supplied separately and are not committed to Git.

The user-facing processed package includes:
- `blantyre_wards_2018.geojson` (26 ward polygons, EPSG:4326)
- `blantyre_city_2018.geojson` (derived city outline, EPSG:4326)
- `blantyre_boundaries_2018.gpkg` (wards and city_boundary layers, EPSG:32736)
- `BOUNDARY_QA_REPORT.json`

The source `TOTAL` field is zero for every feature. Do not interpret it as population. Use `TA_NAME` for ward display names; preserve all original attributes for provenance.

Attribution: World Bank. Malawi City Extents. Blantyre City shapefile, last updated 24 February 2018. Licensed under CC BY 4.0.

Structural geometry checks passed. This does not establish legal authority, completeness, positional accuracy, or absence of gaps. Compare with current Blantyre City Council and National Spatial Data Centre records before policy-facing use.

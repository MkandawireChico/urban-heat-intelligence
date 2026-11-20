# Boundary intake and validation

The project does not yet select an authoritative Blantyre planning boundary.
The city council boundary, district boundary, planning-area boundaries and
functional urban extent are different concepts. Obtain the intended study
boundary from its custodian and record the exact version and licence.

## Intake checklist

1. Preserve the original file unchanged under `data/raw/` or `data/boundaries/`.
2. Record the provider, source URL, retrieval date, licence, version, coordinate
   reference system and any stated administrative level.
3. Confirm whether the file describes Blantyre City, Blantyre District or another
   planning geography. Do not infer this from the filename.
4. Convert a working copy to RFC 7946 GeoJSON using WGS84 longitude/latitude.
5. Run `heatadapt-validate boundary path/to/boundary.geojson`.
6. Review the reported bounds and feature count against the source metadata and
   a trusted map. Structural validation does not prove legal authority, positional
   accuracy, topology, completeness or suitability for planning.
7. Keep the validation report with the data version. Do not publish rankings until
   the study boundary and analysis units have been approved.

## Catalogue validation

Run `heatadapt-validate catalogue data/catalogue.json` to check required
provenance fields, HTTPS source links, supported status values and unique IDs.

The validator intentionally avoids downloading data. Dataset access, terms of use,
attribution and redistribution permission must be checked before retrieval.

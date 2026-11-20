# Data directory

Keep downloaded source files out of Git unless a dataset licence explicitly permits
redistribution and the project maintainer approves the addition.

- `raw/`: immutable source downloads. Record provider, URL, retrieval date, licence,
  version and checksum before analysis.
- `interim/`: temporary cleaned or reprojected data. Regenerate from raw sources.
- `processed/`: documented analysis-ready outputs. Never overwrite source files.
- `boundaries/`: candidate administrative or study-area boundaries, with source
  metadata and a validation report.

Do not commit personal data, facility-level patient data, access tokens, or large
satellite rasters. The repository catalogue records intended sources; it does not
mean those sources have been downloaded or verified.

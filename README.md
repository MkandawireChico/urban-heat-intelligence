# Urban Heat Intelligence

An open-source decision-support platform for equitable, locally feasible urban heat adaptation, beginning with Blantyre, Malawi.

## Why this project exists

Urban heat maps show where conditions are hot. City teams also need to understand where interventions are feasible, what they cost to install and maintain, who benefits, and how to prioritise limited budgets. This project focuses on that decision gap.

This is not intended to reproduce existing global heat-mapping platforms. The project will investigate how locally grounded constraints, distributional equity, lifecycle costs, uncertainty, and transparent evidence can support better neighbourhood-level adaptation decisions.

## Initial objectives

- Build a reproducible urban heat and exposure data workflow for Blantyre.
- Combine heat-related indicators with population, vulnerability, land cover, and intervention feasibility.
- Compare intervention portfolios under explicit budget and equity constraints.
- Show assumptions, data quality, uncertainty, and evidence provenance.
- Provide an accessible map-based interface and exportable planning reports.

## Scientific limits

Satellite land-surface temperature is not the same as air temperature, indoor temperature, personal heat exposure, or clinical heat risk. A spatial association between vegetation and surface temperature does not prove the cooling effect of a proposed intervention. Early versions will label screening indicators and scenario assumptions clearly. Claims about real-world cooling require suitable local validation.

## Project status

Geospatial foundation in progress. The repository includes dataset and boundary validation, Landsat Collection 2 temperature conversion, GeoTIFF processing with QA masks, NDVI helpers, STAC scene discovery, boundary preparation, and per-area raster summaries with valid-pixel coverage diagnostics. The World Bank Blantyre boundary is approved as a provisional input, but its archive has not yet been retrieved or validated. No Blantyre imagery or population raster has yet been downloaded or validated.

## Repository guide

- `docs/RESEARCH_AND_SCOPE.md`: research gap, boundaries, and validation questions.
- `docs/ARCHITECTURE.md`: planned system design.
- `docs/DATA_CATALOGUE.md`: source inventory, resolution, use and limitations.
- `docs/GEOSPATIAL_PROCESSING.md`: satellite indicator formulas, QA rules, zonal summaries and raster workflow.
- `docs/GEOJSON_BOUNDARY_WORKFLOW.md`: boundary intake and validation rules.
- `data/catalogue.json`: machine-readable dataset provenance register.
- `src/heatadapt/`: core Python decision-support and input-validation package.
- `tests/`: automated tests.

## Development

Python 3.11 or later is recommended.

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\\Scripts\\activate
python -m pip install -e ".[dev,geo]"
pytest
ruff check .
mypy
```

The geo extra includes GeoPandas, NumPy, Rasterio and the STAC client. Install it for the complete test suite and geospatial processing.

Validate the source catalogue with `heatadapt-validate catalogue data/catalogue.json`.
Validate a candidate WGS84 GeoJSON boundary with `heatadapt-validate boundary path/to/boundary.geojson`.

## Principles

1. Evidence before claims.
2. Equity is explicit, not an afterthought.
3. Local feasibility matters as much as theoretical cooling potential.
4. Every score must be explainable.
5. Uncertainty and missing data must be visible.
6. Community and municipal knowledge must inform the model.

## Licence

MIT. See [LICENSE](LICENSE).

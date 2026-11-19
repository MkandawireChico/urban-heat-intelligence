# Technical architecture

## Design goals

- Reproducible analysis with explicit data lineage.
- Separate data ingestion, geospatial processing, decision logic, API, and presentation.
- Keep the decision engine testable without downloading large spatial datasets.
- Make assumptions configurable and visible.
- Avoid coupling scientific calculations to frontend components.

## Planned components

### Data catalogue and provenance

A registry of input datasets with source, licence, spatial and temporal coverage, resolution, processing steps, known limitations, and retrieval date.

### Geospatial pipeline

Python tooling will validate, harmonise, and derive spatial indicators from suitable sources. Candidate technologies include GeoPandas, Rasterio, Xarray, Rioxarray, and DuckDB. Final choices depend on actual data formats and deployment constraints.

### Decision engine

A pure Python package will represent candidate interventions and planning areas, calculate transparent screening indicators, apply explicit budget and feasibility constraints, compare alternative equity and cost assumptions, and report why a candidate was ranked or excluded.

The first implementation is deliberately data-agnostic. It does not pretend to estimate physical cooling effects from unvalidated proxies.

### API and interface

FastAPI is the planned service layer. A React-based map and scenario interface is planned. Mapping technology will be selected after the spatial data contract is defined.

### Quality and reproducibility

- Pytest for unit and integration tests.
- Ruff for linting and formatting.
- Type hints for core interfaces.
- GitHub Actions for automated checks.
- Versioned configuration and generated reports.

## Initial repository layout

```text
.
├── docs/
├── src/
│   └── heatadapt/
├── tests/
├── pyproject.toml
├── README.md
└── .gitignore
```

## Development sequence

1. Research scope, data inventory, and scientific safeguards.
2. Transparent decision-engine primitives and tests.
3. Blantyre data inventory and ingestion prototypes.
4. Geospatial indicator pipeline.
5. Scenario and uncertainty analysis.
6. API and map interface.
7. Local review, validation, and deployment.

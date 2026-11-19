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

The initial input layer is implemented. A JSON catalogue records each dataset's provider, source URL, licence, spatial and temporal coverage, intended use, limitations and acquisition status. A validator rejects incomplete records and duplicate identifiers.

A dependency-light GeoJSON validator checks Polygon and MultiPolygon FeatureCollections, WGS84 coordinate ranges, non-empty geometries and closed linear rings. It reports feature counts, geometry types and bounds. This is a structural check only. It does not establish administrative authority, topology, positional accuracy or completeness.

GeoPandas and Rasterio are optional dependencies. Python 3.11 compatibility is retained by constraining Rasterio below 1.5; the base package does not install the geospatial stack. Candidate later tools include Xarray, Rioxarray and DuckDB. Final choices depend on source formats and deployment constraints.

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
├── data/
│   ├── catalogue.json
│   └── README.md
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
3. Dataset provenance register and boundary intake validation.
4. Confirm an authoritative Blantyre study boundary and analysis units.
5. Acquire and quality-check source datasets.
6. Geospatial indicator pipeline.
7. Scenario and uncertainty analysis.
8. API and map interface.
9. Local review, validation, and deployment.

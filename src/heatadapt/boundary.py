"""Prepare a selected source layer as validated WGS84 GeoJSON."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from heatadapt.geojson import validate_boundary_geojson


def prepare_boundary_frame(frame: Any) -> Any:
    """Validate polygon features and convert a geospatial frame to EPSG:4326."""
    if frame.empty:
        raise ValueError("Selected boundary layer contains no features")
    if frame.crs is None:
        raise ValueError("Source layer has no CRS; do not guess its coordinate system")
    if frame.geometry.isna().any():
        raise ValueError("Selected boundary layer contains null geometries")
    if frame.geometry.is_empty.any():
        raise ValueError("Selected boundary layer contains empty geometries")
    if not frame.geometry.is_valid.all():
        raise ValueError("Selected boundary layer contains invalid geometries")
    allowed = {"Polygon", "MultiPolygon"}
    found = set(frame.geometry.geom_type.unique())
    if not found.issubset(allowed):
        raise ValueError(f"Only polygon geometries are supported; found {sorted(found)}")
    return frame.to_crs("EPSG:4326")


def convert_boundary_archive(
    source: str | Path,
    output: str | Path,
    layer: str,
) -> dict[str, object]:
    """Convert one explicitly selected vector layer from an archive to GeoJSON."""
    import geopandas as gpd

    source_path = Path(source)
    output_path = Path(output)
    if not source_path.is_file():
        raise FileNotFoundError(source_path)
    if not layer.strip():
        raise ValueError("An explicit source layer name is required")

    frame = gpd.read_file(source_path, layer=layer)
    prepared = prepare_boundary_frame(frame)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    prepared.to_file(output_path, driver="GeoJSON", index=False)
    summary = validate_boundary_geojson(output_path)
    return {
        "source": str(source_path),
        "source_layer": layer,
        "output": str(output_path),
        "source_crs": str(frame.crs),
        "output_crs": "EPSG:4326",
        "feature_count": summary.feature_count,
        "geometry_types": list(summary.geometry_types),
        "bounds": list(summary.bounds),
    }


def main() -> None:
    """List source archive layers or convert one explicitly selected layer."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", help="Source ZIP archive or vector file")
    parser.add_argument("--list-layers", action="store_true")
    parser.add_argument("--layer", help="Exact source layer name to convert")
    parser.add_argument("--output", help="Destination GeoJSON path")
    args = parser.parse_args()

    import geopandas as gpd

    if args.list_layers:
        for name in gpd.list_layers(args.source)["name"].tolist():
            print(name)
        return
    if not args.layer or not args.output:
        parser.error("--layer and --output are required unless --list-layers is used")
    import json

    print(json.dumps(convert_boundary_archive(args.source, args.output, args.layer), indent=2))


if __name__ == "__main__":
    main()

"""Dependency-light validation for GeoJSON planning boundaries."""

from __future__ import annotations

import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import TypeAlias

Position: TypeAlias = list[float]


@dataclass(frozen=True, slots=True)
class BoundarySummary:
    """Basic structural summary; does not certify administrative authority."""

    feature_count: int
    geometry_types: tuple[str, ...]
    bounds: tuple[float, float, float, float]


def _positions(value: object) -> list[Position]:
    """Flatten nested GeoJSON coordinates into longitude/latitude positions."""
    if not isinstance(value, list) or not value:
        raise ValueError("Geometry coordinates must be non-empty arrays")
    if len(value) >= 2 and all(isinstance(item, (int, float)) for item in value[:2]):
        if len(value) < 2:
            raise ValueError("A coordinate must contain longitude and latitude")
        position = [float(value[0]), float(value[1])]
        if not all(math.isfinite(number) for number in position):
            raise ValueError("Coordinates must be finite numbers")
        longitude, latitude = position
        if not -180 <= longitude <= 180 or not -90 <= latitude <= 90:
            raise ValueError("Coordinates must use WGS84 longitude/latitude ranges")
        return [position]
    flattened: list[Position] = []
    for child in value:
        flattened.extend(_positions(child))
    return flattened


def _validate_polygon_rings(coordinates: object) -> None:
    if not isinstance(coordinates, list) or not coordinates:
        raise ValueError("Polygon must contain at least one linear ring")
    for ring in coordinates:
        if not isinstance(ring, list) or len(ring) < 4:
            raise ValueError("Each linear ring must contain at least four positions")
        positions = _positions(ring)
        if positions[0] != positions[-1]:
            raise ValueError("Each linear ring must be closed")


def validate_boundary_geojson(path: str | Path) -> BoundarySummary:
    """Validate a Polygon/MultiPolygon FeatureCollection in RFC 7946 coordinates."""
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or payload.get("type") != "FeatureCollection":
        raise ValueError("Boundary file must be a GeoJSON FeatureCollection")
    features = payload.get("features")
    if not isinstance(features, list) or not features:
        raise ValueError("FeatureCollection must contain at least one feature")

    all_positions: list[Position] = []
    geometry_types: set[str] = set()
    for index, feature in enumerate(features):
        if not isinstance(feature, dict) or feature.get("type") != "Feature":
            raise ValueError(f"Feature {index} is malformed")
        geometry = feature.get("geometry")
        if not isinstance(geometry, dict):
            raise ValueError(f"Feature {index} has no geometry")
        geometry_type = geometry.get("type")
        coordinates = geometry.get("coordinates")
        if geometry_type == "Polygon":
            _validate_polygon_rings(coordinates)
        elif geometry_type == "MultiPolygon":
            if not isinstance(coordinates, list) or not coordinates:
                raise ValueError("MultiPolygon must contain at least one polygon")
            for polygon in coordinates:
                _validate_polygon_rings(polygon)
        else:
            raise ValueError("Only Polygon and MultiPolygon geometries are supported")
        all_positions.extend(_positions(coordinates))
        geometry_types.add(str(geometry_type))

    longitudes = [position[0] for position in all_positions]
    latitudes = [position[1] for position in all_positions]
    return BoundarySummary(
        feature_count=len(features),
        geometry_types=tuple(sorted(geometry_types)),
        bounds=(min(longitudes), min(latitudes), max(longitudes), max(latitudes)),
    )

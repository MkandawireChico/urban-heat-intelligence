"""Tests for dependency-light GeoJSON validation."""

import json

import pytest

from heatadapt.geojson import validate_boundary_geojson


def _feature_collection(coordinates: list) -> dict:
    return {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {"name": "Example"},
                "geometry": {"type": "Polygon", "coordinates": coordinates},
            }
        ],
    }


def test_valid_polygon_returns_bounds(tmp_path) -> None:
    coordinates = [[
        [34.9, -15.9],
        [35.0, -15.9],
        [35.0, -15.8],
        [34.9, -15.8],
        [34.9, -15.9],
    ]]
    path = tmp_path / "boundary.geojson"
    path.write_text(json.dumps(_feature_collection(coordinates)), encoding="utf-8")

    summary = validate_boundary_geojson(path)

    assert summary.feature_count == 1
    assert summary.geometry_types == ("Polygon",)
    assert summary.bounds == (34.9, -15.9, 35.0, -15.8)


def test_unclosed_ring_is_rejected(tmp_path) -> None:
    coordinates = [[[34.9, -15.9], [35.0, -15.9], [35.0, -15.8], [34.9, -15.8]]]
    path = tmp_path / "bad.geojson"
    path.write_text(json.dumps(_feature_collection(coordinates)), encoding="utf-8")
    with pytest.raises(ValueError, match="closed"):
        validate_boundary_geojson(path)


def test_out_of_range_coordinates_are_rejected(tmp_path) -> None:
    coordinates = [[[200, -15], [201, -15], [201, -14], [200, -14], [200, -15]]]
    path = tmp_path / "bad.geojson"
    path.write_text(json.dumps(_feature_collection(coordinates)), encoding="utf-8")
    with pytest.raises(ValueError, match="WGS84"):
        validate_boundary_geojson(path)


def test_non_polygon_geometry_is_rejected(tmp_path) -> None:
    payload = {
        "type": "FeatureCollection",
        "features": [{
            "type": "Feature",
            "properties": {},
            "geometry": {"type": "Point", "coordinates": [35, -15]},
        }],
    }
    path = tmp_path / "point.geojson"
    path.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(ValueError, match="Only Polygon"):
        validate_boundary_geojson(path)

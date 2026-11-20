from __future__ import annotations

import io
import json
from urllib.error import HTTPError, URLError
from urllib.request import Request

import pytest

from heatadapt.worldpop import population_by_areas, population_in_area


POLYGON = {
    "type": "Polygon",
    "coordinates": [[[33.7, -15.9], [33.8, -15.9], [33.8, -15.8], [33.7, -15.8], [33.7, -15.9]]],
}


class _Response:
    def __init__(self, payload):
        self.payload = json.dumps(payload).encode()

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def read(self):
        return self.payload


def _payload(**overrides):
    values = {
        "total_population": 12500.5,
        "area_km2": 12.5,
        "population_density": 1000.04,
        "data_year": 2025,
        "data_source": "WorldPop Global2 R2025A, 100 m",
        "processing_time_ms": 42,
    }
    return values | overrides


def test_queries_worldpop_and_returns_provenance(monkeypatch):
    captured: list[Request] = []

    def fake_urlopen(request: Request, timeout: float = 60.0):
        captured.append(request)
        return _Response(_payload())

    monkeypatch.setattr("heatadapt.worldpop.urlopen", fake_urlopen)
    result = population_in_area(POLYGON, year=2025)

    request = captured[0]
    sent = json.loads(request.data)
    assert request.full_url == "https://api.worldpop.org/v3/population"
    assert sent == {"geojson": POLYGON, "year": 2025}
    assert result.total_population == 12500.5
    assert result.data_source == "WorldPop Global2 R2025A, 100 m"
    assert result.processing_time_ms == 42


@pytest.mark.parametrize("year", [2014, 2031])
def test_rejects_unsupported_year(year):
    with pytest.raises(ValueError, match="2015 through 2030"):
        population_in_area(POLYGON, year=year)


def test_rejects_non_wgs84_coordinate_values():
    invalid = {
        "type": "Polygon",
        "coordinates": [[[300, 0], [301, 0], [301, 1], [300, 0]]],
    }
    with pytest.raises(ValueError, match="WGS84"):
        population_in_area(invalid, year=2025)


def test_rejects_non_polygon_geometry():
    with pytest.raises(ValueError, match="Polygon or MultiPolygon"):
        population_in_area({"type": "Point", "coordinates": [33.8, -15.8]}, year=2025)


def test_rejects_mismatched_year_returned_by_api(monkeypatch):
    def fake_urlopen(_request: Request, timeout: float = 60.0):
        return _Response(_payload(data_year=2024))

    monkeypatch.setattr("heatadapt.worldpop.urlopen", fake_urlopen)
    with pytest.raises(ValueError, match="requested"):
        population_in_area(POLYGON, year=2025)


def test_reports_api_error_response(monkeypatch):
    api_error = HTTPError(
        "https://api.worldpop.org/v3/population",
        503,
        "Unavailable",
        {},
        io.BytesIO(b'{"error":"data_unavailable","message":"No data"}'),
    )

    def fake_urlopen(_request: Request, timeout: float = 60.0):
        raise api_error

    monkeypatch.setattr("heatadapt.worldpop.urlopen", fake_urlopen)
    with pytest.raises(RuntimeError, match="No data"):
        population_in_area(POLYGON, year=2025)


def test_reports_network_errors(monkeypatch):
    def fake_urlopen(_request: Request, timeout: float = 60.0):
        raise URLError("offline")

    monkeypatch.setattr("heatadapt.worldpop.urlopen", fake_urlopen)
    with pytest.raises(RuntimeError, match="Unable to reach"):
        population_in_area(POLYGON, year=2025)



def _batch_features():
    return {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "id": "ward-01",
                "properties": {"name": "Central"},
                "geometry": POLYGON,
            },
            {
                "type": "Feature",
                "id": "ward-02",
                "properties": {"name": "North"},
                "geometry": POLYGON,
            },
        ],
    }


def _batch_payload():
    return {
        "data_year": 2025,
        "total": {"total_population": 1500.0, "area_km2": 2.0},
        "features": [
            {
                "id": "ward-01",
                "name": "Central",
                "area_km2": 1.0,
                "total_population": 1000.0,
                "population_density": 1000.0,
                "share_of_total": 0.6667,
                "rank": 1,
            },
            {
                "id": "ward-02",
                "name": "North",
                "area_km2": 1.0,
                "total_population": 500.0,
                "population_density": 500.0,
                "share_of_total": 0.3333,
                "rank": 2,
            },
        ],
    }


def test_batch_queries_all_areas_and_preserves_ids(monkeypatch):
    captured: list[Request] = []

    def fake_urlopen(req: Request, timeout: float = 60.0):
        captured.append(req)
        return _Response(_batch_payload())

    monkeypatch.setattr("heatadapt.worldpop.urlopen", fake_urlopen)
    result = population_by_areas(_batch_features(), year=2025)

    sent = json.loads(captured[0].data)
    assert captured[0].full_url == "https://api.worldpop.org/v3/batch"
    assert sent == {"features": _batch_features(), "year": 2025}
    assert result.total_population == 1500.0
    assert [area.area_id for area in result.areas] == ["ward-01", "ward-02"]
    assert result.areas[0].name == "Central"
    assert result.areas[0].rank == 1


@pytest.mark.parametrize(
    ("features", "message"),
    [
        ({"type": "FeatureCollection", "features": []}, "between 1 and 1,000"),
        (
            {
                "type": "FeatureCollection",
                "features": [
                    {"type": "Feature", "properties": {}, "geometry": POLYGON}
                ],
            },
            "stable feature id",
        ),
    ],
)
def test_batch_rejects_invalid_feature_collections(features, message):
    with pytest.raises(ValueError, match=message):
        population_by_areas(features, year=2025)


def test_batch_rejects_duplicate_ids():
    features = _batch_features()
    features["features"][1]["id"] = "ward-01"
    with pytest.raises(ValueError, match="Duplicate area id"):
        population_by_areas(features, year=2025)


def test_batch_rejects_mismatched_response_ids(monkeypatch):
    payload = _batch_payload()
    payload["features"][1]["id"] = "ward-03"

    def fake_urlopen(req: Request, timeout: float = 60.0):
        return _Response(payload)

    monkeypatch.setattr("heatadapt.worldpop.urlopen", fake_urlopen)
    with pytest.raises(ValueError, match="IDs do not match"):
        population_by_areas(_batch_features(), year=2025)

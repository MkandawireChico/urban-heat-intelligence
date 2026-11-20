from __future__ import annotations

import io
import json
import unittest.mock
import urllib.error

import pytest

from heatadapt.worldpop import population_in_area


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


def test_queries_worldpop_and_returns_provenance():
    with unittest.mock.patch("heatadapt.worldpop.urlopen", return_value=_Response(_payload())) as mocked:
        result = population_in_area(POLYGON, year=2025)

    request = mocked.call_args.args[0]
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


def test_rejects_mismatched_year_returned_by_api():
    with unittest.mock.patch(
        "heatadapt.worldpop.urlopen",
        return_value=_Response(_payload(data_year=2024)),
    ):
        with pytest.raises(ValueError, match="requested"):
            population_in_area(POLYGON, year=2025)


def test_reports_api_error_response():
    error = urllib.error.HTTPError(
        "https://api.worldpop.org/v3/population",
        503,
        "Unavailable",
        {},
        io.BytesIO(b'{"error":"data_unavailable","message":"No data"}'),
    )
    with unittest.mock.patch("heatadapt.worldpop.urlopen", side_effect=error):
        with pytest.raises(RuntimeError, match="No data"):
            population_in_area(POLYGON, year=2025)


def test_reports_network_errors():
    with unittest.mock.patch("heatadapt.worldpop.urlopen", side_effect=urllib.error.URLError("offline")):
        with pytest.raises(RuntimeError, match="Unable to reach"):
            population_in_area(POLYGON, year=2025)

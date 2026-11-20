"""Query WorldPop Global2 population estimates for a supplied polygon."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

DEFAULT_WORLDPOP_API = "https://api.worldpop.org/v3"
SUPPORTED_YEARS = frozenset(range(2015, 2031))


@dataclass(frozen=True, slots=True)
class PopulationEstimate:
    """Auditable population summary returned by the WorldPop API."""

    total_population: float
    area_km2: float
    population_density: float
    data_year: int
    data_source: str
    processing_time_ms: int | None

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serializable representation."""
        return asdict(self)


def population_in_area(
    geometry: dict[str, Any],
    *,
    year: int,
    endpoint: str = DEFAULT_WORLDPOP_API,
    timeout_seconds: float = 60.0,
) -> PopulationEstimate:
    """Return a WorldPop population estimate for a WGS84 GeoJSON polygon.

    This is an API-derived polygon aggregate, not a locally downloaded raster.
    The geometry must be a Polygon or MultiPolygon in longitude/latitude order.
    The API release and source are retained in the result for provenance.
    """
    if year not in SUPPORTED_YEARS:
        raise ValueError("WorldPop Global2 R2025A supports years 2015 through 2030")
    if timeout_seconds <= 0:
        raise ValueError("timeout_seconds must be positive")
    _validate_geometry(geometry)

    payload = json.dumps({"geojson": geometry, "year": year}).encode("utf-8")
    request = Request(
        f"{endpoint.rstrip('/')}/population",
        data=payload,
        headers={"Content-Type": "application/json", "Accept": "application/json"},
        method="POST",
    )
    try:
        with urlopen(request, timeout=timeout_seconds) as response:
            result = json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"WorldPop API returned HTTP {exc.code}: {detail}") from exc
    except URLError as exc:
        raise RuntimeError(f"Unable to reach WorldPop API: {exc.reason}") from exc
    except (TimeoutError, OSError) as exc:
        raise RuntimeError(f"WorldPop API request failed: {exc}") from exc

    if not isinstance(result, dict):
        raise ValueError("WorldPop API returned an unexpected response")
    required = ("total_population", "area_km2", "population_density", "data_year", "data_source")
    missing = [key for key in required if key not in result]
    if missing:
        if "error" in result:
            raise RuntimeError(f"WorldPop API error: {result.get('message', result['error'])}")
        raise ValueError(f"WorldPop API response is missing fields: {missing}")

    try:
        estimate = PopulationEstimate(
            total_population=float(result["total_population"]),
            area_km2=float(result["area_km2"]),
            population_density=float(result["population_density"]),
            data_year=int(result["data_year"]),
            data_source=str(result["data_source"]),
            processing_time_ms=(
                int(result["processing_time_ms"])
                if result.get("processing_time_ms") is not None
                else None
            ),
        )
    except (TypeError, ValueError) as exc:
        raise ValueError("WorldPop API returned invalid population values") from exc

    if estimate.data_year != year:
        raise ValueError(
            f"WorldPop returned year {estimate.data_year}, but year {year} was requested"
        )
    if (
        estimate.total_population < 0
        or estimate.area_km2 <= 0
        or estimate.population_density < 0
    ):
        raise ValueError("WorldPop returned negative population or non-positive area")
    return estimate


def _validate_geometry(geometry: dict[str, Any]) -> None:
    if geometry.get("type") not in {"Polygon", "MultiPolygon"}:
        raise ValueError("geometry must be a GeoJSON Polygon or MultiPolygon")
    coordinates = geometry.get("coordinates")
    if not isinstance(coordinates, list) or not coordinates:
        raise ValueError("geometry must contain non-empty coordinates")
    # Coordinate ranges are checked recursively without altering source geometry.
    def visit(value: Any) -> None:
        if (
            isinstance(value, (list, tuple))
            and len(value) >= 2
            and isinstance(value[0], (int, float))
            and isinstance(value[1], (int, float))
        ):
            longitude, latitude = float(value[0]), float(value[1])
            if not -180 <= longitude <= 180 or not -90 <= latitude <= 90:
                raise ValueError("geometry coordinates must be WGS84 longitude/latitude")
            return
        if isinstance(value, (list, tuple)):
            for child in value:
                visit(child)
            return
        raise ValueError("geometry contains malformed coordinates")

    visit(coordinates)

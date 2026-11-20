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


@dataclass(frozen=True, slots=True)
class AreaPopulationEstimate:
    """Population summary for one feature in a WorldPop batch response."""

    area_id: str
    name: str
    area_km2: float
    total_population: float
    population_density: float
    share_of_total: float
    rank: int

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class PopulationBatch:
    """Auditable population summary for a set of planning areas."""

    data_year: int
    total_population: float
    area_km2: float
    areas: tuple[AreaPopulationEstimate, ...]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def population_by_areas(
    features: dict[str, Any],
    *,
    year: int,
    endpoint: str = DEFAULT_WORLDPOP_API,
    timeout_seconds: float = 60.0,
) -> PopulationBatch:
    """Query the WorldPop batch endpoint for up to 1,000 WGS84 polygons."""
    if year not in SUPPORTED_YEARS:
        raise ValueError("WorldPop Global2 R2025A supports years 2015 through 2030")
    if timeout_seconds <= 0:
        raise ValueError("timeout_seconds must be positive")
    if features.get("type") != "FeatureCollection":
        raise ValueError("features must be a GeoJSON FeatureCollection")
    feature_list = features.get("features")
    if not isinstance(feature_list, list) or not 1 <= len(feature_list) <= 1000:
        raise ValueError("FeatureCollection must contain between 1 and 1,000 areas")

    identifiers: set[str] = set()
    for feature in feature_list:
        if not isinstance(feature, dict) or feature.get("type") != "Feature":
            raise ValueError("Each area must be a GeoJSON Feature")
        properties = feature.get("properties") or {}
        area_id = feature.get("id", properties.get("id"))
        if area_id is None or not str(area_id).strip():
            raise ValueError("Each area must have a stable feature id or properties.id")
        identifier = str(area_id)
        if identifier in identifiers:
            raise ValueError(f"Duplicate area id: {identifier}")
        identifiers.add(identifier)
        geometry = feature.get("geometry")
        if not isinstance(geometry, dict):
            raise ValueError(f"Area {identifier} has no geometry")
        _validate_geometry(geometry)

    payload = json.dumps({"features": features, "year": year}).encode("utf-8")
    request = Request(
        f"{endpoint.rstrip('/')}/batch",
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
        raise ValueError("WorldPop batch API returned an unexpected response")
    if "error" in result:
        raise RuntimeError(f"WorldPop API error: {result.get('message', result['error'])}")
    if result.get("data_year") != year:
        raise ValueError(
            f"WorldPop returned year {result.get('data_year')}, but year {year} was requested"
        )
    total = result.get("total")
    response_areas = result.get("features")
    if not isinstance(total, dict) or not isinstance(response_areas, list):
        raise ValueError("WorldPop batch response is missing total or features")
    if len(response_areas) != len(feature_list):
        raise ValueError("WorldPop batch response count does not match submitted areas")
    try:
        total_population = float(total["total_population"])
        total_area = float(total["area_km2"])
        areas = tuple(
            AreaPopulationEstimate(
                area_id=str(item["id"]),
                name=str(item["name"]),
                area_km2=float(item["area_km2"]),
                total_population=float(item["total_population"]),
                population_density=float(item["population_density"]),
                share_of_total=float(item["share_of_total"]),
                rank=int(item["rank"]),
            )
            for item in response_areas
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError("WorldPop batch response contains invalid area values") from exc

    if {area.area_id for area in areas} != identifiers:
        raise ValueError("WorldPop batch response IDs do not match submitted area IDs")
    if (
        total_population < 0
        or total_area <= 0
        or any(
            area.area_km2 <= 0
            or area.total_population < 0
            or area.population_density < 0
            or not 0 <= area.share_of_total <= 1
            or area.rank < 1
            for area in areas
        )
    ):
        raise ValueError("WorldPop batch response contains invalid population values")
    return PopulationBatch(year, total_population, total_area, areas)


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

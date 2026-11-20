"""Download a clipped WorldPop population GeoTIFF for a WGS84 polygon."""

from __future__ import annotations

import hashlib
import json
import math
import os
import tempfile
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from heatadapt.worldpop import DEFAULT_WORLDPOP_API, SUPPORTED_YEARS, _validate_geometry


@dataclass(frozen=True, slots=True)
class PopulationRasterMetadata:
    """Response metadata and checksums for one downloaded WorldPop raster."""

    data_year: int
    resolution: str
    data_source: str
    total_population: float | None
    area_km2: float | None
    content_type: str
    file_bytes: int
    file_sha256: str
    source_endpoint: str

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serializable representation."""
        return asdict(self)


def download_population_raster(
    geometry: dict[str, Any],
    *,
    year: int,
    output_path: Path,
    resolution: str = "100m",
    endpoint: str = DEFAULT_WORLDPOP_API,
    timeout_seconds: float = 120.0,
    force: bool = False,
) -> PopulationRasterMetadata:
    """Download WorldPop people-per-cell GeoTIFF clipped to a polygon.

    The returned raster is a modelled population surface, not a census count.
    No resampling or reprojection is performed. The original EPSG:4326 grid is
    retained. A JSON sidecar records the request, response headers and hash.
    """
    if year not in SUPPORTED_YEARS:
        raise ValueError("WorldPop Global2 R2025A supports years 2015 through 2030")
    if resolution not in {"100m", "1km"}:
        raise ValueError("resolution must be '100m' or '1km'")
    if not math.isfinite(timeout_seconds) or timeout_seconds <= 0:
        raise ValueError("timeout_seconds must be a positive finite number")
    _validate_geometry(geometry)

    output_path = Path(output_path)
    metadata_path = output_path.with_suffix(output_path.suffix + ".json")
    if not force and (output_path.exists() or metadata_path.exists()):
        raise FileExistsError(
            f"Raster or metadata output already exists: {output_path}. Pass force=True to replace."
        )
    output_path.parent.mkdir(parents=True, exist_ok=True)

    request_body = json.dumps(
        {"geojson": geometry, "year": year, "resolution": resolution, "layer": "population"}
    ).encode("utf-8")
    request = Request(
        f"{endpoint.rstrip('/')}/raster",
        data=request_body,
        headers={"Content-Type": "application/json", "Accept": "image/tiff"},
        method="POST",
    )
    try:
        with urlopen(request, timeout=timeout_seconds) as response:
            content_type = response.headers.get("Content-Type", "").split(";", 1)[0].strip()
            body = response.read()
            total_header = response.headers.get("X-Total-Population")
            area_header = response.headers.get("X-Area-Km2")
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"WorldPop raster API returned HTTP {exc.code}: {detail}") from exc
    except URLError as exc:
        raise RuntimeError(f"Unable to reach WorldPop raster API: {exc.reason}") from exc
    except (TimeoutError, OSError) as exc:
        raise RuntimeError(f"WorldPop raster request failed: {exc}") from exc

    if content_type not in {"image/tiff", "application/octet-stream"}:
        try:
            detail = json.loads(body.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            detail = body[:500].decode("utf-8", errors="replace")
        if isinstance(detail, dict):
            message = detail.get("message") or detail.get("error") or detail
        else:
            message = detail
        raise RuntimeError(f"WorldPop did not return a GeoTIFF: {message}")
    if len(body) < 8 or body[:4] not in {b"II*\x00", b"MM\x00*", b"II+\x00", b"MM\x00+"}:
        raise ValueError("WorldPop response does not have a valid TIFF file signature")

    try:
        total_population = float(total_header) if total_header is not None else None
        area_km2 = float(area_header) if area_header is not None else None
    except ValueError as exc:
        raise ValueError("WorldPop returned invalid raster summary headers") from exc
    if total_population is not None and (
        not math.isfinite(total_population) or total_population < 0
    ):
        raise ValueError("WorldPop returned an invalid total population header")
    if area_km2 is not None and (not math.isfinite(area_km2) or area_km2 <= 0):
        raise ValueError("WorldPop returned an invalid area header")

    digest = hashlib.sha256(body).hexdigest()
    metadata = PopulationRasterMetadata(
        data_year=year,
        resolution=resolution,
        data_source="WorldPop Global2 R2025A",
        total_population=total_population,
        area_km2=area_km2,
        content_type=content_type,
        file_bytes=len(body),
        file_sha256=digest,
        source_endpoint=f"{endpoint.rstrip('/')}/raster",
    )
    sidecar = {
        "record_type": "worldpop_population_raster",
        "retrieved_at_utc": __import__("datetime").datetime.now(
            __import__("datetime").UTC
        ).isoformat(),
        "request": {
            "year": year,
            "resolution": resolution,
            "layer": "population",
            "geometry": geometry,
        },
        "metadata": metadata.to_dict(),
        "interpretation": (
            "Modelled people-per-cell estimates, not census counts. "
            "EPSG:4326 source grid retained without resampling."
        ),
        "nodata": "WorldPop documentation specifies -99999 outside the area and where data has no value; zero means no modelled residents.",
    }

    raster_temp: str | None = None
    sidecar_temp: str | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="wb", dir=output_path.parent, prefix=f".{output_path.name}.", delete=False
        ) as temporary:
            raster_temp = temporary.name
            temporary.write(body)
            temporary.flush()
            os.fsync(temporary.fileno())
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=metadata_path.parent,
            prefix=f".{metadata_path.name}.",
            delete=False,
        ) as temporary:
            sidecar_temp = temporary.name
            json.dump(sidecar, temporary, indent=2, sort_keys=True)
            temporary.write("\n")
            temporary.flush()
            os.fsync(temporary.fileno())
        os.replace(raster_temp, output_path)
        raster_temp = None
        os.replace(sidecar_temp, metadata_path)
        sidecar_temp = None
    finally:
        for temporary_path in (raster_temp, sidecar_temp):
            if temporary_path is not None:
                try:
                    os.unlink(temporary_path)
                except FileNotFoundError:
                    pass

    return metadata

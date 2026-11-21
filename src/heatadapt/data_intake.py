"""Reproducible command-line intake for WorldPop and Landsat STAC metadata."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections.abc import Sequence
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit, urlunsplit

from heatadapt.stac import DEFAULT_STAC_ENDPOINT, search_stac_scenes
from heatadapt.worldpop import DEFAULT_WORLDPOP_API, population_by_areas
from heatadapt.worldpop_raster import download_population_raster


def _read_feature_collection(path: Path) -> tuple[dict[str, Any], str]:
    raw = path.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    try:
        document = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid GeoJSON JSON: {exc}") from exc
    if not isinstance(document, dict) or document.get("type") != "FeatureCollection":
        raise ValueError("Input must be a GeoJSON FeatureCollection")
    features = document.get("features")
    if not isinstance(features, list) or not features:
        raise ValueError("GeoJSON FeatureCollection must contain at least one feature")
    return document, digest


def _population_features(
    collection: dict[str, Any],
    *,
    id_field: str,
    name_field: str,
) -> dict[str, Any]:
    selected: list[dict[str, Any]] = []
    for index, feature in enumerate(collection["features"]):
        if not isinstance(feature, dict):
            raise ValueError(f"Feature {index} is not a GeoJSON Feature")
        properties = feature.get("properties") or {}
        area_id = feature.get("id", properties.get(id_field))
        name = properties.get(name_field)
        geometry = feature.get("geometry")
        if area_id is None or not str(area_id).strip():
            raise ValueError(f"Feature {index} is missing the ID field {id_field!r}")
        if name is None or not str(name).strip():
            raise ValueError(f"Feature {index} is missing the name field {name_field!r}")
        if not isinstance(geometry, dict):
            raise ValueError(f"Feature {index} is missing polygon geometry")
        selected.append(
            {
                "type": "Feature",
                "id": str(area_id),
                "properties": {"name": str(name)},
                "geometry": geometry,
            }
        )
    return {"type": "FeatureCollection", "features": selected}


def _single_geometry(collection: dict[str, Any]) -> dict[str, Any]:
    if len(collection["features"]) != 1:
        raise ValueError(
            "Landsat discovery requires a single dissolved city-boundary feature. "
            "Use the city outline GeoJSON, not the 26-ward file."
        )
    geometry = collection["features"][0].get("geometry")
    if not isinstance(geometry, dict):
        raise ValueError("City boundary feature is missing geometry")
    return geometry


def _safe_asset_href(href: str) -> str:
    parts = urlsplit(href)
    return urlunsplit((parts.scheme, parts.netloc, parts.path, "", ""))


def _write_output(path: Path, payload: dict[str, Any], *, force: bool) -> None:
    if path.exists() and not force:
        raise FileExistsError(f"Output already exists: {path}. Pass --force to replace it.")
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    temporary.replace(path)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="heatadapt-data-intake",
        description="Create provenance-recorded WorldPop and Landsat discovery outputs.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    population = subparsers.add_parser(
        "worldpop", help="Retrieve modelled population aggregates for polygon features"
    )
    population.add_argument("--boundary", required=True, type=Path)
    population.add_argument("--year", required=True, type=int)
    population.add_argument("--output", required=True, type=Path)
    population.add_argument("--id-field", default="source_id")
    population.add_argument("--name-field", default="ward_name")
    population.add_argument("--endpoint", default=DEFAULT_WORLDPOP_API)
    population.add_argument("--timeout", type=float, default=60.0)
    population.add_argument("--force", action="store_true")

    raster = subparsers.add_parser(
        "worldpop-raster", help="Download a clipped WorldPop people-per-cell GeoTIFF"
    )
    raster.add_argument("--boundary", required=True, type=Path)
    raster.add_argument("--year", required=True, type=int)
    raster.add_argument("--output", required=True, type=Path)
    raster.add_argument("--resolution", choices=("100m", "1km"), default="100m")
    raster.add_argument("--endpoint", default=DEFAULT_WORLDPOP_API)
    raster.add_argument("--timeout", type=float, default=120.0)
    raster.add_argument("--force", action="store_true")

    landsat = subparsers.add_parser(
        "landsat", help="Discover Landsat Collection 2 Level-2 scenes without downloading"
    )
    landsat.add_argument("--boundary", required=True, type=Path)
    landsat.add_argument("--start", required=True, help="Start date, inclusive (YYYY-MM-DD)")
    landsat.add_argument("--end", required=True, help="End date, inclusive (YYYY-MM-DD)")
    landsat.add_argument("--max-cloud", type=float, default=20.0)
    landsat.add_argument("--limit", type=int, default=100)
    landsat.add_argument("--output", required=True, type=Path)
    landsat.add_argument("--endpoint", default=DEFAULT_STAC_ENDPOINT)
    landsat.add_argument("--collection", default="landsat-c2-l2")
    landsat.add_argument("--force", action="store_true")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Run a data-intake command and return a process exit code."""
    args = _parser().parse_args(argv)
    try:
        collection, boundary_sha256 = _read_feature_collection(args.boundary)
        retrieved_at = datetime.now(UTC).isoformat()
        if args.command == "worldpop-raster":
            geometry = _single_geometry(collection)
            raster_result = download_population_raster(
                geometry,
                year=args.year,
                output_path=args.output,
                resolution=args.resolution,
                endpoint=args.endpoint,
                timeout_seconds=args.timeout,
                force=args.force,
            )
            print(
                json.dumps(
                    {
                        "success": True,
                        "output": str(args.output),
                        "metadata_output": str(
                            args.output.with_suffix(args.output.suffix + ".json")
                        ),
                        "file_bytes": raster_result.file_bytes,
                        "file_sha256": raster_result.file_sha256,
                        "total_population": raster_result.total_population,
                    },
                    indent=2,
                )
            )
            return 0
        if args.command == "worldpop":
            features = _population_features(
                collection,
                id_field=args.id_field,
                name_field=args.name_field,
            )
            population_result = population_by_areas(
                features,
                year=args.year,
                endpoint=args.endpoint,
                timeout_seconds=args.timeout,
            )
            payload = {
                "record_type": "worldpop_polygon_aggregate",
                "retrieved_at_utc": retrieved_at,
                "source": "WorldPop Global2 R2025A",
                "endpoint": args.endpoint,
                "year_requested": args.year,
                "boundary_file": str(args.boundary),
                "boundary_sha256": boundary_sha256,
                "feature_count": len(features["features"]),
                "id_field": args.id_field,
                "name_field": args.name_field,
                "result": population_result.to_dict(),
                "interpretation": (
                    "Modelled polygon aggregates, not census counts or within-polygon "
                    "population surfaces."
                ),
            }
        else:
            geometry = _single_geometry(collection)
            try:
                start_date = date.fromisoformat(args.start)
                end_date = date.fromisoformat(args.end)
            except ValueError as exc:
                raise ValueError("Start and end dates must use YYYY-MM-DD format") from exc
            if end_date < start_date:
                raise ValueError("End date must not be earlier than start date")
            datetime_range = f"{start_date.isoformat()}T00:00:00Z/{end_date.isoformat()}T23:59:59Z"
            scenes = search_stac_scenes(
                collection_ids=[args.collection],
                intersects=geometry,
                datetime_range=datetime_range,
                max_cloud_cover=args.max_cloud,
                limit=args.limit,
                endpoint=args.endpoint,
            )
            scene_records = []
            for scene in scenes:
                record = scene.to_dict()
                record["assets"] = {
                    key: _safe_asset_href(href) for key, href in scene.assets.items()
                }
                scene_records.append(record)
            payload = {
                "record_type": "landsat_stac_scene_discovery",
                "retrieved_at_utc": retrieved_at,
                "endpoint": args.endpoint,
                "collection": args.collection,
                "datetime_range": datetime_range,
                "max_cloud_cover_percent": args.max_cloud,
                "boundary_file": str(args.boundary),
                "boundary_sha256": boundary_sha256,
                "scene_count": len(scene_records),
                "scenes": scene_records,
                "limitations": [
                    "Discovery metadata only. No imagery has been downloaded or processed.",
                    "Scene-level cloud cover does not replace pixel-level QA.",
                    "Review footprints, acquisition dates, valid-pixel coverage and QA bands.",
                    "Surface temperature is land-surface temperature, not air temperature.",
                ],
            }
        _write_output(args.output, payload, force=args.force)
    except (OSError, RuntimeError, ValueError) as error:
        print(f"Data intake failed: {error}", file=sys.stderr)
        return 1

    print(
        json.dumps(
            {
                "success": True,
                "output": str(args.output),
                "record_type": payload["record_type"],
                "item_count": payload.get("feature_count", payload.get("scene_count")),
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

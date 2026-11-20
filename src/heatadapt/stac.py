"""STAC scene discovery with explicit spatial and temporal constraints."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass
from typing import Any

from pystac_client import Client

DEFAULT_STAC_ENDPOINT = "https://planetarycomputer.microsoft.com/api/stac/v1"


@dataclass(frozen=True, slots=True)
class SceneRecord:
    """Compact, auditable metadata for one discovered STAC scene."""

    item_id: str
    collection_id: str | None
    acquired_at: str | None
    cloud_cover_percent: float | None
    platform: str | None
    instruments: tuple[str, ...]
    assets: dict[str, str]
    geometry: dict[str, Any] | None

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serializable representation."""
        return asdict(self)


def search_stac_scenes(
    *,
    collection_ids: Sequence[str],
    intersects: Mapping[str, Any],
    datetime_range: str,
    max_cloud_cover: float | None = 30.0,
    limit: int = 100,
    endpoint: str = DEFAULT_STAC_ENDPOINT,
) -> list[SceneRecord]:
    """Search a STAC API and return scene metadata without downloading assets.

    The intersects argument must be a GeoJSON geometry in WGS84
    longitude/latitude. The STAC client follows pagination up to limit items.
    Cloud-cover filtering uses the common eo:cloud_cover property.
    """
    if not collection_ids or any(not value.strip() for value in collection_ids):
        raise ValueError("At least one non-empty STAC collection ID is required")
    if not datetime_range.strip():
        raise ValueError("datetime_range must not be empty")
    if limit < 1 or limit > 1000:
        raise ValueError("limit must be between 1 and 1000")
    if max_cloud_cover is not None and not 0 <= max_cloud_cover <= 100:
        raise ValueError("max_cloud_cover must be between 0 and 100")
    if intersects.get("type") not in {"Polygon", "MultiPolygon"}:
        raise ValueError("intersects must be a GeoJSON Polygon or MultiPolygon")
    if not isinstance(intersects.get("coordinates"), list):
        raise ValueError("intersects must contain GeoJSON coordinates")

    query: dict[str, dict[str, float]] | None = None
    if max_cloud_cover is not None:
        query = {"eo:cloud_cover": {"lte": max_cloud_cover}}

    catalog = Client.open(endpoint)
    search = catalog.search(
        collections=list(collection_ids),
        intersects=dict(intersects),
        datetime=datetime_range,
        query=query,
        max_items=limit,
    )

    records: list[SceneRecord] = []
    for item in search.items_as_dicts():
        properties = item.get("properties") or {}
        assets = item.get("assets") or {}
        asset_hrefs = {
            key: value["href"]
            for key, value in assets.items()
            if isinstance(value, dict) and isinstance(value.get("href"), str)
        }
        cloud_cover = properties.get("eo:cloud_cover")
        records.append(
            SceneRecord(
                item_id=str(item.get("id", "")),
                collection_id=item.get("collection"),
                acquired_at=properties.get("datetime") or properties.get("start_datetime"),
                cloud_cover_percent=(
                    float(cloud_cover) if cloud_cover is not None else None
                ),
                platform=properties.get("platform"),
                instruments=tuple(properties.get("instruments") or ()),
                assets=asset_hrefs,
                geometry=item.get("geometry"),
            )
        )
    return records

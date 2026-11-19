"""Dataset catalogue records and validation for traceable geospatial inputs."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse


@dataclass(frozen=True, slots=True)
class DatasetRecord:
    """A source record. Metadata describes provenance, not data quality certification."""

    dataset_id: str
    title: str
    provider: str
    source_url: str
    licence: str
    spatial_resolution: str
    temporal_coverage: str
    intended_use: str
    limitations: str
    status: str = "planned"

    def __post_init__(self) -> None:
        required = (
            "dataset_id",
            "title",
            "provider",
            "licence",
            "spatial_resolution",
            "temporal_coverage",
            "intended_use",
            "limitations",
        )
        for field_name in required:
            value = getattr(self, field_name)
            if not value.strip():
                raise ValueError(f"{field_name} must not be empty")
        parsed_url = urlparse(self.source_url)
        if parsed_url.scheme != "https" or not parsed_url.netloc:
            raise ValueError("source_url must be a valid HTTPS URL")
        if self.status not in {"planned", "assessed", "downloaded", "verified", "rejected"}:
            raise ValueError("status must be planned, assessed, downloaded, verified, or rejected")


def load_catalogue(path: str | Path) -> list[DatasetRecord]:
    """Load records from a JSON array and reject malformed or duplicate entries."""
    source = Path(path)
    payload = json.loads(source.read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise ValueError("Catalogue root must be a JSON array")

    records: list[DatasetRecord] = []
    seen_ids: set[str] = set()
    required_keys = {
        "dataset_id",
        "title",
        "provider",
        "source_url",
        "licence",
        "spatial_resolution",
        "temporal_coverage",
        "intended_use",
        "limitations",
    }
    optional_keys = {"status"}
    for index, item in enumerate(payload):
        if not isinstance(item, dict):
            raise ValueError(f"Catalogue entry {index} must be an object")
        missing = required_keys - item.keys()
        unknown = item.keys() - required_keys - optional_keys
        if missing:
            raise ValueError(f"Catalogue entry {index} is missing: {', '.join(sorted(missing))}")
        if unknown:
            fields = ", ".join(sorted(unknown))
            raise ValueError(f"Catalogue entry {index} has unknown fields: {fields}")
        record = DatasetRecord(**item)
        if record.dataset_id in seen_ids:
            raise ValueError(f"Duplicate dataset_id: {record.dataset_id}")
        seen_ids.add(record.dataset_id)
        records.append(record)
    return records

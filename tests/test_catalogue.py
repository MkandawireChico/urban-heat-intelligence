"""Tests for source metadata validation."""

import json

import pytest

from heatadapt.catalogue import DatasetRecord, load_catalogue


def _record(**overrides: str) -> dict[str, str]:
    values = {
        "dataset_id": "sample",
        "title": "Sample dataset",
        "provider": "Example provider",
        "source_url": "https://example.org/data",
        "licence": "CC BY 4.0",
        "spatial_resolution": "100 m",
        "temporal_coverage": "2020-2025",
        "intended_use": "Testing",
        "limitations": "Synthetic test record",
    }
    values.update(overrides)
    return values


def test_valid_record_is_created() -> None:
    record = DatasetRecord(**_record())
    assert record.dataset_id == "sample"
    assert record.status == "planned"


@pytest.mark.parametrize("url", ["http://example.org", "not-a-url", ""])
def test_source_url_must_use_https(url: str) -> None:
    with pytest.raises(ValueError, match="HTTPS"):
        DatasetRecord(**_record(source_url=url))


def test_catalogue_rejects_duplicate_ids(tmp_path) -> None:
    path = tmp_path / "catalogue.json"
    path.write_text(json.dumps([_record(), _record()]), encoding="utf-8")
    with pytest.raises(ValueError, match="Duplicate"):
        load_catalogue(path)


def test_catalogue_rejects_unknown_fields(tmp_path) -> None:
    path = tmp_path / "catalogue.json"
    path.write_text(json.dumps([_record(extra="unexpected")]), encoding="utf-8")
    with pytest.raises(ValueError, match="unknown fields"):
        load_catalogue(path)


def test_catalogue_loads_repository_manifest() -> None:
    records = load_catalogue("data/catalogue.json")
    assert len(records) >= 5
    assert {record.dataset_id for record in records}

from __future__ import annotations

from typing import Any

import pytest

from heatadapt import stac


class FakeSearch:
    def items_as_dicts(self):
        return [
            {
                "id": "S2A_TEST_SCENE",
                "collection": "sentinel-2-l2a",
                "geometry": {"type": "Polygon", "coordinates": []},
                "properties": {
                    "datetime": "2025-10-15T08:12:00Z",
                    "eo:cloud_cover": 7.5,
                    "platform": "sentinel-2a",
                    "instruments": ["msi"],
                },
                "assets": {
                    "B04": {"href": "https://example.test/B04.jp2"},
                    "thumbnail": {"href": "https://example.test/preview.jpg"},
                    "metadata": {"title": "metadata without href"},
                },
            }
        ]


class FakeCatalog:
    def __init__(self):
        self.arguments: dict[str, Any] | None = None

    def search(self, **kwargs):
        self.arguments = kwargs
        return FakeSearch()


def test_search_stac_scenes_returns_auditable_metadata(monkeypatch):
    catalog = FakeCatalog()
    monkeypatch.setattr(stac.Client, "open", lambda endpoint: catalog)

    scenes = stac.search_stac_scenes(
        collection_ids=["sentinel-2-l2a"],
        intersects={
            "type": "Polygon",
            "coordinates": [[[33.7, -15.9], [35.0, -15.9], [35.0, -14.5], [33.7, -15.9]]],
        },
        datetime_range="2025-10-01/2025-11-01",
        max_cloud_cover=20,
        limit=25,
    )

    assert len(scenes) == 1
    assert scenes[0].item_id == "S2A_TEST_SCENE"
    assert scenes[0].cloud_cover_percent == 7.5
    assert scenes[0].assets == {\n        "B04": "https://example.test/B04.jp2",\n        "thumbnail": "https://example.test/preview.jpg",\n    }
    assert catalog.arguments is not None
    assert catalog.arguments["collections"] == ["sentinel-2-l2a"]
    assert catalog.arguments["max_items"] == 25
    assert catalog.arguments["query"] == {"eo:cloud_cover": {"lte": 20}}


@pytest.mark.parametrize(
    ("overrides", "message"),
    [
        ({"collection_ids": []}, "collection ID"),
        ({"datetime_range": ""}, "datetime_range"),
        ({"limit": 0}, "limit"),
        ({"max_cloud_cover": 101}, "max_cloud_cover"),
        ({"intersects": {"type": "Point", "coordinates": [0, 0]}}, "Polygon"),
    ],
)
def test_rejects_invalid_search_parameters(overrides, message):
    arguments = {
        "collection_ids": ["sentinel-2-l2a"],
        "intersects": {"type": "Polygon", "coordinates": []},
        "datetime_range": "2025-01-01/2025-02-01",
    }
    arguments.update(overrides)

    with pytest.raises(ValueError, match=message):
        stac.search_stac_scenes(**arguments)

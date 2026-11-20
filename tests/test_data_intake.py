from __future__ import annotations

import json
from pathlib import Path

from heatadapt import data_intake
from heatadapt.stac import SceneRecord
from heatadapt.worldpop import AreaPopulationEstimate, PopulationBatch


def _write_boundary(path: Path, *, wards: bool = True) -> Path:
    features = [
        {
            "type": "Feature",
            "properties": {"source_id": "W01", "ward_name": "Central"},
            "geometry": {
                "type": "Polygon",
                "coordinates": [[[33.7, -15.9], [33.8, -15.9], [33.8, -15.8], [33.7, -15.9]]],
            },
        }
    ]
    if wards:
        features.append(
            {
                "type": "Feature",
                "properties": {"source_id": "W02", "ward_name": "North"},
                "geometry": features[0]["geometry"],
            }
        )
    path.write_text(json.dumps({"type": "FeatureCollection", "features": features}))
    return path


def test_worldpop_cli_writes_provenance_and_aggregates(tmp_path, monkeypatch, capsys):
    boundary = _write_boundary(tmp_path / "wards.geojson")
    output = tmp_path / "processed" / "worldpop.json"
    captured = {}

    def fake_population(features, **kwargs):
        captured["features"] = features
        captured["kwargs"] = kwargs
        return PopulationBatch(
            data_year=2025,
            total_population=1500.0,
            area_km2=2.0,
            areas=(
                AreaPopulationEstimate("W01", "Central", 1.0, 1000.0, 1000.0, 0.6667, 1),
                AreaPopulationEstimate("W02", "North", 1.0, 500.0, 500.0, 0.3333, 2),
            ),
        )

    monkeypatch.setattr(data_intake, "population_by_areas", fake_population)
    assert data_intake.main(
        [
            "worldpop",
            "--boundary",
            str(boundary),
            "--year",
            "2025",
            "--output",
            str(output),
        ]
    ) == 0

    payload = json.loads(output.read_text())
    assert payload["feature_count"] == 2
    assert len(payload["boundary_sha256"]) == 64
    assert payload["result"]["areas"][0]["area_id"] == "W01"
    assert captured["kwargs"]["year"] == 2025
    assert captured["features"]["features"][0]["id"] == "W01"
    assert captured["features"]["features"][0]["properties"] == {"name": "Central"}
    assert json.loads(capsys.readouterr().out)["success"] is True


def test_landsat_cli_uses_single_city_geometry_and_redacts_asset_queries(
    tmp_path, monkeypatch
):
    boundary = _write_boundary(tmp_path / "city.geojson", wards=False)
    output = tmp_path / "scenes.json"

    def fake_search(**kwargs):
        assert kwargs["datetime_range"] == "2025-10-01T00:00:00Z/2025-11-01T23:59:59Z"
        return [
            SceneRecord(
                item_id="LC08_TEST",
                collection_id="landsat-c2-l2",
                acquired_at="2025-10-12T07:30:00Z",
                cloud_cover_percent=8.5,
                platform="landsat-8",
                instruments=("OLI", "TIRS"),
                assets={"ST_B10": "https://example.org/data.tif?token=secret"},
                geometry={"type": "Polygon", "coordinates": []},
            )
        ]

    monkeypatch.setattr(data_intake, "search_stac_scenes", fake_search)
    assert data_intake.main(
        [
            "landsat",
            "--boundary",
            str(boundary),
            "--start",
            "2025-10-01",
            "--end",
            "2025-11-01",
            "--output",
            str(output),
        ]
    ) == 0

    payload = json.loads(output.read_text())
    assert payload["scene_count"] == 1
    assert payload["scenes"][0]["item_id"] == "LC08_TEST"
    assert payload["scenes"][0]["assets"]["ST_B10"] == "https://example.org/data.tif"
    assert "secret" not in output.read_text()


def test_landsat_cli_rejects_ward_collection_as_study_geometry(tmp_path, monkeypatch):
    boundary = _write_boundary(tmp_path / "wards.geojson")
    monkeypatch.setattr(
        data_intake,
        "search_stac_scenes",
        lambda **_kwargs: (_ for _ in ()).throw(AssertionError("search must not run")),
    )
    assert data_intake.main(
        [
            "landsat",
            "--boundary",
            str(boundary),
            "--start",
            "2025-10-01",
            "--end",
            "2025-11-01",
            "--output",
            str(tmp_path / "scenes.json"),
        ]
    ) == 1


def test_output_is_not_overwritten_without_force(tmp_path):
    output = tmp_path / "existing.json"
    output.write_text("keep")
    try:
        data_intake._write_output(output, {"new": True}, force=False)
    except FileExistsError:
        pass
    else:
        raise AssertionError("Expected FileExistsError")
    assert output.read_text() == "keep"

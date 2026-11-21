from __future__ import annotations

import hashlib
import json

import pytest

from heatadapt import worldpop_raster

POLYGON = {
    "type": "Polygon",
    "coordinates": [[[33.7, -15.9], [33.8, -15.9], [33.8, -15.8], [33.7, -15.9]]],
}
TIFF_BYTES = b"II*\x00" + b"\x08\x00\x00\x00" + b"test-geotiff-payload"


class FakeResponse:
    def __init__(self, body: bytes, headers: dict[str, str]):
        self._body = body
        self.headers = headers

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def read(self):
        return self._body


def test_download_population_raster_writes_geotiff_and_provenance(tmp_path, monkeypatch):
    captured = {}

    def fake_urlopen(request, timeout):
        captured["url"] = request.full_url
        captured["timeout"] = timeout
        captured["body"] = json.loads(request.data)
        return FakeResponse(
            TIFF_BYTES,
            {
                "Content-Type": "image/tiff",
                "X-Total-Population": "12345.6",
                "X-Area-Km2": "236.38",
            },
        )

    monkeypatch.setattr(worldpop_raster, "urlopen", fake_urlopen)
    output = tmp_path / "population.tif"
    result = worldpop_raster.download_population_raster(
        POLYGON,
        year=2025,
        output_path=output,
    )

    assert output.read_bytes() == TIFF_BYTES
    metadata_path = tmp_path / "population.tif.json"
    sidecar = json.loads(metadata_path.read_text())
    assert result.file_sha256 == hashlib.sha256(TIFF_BYTES).hexdigest()
    assert sidecar["metadata"]["file_sha256"] == result.file_sha256
    assert sidecar["request"]["year"] == 2025
    assert sidecar["request"]["resolution"] == "100m"
    assert sidecar["metadata"]["total_population"] == 12345.6
    assert captured["url"] == "https://api.worldpop.org/v3/raster"
    assert captured["body"]["geojson"] == POLYGON
    assert captured["body"]["layer"] == "population"


def test_download_rejects_non_tiff_response(tmp_path, monkeypatch):
    monkeypatch.setattr(
        worldpop_raster,
        "urlopen",
        lambda *_args, **_kwargs: FakeResponse(
            b'{"error":"no_data","message":"No population data"}',
            {"Content-Type": "application/json"},
        ),
    )
    with pytest.raises(RuntimeError, match="did not return a GeoTIFF"):
        worldpop_raster.download_population_raster(
            POLYGON, year=2025, output_path=tmp_path / "population.tif"
        )
    assert not (tmp_path / "population.tif").exists()


def test_download_rejects_invalid_tiff_signature(tmp_path, monkeypatch):
    monkeypatch.setattr(
        worldpop_raster,
        "urlopen",
        lambda *_args, **_kwargs: FakeResponse(
            b"not-a-tiff-file",
            {"Content-Type": "image/tiff"},
        ),
    )
    with pytest.raises(ValueError, match="TIFF file signature"):
        worldpop_raster.download_population_raster(
            POLYGON, year=2025, output_path=tmp_path / "population.tif"
        )


def test_download_does_not_overwrite_existing_outputs(tmp_path, monkeypatch):
    output = tmp_path / "population.tif"
    output.write_bytes(b"keep")
    monkeypatch.setattr(
        worldpop_raster,
        "urlopen",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("network must not run")),
    )
    with pytest.raises(FileExistsError):
        worldpop_raster.download_population_raster(POLYGON, year=2025, output_path=output)
    assert output.read_bytes() == b"keep"


def test_download_validates_resolution_and_year(tmp_path):
    with pytest.raises(ValueError, match="resolution"):
        worldpop_raster.download_population_raster(
            POLYGON, year=2025, output_path=tmp_path / "a.tif", resolution="10m"
        )
    with pytest.raises(ValueError, match="2015 through 2030"):
        worldpop_raster.download_population_raster(
            POLYGON, year=2031, output_path=tmp_path / "b.tif"
        )

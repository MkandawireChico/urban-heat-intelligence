from __future__ import annotations

import hashlib
import json
import sys
from types import SimpleNamespace

import pytest

from heatadapt import landsat_download

SCENE = {
    "item_id": "LC08_L2SP_168071_20251015_20251022_02_T1",
    "collection_id": "landsat-c2-l2",
    "acquired_at": "2025-10-15T07:45:00Z",
    "cloud_cover_percent": 8.2,
    "platform": "landsat-8",
    "instruments": ["OLI", "TIRS"],
    "assets": {
        "lwir11": "https://example.blob.core.windows.net/scene/st.tif",
        "qa_pixel": "https://example.blob.core.windows.net/scene/qa.tif",
        "qa_radsat": "https://example.blob.core.windows.net/scene/radsat.tif",
    },
}
TIFF = b"II*\x00" + b"\x08\x00\x00\x00" + b"payload"


class FakeResponse:
    headers = {"Content-Type": "image/tiff"}

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def read(self):
        return TIFF


def test_downloads_assets_and_never_persists_signature_tokens(tmp_path, monkeypatch):
    signed = []
    requested = []

    def fake_sign(href):
        signed.append(href)
        return href + "?sig=secret-token"

    def fake_urlopen(request, timeout):
        requested.append((request.full_url, timeout))
        return FakeResponse()

    monkeypatch.setitem(
        sys.modules, "planetary_computer", SimpleNamespace(sign=fake_sign)
    )
    monkeypatch.setattr(landsat_download, "urlopen", fake_urlopen)

    result = landsat_download.download_landsat_scene_assets(SCENE, tmp_path)

    scene_dir = tmp_path / SCENE["item_id"]
    assert set(result["assets"]) == {"lwir11", "qa_pixel", "qa_radsat"}
    assert all((scene_dir / f"{key}.tif").read_bytes() == TIFF for key in result["assets"])
    assert len(signed) == 3
    assert all("?sig=secret-token" in url for url, _ in requested)
    assert all(
        record["sha256"] == hashlib.sha256(TIFF).hexdigest()
        for record in result["assets"].values()
    )
    metadata_text = (scene_dir / "scene_metadata.json").read_text()
    assert "secret-token" not in metadata_text
    assert "?sig=" not in metadata_text
    assert json.loads(metadata_text)["scene"]["item_id"] == SCENE["item_id"]


def test_requires_all_requested_assets_before_network(tmp_path, monkeypatch):
    scene = {**SCENE, "assets": {"lwir11": SCENE["assets"]["lwir11"]}}
    monkeypatch.setattr(
        landsat_download,
        "urlopen",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("network called")),
    )
    with pytest.raises(ValueError, match="qa_pixel, qa_radsat"):
        landsat_download.download_landsat_scene_assets(scene, tmp_path)


def test_rejects_non_tiff_asset(tmp_path, monkeypatch):
    monkeypatch.setitem(
        sys.modules, "planetary_computer", SimpleNamespace(sign=lambda href: href)
    )

    class InvalidResponse(FakeResponse):
        def read(self):
            return b"not a raster"

    monkeypatch.setattr(
        landsat_download, "urlopen", lambda *_args, **_kwargs: InvalidResponse()
    )
    with pytest.raises(ValueError, match="valid TIFF signature"):
        landsat_download.download_landsat_scene_assets(SCENE, tmp_path)


def test_refuses_existing_scene_directory_without_force(tmp_path):
    (tmp_path / SCENE["item_id"]).mkdir()
    with pytest.raises(FileExistsError):
        landsat_download.download_landsat_scene_assets(SCENE, tmp_path)


def test_rejects_unsafe_scene_identifier(tmp_path):
    scene = {**SCENE, "item_id": "../outside"}
    with pytest.raises(ValueError, match="safe directory name"):
        landsat_download.download_landsat_scene_assets(scene, tmp_path)

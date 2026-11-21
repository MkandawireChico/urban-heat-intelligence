"""Download selected Landsat assets with short-lived Planetary Computer signatures."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import os
import tempfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit, urlunsplit
from urllib.request import Request, urlopen

REQUIRED_ASSETS = ("lwir11", "qa_pixel", "qa_radsat")


def _unsigned_href(href: str) -> str:
    """Return an asset URL without SAS query parameters or fragments."""
    parts = urlsplit(href)
    return urlunsplit((parts.scheme, parts.netloc, parts.path, "", ""))


def _is_tiff(payload: bytes) -> bool:
    return payload.startswith((b"II*\x00", b"MM\x00*", b"II+\x00", b"MM\x00+"))


def download_landsat_scene_assets(
    scene: dict[str, Any],
    output_dir: str | Path,
    *,
    asset_keys: tuple[str, ...] = REQUIRED_ASSETS,
    timeout_seconds: float = 180.0,
    force: bool = False,
) -> dict[str, Any]:
    """Download selected assets for one STAC scene and write provenance metadata.

    The Planetary Computer SDK signs source URLs at download time. Signed URLs
    are never written to disk. The caller must supply a scene record produced
    by the STAC discovery command.
    """
    if not isinstance(scene, dict) or not isinstance(scene.get("item_id"), str):
        raise ValueError("scene must contain a non-empty item_id")
    scene_id = scene["item_id"].strip()
    if not scene_id or any(part in scene_id for part in ("/", "\\", "..")):
        raise ValueError("scene item_id is not a safe directory name")
    if not asset_keys or any(not key.strip() for key in asset_keys):
        raise ValueError("At least one non-empty asset key is required")
    if timeout_seconds <= 0:
        raise ValueError("timeout_seconds must be positive")

    assets = scene.get("assets")
    if not isinstance(assets, dict):
        raise ValueError("scene assets must be an object")
    missing = [key for key in asset_keys if not isinstance(assets.get(key), str)]
    if missing:
        raise ValueError(f"Scene is missing required asset hrefs: {', '.join(missing)}")

    try:
        import planetary_computer
    except ImportError as exc:
        raise RuntimeError(
            "Install the geo extra to download Landsat assets: pip install -e '.[geo]'"
        ) from exc

    destination = Path(output_dir) / scene_id
    metadata_path = destination / "scene_metadata.json"
    if destination.exists() and not force:
        raise FileExistsError(
            f"Scene output directory already exists: {destination}. Pass --force to replace files."
        )
    destination.mkdir(parents=True, exist_ok=True)

    downloaded: dict[str, dict[str, Any]] = {}
    for key in asset_keys:
        source_href = assets[key]
        parts = urlsplit(source_href)
        if parts.scheme != "https" or not parts.netloc:
            raise ValueError(f"Asset {key!r} must use an HTTPS URL")
        signed_href = planetary_computer.sign(source_href)
        request = Request(signed_href, headers={"User-Agent": "urban-heat-intelligence/0.1"})
        try:
            with urlopen(request, timeout=timeout_seconds) as response:
                payload = response.read()
                content_type = response.headers.get("Content-Type")
        except HTTPError as exc:
            raise RuntimeError(f"Download failed for asset {key!r}: HTTP {exc.code}") from exc
        except (URLError, TimeoutError, OSError) as exc:
            raise RuntimeError(f"Download failed for asset {key!r}: {exc}") from exc
        if not _is_tiff(payload):
            raise ValueError(f"Asset {key!r} did not return a valid TIFF signature")

        filename = f"{key}.tif"
        target = destination / filename
        if target.exists() and not force:
            raise FileExistsError(f"Asset already exists: {target}")
        digest = hashlib.sha256(payload).hexdigest()
        file_descriptor, temporary_name = tempfile.mkstemp(
            prefix=f".{key}.", suffix=".tmp", dir=destination
        )
        try:
            with os.fdopen(file_descriptor, "wb") as temporary_file:
                temporary_file.write(payload)
                temporary_file.flush()
                os.fsync(temporary_file.fileno())
            os.replace(temporary_name, target)
        finally:
            if os.path.exists(temporary_name):
                os.unlink(temporary_name)
        downloaded[key] = {
            "file": filename,
            "bytes": len(payload),
            "sha256": digest,
            "content_type": content_type,
            "source_url": _unsigned_href(source_href),
        }

    metadata = {
        "record_type": "landsat_scene_asset_download",
        "retrieved_at_utc": datetime.now(UTC).isoformat(),
        "scene": {
            "item_id": scene_id,
            "collection_id": scene.get("collection_id"),
            "acquired_at": scene.get("acquired_at"),
            "cloud_cover_percent": scene.get("cloud_cover_percent"),
            "platform": scene.get("platform"),
            "instruments": scene.get("instruments", []),
        },
        "assets": downloaded,
        "interpretation": [
            "lwir11 is the Landsat Collection 2 Level-2 surface-temperature band.",
            "qa_pixel and qa_radsat are required for quality masking before analysis.",
            "Surface temperature is land-surface temperature, not near-surface air temperature.",
            "SAS signatures are intentionally excluded from this metadata file.",
        ],
    }
    temporary_metadata = metadata_path.with_suffix(".json.tmp")
    temporary_metadata.write_text(
        json.dumps(metadata, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    os.replace(temporary_metadata, metadata_path)
    return metadata



def main() -> int:
    """Download selected assets from a previously saved STAC discovery file."""
    parser = argparse.ArgumentParser(
        prog="heatadapt-download-landsat",
        description="Download quality-control and surface-temperature assets for one Landsat scene.",
    )
    parser.add_argument("--scenes", required=True, type=Path, help="STAC discovery JSON file")
    parser.add_argument("--scene-id", required=True, help="Exact STAC item ID")
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument(
        "--assets",
        nargs="+",
        default=list(REQUIRED_ASSETS),
        help="STAC asset keys to download (default: lwir11 qa_pixel qa_radsat)",
    )
    parser.add_argument("--timeout", type=float, default=180.0)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    try:
        document = json.loads(args.scenes.read_text(encoding="utf-8"))
        if document.get("record_type") != "landsat_stac_scene_discovery":
            raise ValueError("Input is not a Landsat STAC discovery file")
        matches = [
            scene
            for scene in document.get("scenes", [])
            if scene.get("item_id") == args.scene_id
        ]
        if len(matches) != 1:
            raise ValueError(
                f"Expected one scene matching {args.scene_id!r}; found {len(matches)}"
            )
        result = download_landsat_scene_assets(
            matches[0],
            args.output_dir,
            asset_keys=tuple(args.assets),
            timeout_seconds=args.timeout,
            force=args.force,
        )
    except (OSError, RuntimeError, ValueError, json.JSONDecodeError) as error:
        print(f"Landsat download failed: {error}", file=sys.stderr)
        return 1

    print(
        json.dumps(
            {
                "success": True,
                "scene_id": result["scene"]["item_id"],
                "output_dir": str(args.output_dir / args.scene_id),
                "assets": list(result["assets"]),
                "metadata": str(args.output_dir / args.scene_id / "scene_metadata.json"),
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Summarise raster indicators within planning-area polygons."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import rasterio  # type: ignore[import-untyped]
from rasterio.features import geometry_mask
from shapely.geometry import mapping


def summarise_raster_by_area(
    raster_path: str | Path,
    areas: Any,
    id_field: str,
) -> list[dict[str, str | int | float | None]]:
    """Calculate transparent per-area summaries for a single-band raster.

    Polygons are reprojected to the raster CRS. Pixel inclusion follows the
    raster cell-centre rule (all_touched=False). No interpolation or
    downscaling occurs. Valid fraction is valid raster pixels divided by
    raster pixels intersecting each polygon under this inclusion rule.
    """
    if areas.empty:
        raise ValueError("Planning-area layer contains no features")
    if areas.crs is None:
        raise ValueError("Planning-area layer must declare a CRS")
    if id_field not in areas.columns:
        raise ValueError(f"ID field {id_field!r} is missing from planning areas")
    identifiers = areas[id_field]
    if identifiers.isna().any():
        raise ValueError("Planning-area identifiers must not be null")
    if identifiers.astype(str).duplicated().any():
        raise ValueError("Planning-area identifiers must be unique")
    if areas.geometry.isna().any() or areas.geometry.is_empty.any():
        raise ValueError("Planning areas contain null or empty geometries")
    if not areas.geometry.is_valid.all():
        raise ValueError("Planning areas contain invalid geometries")
    allowed = {"Polygon", "MultiPolygon"}
    found = set(areas.geometry.geom_type.unique())
    if not found.issubset(allowed):
        raise ValueError(f"Planning areas must be polygons; found {sorted(found)}")

    summaries: list[dict[str, str | int | float | None]] = []
    with rasterio.open(raster_path) as dataset:
        if dataset.count != 1:
            raise ValueError("Indicator raster must contain exactly one band")
        if dataset.crs is None:
            raise ValueError("Indicator raster must declare a CRS")
        projected = areas.to_crs(dataset.crs)
        raster = dataset.read(1, masked=True)
        values = np.asarray(raster.data, dtype=np.float64)
        raster_invalid = np.ma.getmaskarray(raster) | ~np.isfinite(values)

        for identifier, geometry in zip(
            identifiers.astype(str).tolist(),
            projected.geometry.tolist(),
            strict=True,
        ):
            inside = geometry_mask(
                [mapping(geometry)],
                out_shape=(dataset.height, dataset.width),
                transform=dataset.transform,
                invert=True,
                all_touched=False,
            )
            inside_count = int(inside.sum())
            valid = inside & ~raster_invalid
            valid_values = values[valid]
            valid_count = int(valid_values.size)
            summaries.append(
                {
                    id_field: identifier,
                    "raster_crs": dataset.crs.to_string(),
                    "pixels_in_area": inside_count,
                    "valid_pixels": valid_count,
                    "valid_fraction": (
                        valid_count / inside_count if inside_count else 0.0
                    ),
                    "mean": float(valid_values.mean()) if valid_count else None,
                    "median": float(np.median(valid_values)) if valid_count else None,
                    "p90": (
                        float(np.percentile(valid_values, 90))
                        if valid_count
                        else None
                    ),
                    "minimum": float(valid_values.min()) if valid_count else None,
                    "maximum": float(valid_values.max()) if valid_count else None,
                }
            )
    return summaries

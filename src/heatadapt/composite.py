"""Create a median composite from already quality-masked indicator rasters."""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path
from typing import Any

import numpy as np
import rasterio  # type: ignore[import-untyped]

from heatadapt.raster import OUTPUT_NODATA


def median_composite(
    input_paths: Sequence[str | Path],
    output_path: str | Path,
    observation_count_path: str | Path,
) -> dict[str, int | float | str]:
    """Write a per-pixel median and valid-observation count for aligned rasters.

    Inputs must already be quality-masked, single-band rasters with identical
    dimensions, CRS and affine transform. The function does not select scenes,
    harmonise sensors, apply QA, or correct seasonal/acquisition differences.
    """
    if len(input_paths) < 2:
        raise ValueError("At least two input rasters are required")

    sources = [Path(path) for path in input_paths]
    median_path = Path(output_path)
    count_path = Path(observation_count_path)
    destinations = {median_path.resolve(), count_path.resolve()}
    if len(destinations) != 2:
        raise ValueError("Median and observation-count outputs must differ")
    if destinations.intersection(path.resolve() for path in sources):
        raise ValueError("Output paths must differ from every input path")

    with rasterio.open(sources[0]) as first:
        _validate_source(first, sources[0])
        reference_profile = first.profile.copy()
        reference_grid = (first.width, first.height, first.crs, first.transform)
        arrays = [_read_valid(first)]

        for source_path in sources[1:]:
            with rasterio.open(source_path) as dataset:
                _validate_source(dataset, source_path)
                candidate_grid = (
                    dataset.width,
                    dataset.height,
                    dataset.crs,
                    dataset.transform,
                )
                if candidate_grid != reference_grid:
                    raise ValueError(
                        f"Input raster {source_path} does not match the reference grid"
                    )
                arrays.append(_read_valid(dataset))

    stack = np.ma.stack(arrays)
    counts = np.ma.count(stack, axis=0).astype(np.uint16)
    median = np.ma.median(stack, axis=0).filled(OUTPUT_NODATA).astype(  # type: ignore[no-untyped-call]
        np.float32
    )

    profile = reference_profile.copy()
    profile.update(
        driver="GTiff",
        count=1,
        dtype="float32",
        nodata=OUTPUT_NODATA,
        compress="deflate",
        predictor=3,
    )
    median_path.parent.mkdir(parents=True, exist_ok=True)
    count_path.parent.mkdir(parents=True, exist_ok=True)

    with rasterio.open(median_path, "w", **profile) as destination:
        destination.write(median, 1)
        destination.write_mask((counts > 0).astype(np.uint8) * 255)
        destination.update_tags(
            1,
            statistic="per_pixel_median",
            input_count=str(len(sources)),
            interpretation="Median of supplied valid indicator observations",
        )

    count_profile = profile.copy()
    count_profile.update(dtype="uint16", nodata=0, predictor=2)
    with rasterio.open(count_path, "w", **count_profile) as destination:
        destination.write(counts, 1)
        destination.write_mask((counts > 0).astype(np.uint8) * 255)
        destination.update_tags(
            1,
            quantity="valid_observation_count",
            input_count=str(len(sources)),
        )

    valid = counts > 0
    valid_medians = median[valid]
    return {
        "median_output": str(median_path),
        "observation_count_output": str(count_path),
        "input_count": len(sources),
        "valid_pixels": int(valid.sum()),
        "zero_observation_pixels": int((~valid).sum()),
        "minimum_median": float(valid_medians.min()) if valid_medians.size else float("nan"),
        "maximum_median": float(valid_medians.max()) if valid_medians.size else float("nan"),
    }


def _validate_source(dataset: Any, path: Path) -> None:
    if dataset.count != 1:
        raise ValueError(f"Input raster {path} must contain exactly one band")
    if dataset.crs is None:
        raise ValueError(f"Input raster {path} must declare a CRS")
    if dataset.nodata is None:
        raise ValueError(
            f"Input raster {path} must declare nodata; do not infer missing values"
        )


def _read_valid(dataset: Any) -> np.ma.MaskedArray:
    band = dataset.read(1, masked=True)
    values = np.asarray(band.data, dtype=np.float32)
    mask = np.ma.getmaskarray(band) | ~np.isfinite(values)
    return np.ma.array(values, mask=mask)

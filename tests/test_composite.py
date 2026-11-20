from __future__ import annotations

import numpy as np
import pytest
import rasterio
from rasterio.transform import from_origin

from heatadapt.composite import median_composite


def _write(path, values, *, transform=None, nodata=-9999.0):
    array = np.asarray(values, dtype="float32")
    with rasterio.open(
        path,
        "w",
        driver="GTiff",
        width=array.shape[1],
        height=array.shape[0],
        count=1,
        dtype="float32",
        crs="EPSG:32636",
        transform=transform or from_origin(0, 2, 1, 1),
        nodata=nodata,
    ) as dataset:
        dataset.write(array, 1)


def test_median_composite_preserves_valid_observation_counts(tmp_path):
    first = tmp_path / "first.tif"
    second = tmp_path / "second.tif"
    third = tmp_path / "third.tif"
    _write(first, [[10, 20], [30, -9999]])
    _write(second, [[20, -9999], [40, -9999]])
    _write(third, [[30, 40], [-9999, -9999]])
    median = tmp_path / "median.tif"
    counts = tmp_path / "counts.tif"

    summary = median_composite([first, second, third], median, counts)

    with rasterio.open(median) as dataset:
        values = dataset.read(1, masked=True)
        assert values[0, 0] == 20
        assert values[0, 1] == 30
        assert values[1, 0] == 35
        assert values.mask[1, 1]
        assert dataset.crs.to_string() == "EPSG:32636"
    with rasterio.open(counts) as dataset:
        assert dataset.read(1).tolist() == [[3, 2], [2, 0]]

    assert summary["input_count"] == 3
    assert summary["valid_pixels"] == 3
    assert summary["zero_observation_pixels"] == 1


def test_rejects_misaligned_input_grids(tmp_path):
    first = tmp_path / "first.tif"
    second = tmp_path / "second.tif"
    _write(first, [[1, 2], [3, 4]])
    _write(second, [[1, 2], [3, 4]], transform=from_origin(1, 2, 1, 1))

    with pytest.raises(ValueError, match="does not match"):
        median_composite([first, second], tmp_path / "median.tif", tmp_path / "count.tif")


def test_requires_explicit_nodata_metadata(tmp_path):
    first = tmp_path / "first.tif"
    second = tmp_path / "second.tif"
    _write(first, [[1, 2], [3, 4]], nodata=None)
    _write(second, [[1, 2], [3, 4]])

    with pytest.raises(ValueError, match="declare nodata"):
        median_composite([first, second], tmp_path / "median.tif", tmp_path / "count.tif")


def test_requires_two_input_scenes(tmp_path):
    source = tmp_path / "single.tif"
    _write(source, [[1, 2], [3, 4]])

    with pytest.raises(ValueError, match="At least two"):
        median_composite([source], tmp_path / "median.tif", tmp_path / "count.tif")

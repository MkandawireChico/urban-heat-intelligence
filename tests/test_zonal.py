from __future__ import annotations

import geopandas as gpd
import numpy as np
import rasterio
from rasterio.transform import from_origin
from shapely.geometry import box

from heatadapt.zonal import summarise_raster_by_area


def _write_raster(path, values, *, nodata=-9999.0):
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
        transform=from_origin(0, 2, 1, 1),
        nodata=nodata,
    ) as dataset:
        dataset.write(array, 1)


def test_summarises_valid_pixels_per_polygon(tmp_path):
    raster = tmp_path / "indicator.tif"
    _write_raster(raster, [[10, 20], [30, -9999]])
    areas = gpd.GeoDataFrame(
        {"area_code": ["north", "south"]},
        geometry=[box(0, 1, 2, 2), box(0, 0, 2, 1)],
        crs="EPSG:32636",
    )

    result = summarise_raster_by_area(raster, areas, "area_code")

    assert result[0]["area_code"] == "north"
    assert result[0]["pixels_in_area"] == 2
    assert result[0]["valid_pixels"] == 2
    assert result[0]["valid_fraction"] == 1.0
    assert result[0]["mean"] == 15.0
    assert result[0]["median"] == 15.0
    assert result[0]["p90"] == 19.0
    assert result[1]["pixels_in_area"] == 2
    assert result[1]["valid_pixels"] == 1
    assert result[1]["valid_fraction"] == 0.5
    assert result[1]["mean"] == 30.0


def test_returns_null_statistics_when_area_has_no_valid_pixels(tmp_path):
    raster = tmp_path / "indicator.tif"
    _write_raster(raster, [[-9999, -9999], [-9999, -9999]])
    areas = gpd.GeoDataFrame(
        {"area_code": ["empty"]},
        geometry=[box(0, 0, 2, 2)],
        crs="EPSG:32636",
    )

    result = summarise_raster_by_area(raster, areas, "area_code")

    assert result[0]["pixels_in_area"] == 4
    assert result[0]["valid_pixels"] == 0
    assert result[0]["valid_fraction"] == 0.0
    assert result[0]["mean"] is None


def test_rejects_duplicate_area_identifiers(tmp_path):
    raster = tmp_path / "indicator.tif"
    _write_raster(raster, [[1, 2], [3, 4]])
    areas = gpd.GeoDataFrame(
        {"area_code": ["same", "same"]},
        geometry=[box(0, 0, 1, 1), box(1, 0, 2, 1)],
        crs="EPSG:32636",
    )

    import pytest

    with pytest.raises(ValueError, match="must be unique"):
        summarise_raster_by_area(raster, areas, "area_code")

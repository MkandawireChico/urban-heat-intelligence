from __future__ import annotations

import numpy as np
import pytest
import rasterio
from rasterio.transform import from_origin

from heatadapt.raster import (
    OUTPUT_NODATA,
    inspect_worldpop_population_raster,
    process_landsat_surface_temperature,
)


def _write_band(path, values, *, crs="EPSG:32636", transform=None):
    array = np.asarray(values, dtype="uint16")
    with rasterio.open(
        path,
        "w",
        driver="GTiff",
        width=array.shape[1],
        height=array.shape[0],
        count=1,
        dtype="uint16",
        crs=crs,
        transform=transform or from_origin(600000, 8300000, 30, 30),
    ) as dataset:
        dataset.write(array, 1)


def test_processes_temperature_and_masks_fill_cloud_and_saturation(tmp_path):
    st = tmp_path / "ST_B10.tif"
    qa = tmp_path / "QA_PIXEL.tif"
    sat = tmp_path / "QA_RADSAT.tif"
    output = tmp_path / "temperature_c.tif"
    _write_band(st, [[44947, 44947, 0, 44947]])
    _write_band(qa, [[0, 1 << 3, 0, 0]])
    _write_band(sat, [[0, 0, 0, 1]])

    summary = process_landsat_surface_temperature(st, qa, output, sat)

    assert summary["valid_pixels"] == 1
    assert summary["masked_pixels"] == 3
    with rasterio.open(output) as dataset:
        result = dataset.read(1)
        assert result[0, 0] == pytest.approx(29.4797, abs=0.001)
        assert np.all(result[0, 1:] == OUTPUT_NODATA)
        assert dataset.crs.to_string() == "EPSG:32636"
        assert dataset.tags(1)["units"] == "degrees_Celsius"


def test_rejects_mismatched_grid(tmp_path):
    st = tmp_path / "ST_B10.tif"
    qa = tmp_path / "QA_PIXEL.tif"
    _write_band(st, [[44947, 44947]])
    _write_band(qa, [[0, 0]], transform=from_origin(600010, 8300000, 30, 30))

    with pytest.raises(ValueError, match="match the ST raster grid"):
        process_landsat_surface_temperature(st, qa, tmp_path / "out.tif")


def test_rejects_missing_crs(tmp_path):
    st = tmp_path / "ST_B10.tif"
    qa = tmp_path / "QA_PIXEL.tif"
    _write_band(st, [[44947]], crs=None)
    _write_band(qa, [[0]], crs=None)

    with pytest.raises(ValueError, match="declare a CRS"):
        process_landsat_surface_temperature(st, qa, tmp_path / "out.tif")



def _write_population_raster(path, values, *, nodata=-99999.0, crs="EPSG:4326"):
    array = np.asarray(values, dtype="float32")
    with rasterio.open(
        path,
        "w",
        driver="GTiff",
        width=array.shape[1],
        height=array.shape[0],
        count=1,
        dtype="float32",
        crs=crs,
        transform=from_origin(33.7, -15.8, 0.001, 0.001),
        nodata=nodata,
    ) as dataset:
        dataset.write(array, 1)


def test_inspects_worldpop_raster_and_keeps_zero_distinct_from_nodata(tmp_path):
    raster = tmp_path / "worldpop.tif"
    _write_population_raster(raster, [[10.0, 0.0, -99999.0], [5.0, 2.0, -99999.0]])

    report = inspect_worldpop_population_raster(raster, expected_total_population=17.0)

    assert report["crs"] == "EPSG:4326"
    assert report["pixel_count"] == 6
    assert report["valid_pixel_count"] == 4
    assert report["nodata_or_nonfinite_pixel_count"] == 2
    assert report["zero_population_pixel_count"] == 1
    assert report["population_sum_people"] == pytest.approx(17.0)
    assert report["difference_from_expected_people"] == pytest.approx(0.0)


def test_population_raster_inspection_rejects_wrong_crs_and_negative_valid_cells(tmp_path):
    wrong_crs = tmp_path / "wrong_crs.tif"
    _write_population_raster(wrong_crs, [[1.0]], crs="EPSG:32736")
    with pytest.raises(ValueError, match="EPSG:4326"):
        inspect_worldpop_population_raster(wrong_crs)

    negative = tmp_path / "negative.tif"
    _write_population_raster(negative, [[-1.0]])
    with pytest.raises(ValueError, match="negative population"):
        inspect_worldpop_population_raster(negative)

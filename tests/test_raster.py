from __future__ import annotations

import numpy as np
import pytest
import rasterio
from rasterio.transform import from_origin

from heatadapt.raster import OUTPUT_NODATA, process_landsat_surface_temperature


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

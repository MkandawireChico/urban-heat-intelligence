"""File-level Landsat Collection 2 raster processing.

The function writes a single-band land-surface temperature GeoTIFF in Celsius.
It preserves the input grid and CRS; reprojection and clipping are separate steps.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import rasterio  # type: ignore[import-untyped]

from heatadapt.landsat import (
    KELVIN_TO_CELSIUS,
    LANDSAT_C2_EXCLUDED_QA_PIXEL_BITS,
    LANDSAT_C2_FILL_VALUE,
    LANDSAT_C2_ST_OFFSET_K,
    LANDSAT_C2_ST_SCALE,
)

OUTPUT_NODATA = -9999.0


def process_landsat_surface_temperature(
    st_band_path: str | Path,
    qa_pixel_path: str | Path,
    output_path: str | Path,
    qa_radsat_path: str | Path | None = None,
) -> dict[str, int | float | str]:
    """Convert Landsat ST and QA GeoTIFFs into a masked Celsius GeoTIFF.

    Inputs must be single-band rasters on the same grid. The output retains
    their CRS, transform and dimensions. Non-zero QA_RADSAT values are masked
    when that band is supplied. No reprojection, clipping or scene selection
    takes place here.
    """
    output = Path(output_path)
    input_paths = [Path(st_band_path), Path(qa_pixel_path)]
    if qa_radsat_path is not None:
        input_paths.append(Path(qa_radsat_path))
    if output.resolve() in {path.resolve() for path in input_paths}:
        raise ValueError("Output path must differ from every input path")

    with (
        rasterio.open(st_band_path) as st_src,
        rasterio.open(qa_pixel_path) as qa_src,
    ):
        if st_src.count != 1 or qa_src.count != 1:
            raise ValueError("ST_B10 and QA_PIXEL inputs must each contain one band")
        _require_matching_grid(st_src, qa_src, "QA_PIXEL")
        if st_src.crs is None:
            raise ValueError("Input rasters must declare a CRS")

        st_dn = st_src.read(1)
        qa_pixel = qa_src.read(1)
        invalid = (st_dn == LANDSAT_C2_FILL_VALUE) | (
            (qa_pixel & LANDSAT_C2_EXCLUDED_QA_PIXEL_BITS) != 0
        )

        if qa_radsat_path is not None:
            with rasterio.open(qa_radsat_path) as qa_radsat_src:
                if qa_radsat_src.count != 1:
                    raise ValueError("QA_RADSAT input must contain one band")
                _require_matching_grid(st_src, qa_radsat_src, "QA_RADSAT")
                invalid |= qa_radsat_src.read(1) != 0

        temperature_c = (
            st_dn.astype(np.float32) * LANDSAT_C2_ST_SCALE
            + LANDSAT_C2_ST_OFFSET_K
            - KELVIN_TO_CELSIUS
        ).astype(np.float32)
        temperature_c[invalid] = OUTPUT_NODATA

        profile = st_src.profile.copy()
        profile.update(
            driver="GTiff",
            count=1,
            dtype="float32",
            nodata=OUTPUT_NODATA,
            compress="deflate",
            predictor=3,
        )
        output.parent.mkdir(parents=True, exist_ok=True)
        with rasterio.open(output, "w", **profile) as destination:
            destination.write(temperature_c, 1)
            destination.write_mask((~invalid).astype(np.uint8) * 255)
            destination.update_tags(
                1,
                units="degrees_Celsius",
                quantity="satellite_land_surface_temperature",
                source_product="Landsat Collection 2 Level-2",
                source_band="ST_B10 or ST_B6",
                scale_factor=str(LANDSAT_C2_ST_SCALE),
                additive_offset_kelvin=str(LANDSAT_C2_ST_OFFSET_K),
                kelvin_to_celsius_offset=str(KELVIN_TO_CELSIUS),
                masked_qa_pixel_bits="0,1,2,3,4,5",
                qa_radsat_applied=str(qa_radsat_path is not None).lower(),
                interpretation_limit=(
                    "Land-surface temperature at satellite overpass; "
                    "not air temperature or personal heat exposure"
                ),
            )

        valid_count = int((~invalid).sum())
        total_count = int(invalid.size)
        valid_values = temperature_c[~invalid]
        return {
            "output": str(output),
            "width": int(st_src.width),
            "height": int(st_src.height),
            "valid_pixels": valid_count,
            "masked_pixels": total_count - valid_count,
            "valid_fraction": valid_count / total_count if total_count else 0.0,
            "minimum_celsius": float(valid_values.min()) if valid_count else float("nan"),
            "maximum_celsius": float(valid_values.max()) if valid_count else float("nan"),
        }


def _require_matching_grid(
    reference: Any,
    candidate: Any,
    label: str,
) -> None:
    if (
        reference.width != candidate.width
        or reference.height != candidate.height
        or reference.transform != candidate.transform
        or reference.crs != candidate.crs
    ):
        raise ValueError(f"{label} raster must match the ST raster grid and CRS")


def inspect_worldpop_population_raster(
    raster_path: str | Path,
    *,
    expected_total_population: float | None = None,
) -> dict[str, int | float | str | None]:
    """Inspect a WorldPop people-per-cell raster without changing its grid.

    Nodata cells are excluded from population sums. Valid zero cells remain
    valid observations and are counted separately. This function does not
    reproject, resample, clip or infer population in missing cells.
    """
    with rasterio.open(raster_path) as source:
        if source.count != 1:
            raise ValueError("WorldPop population raster must contain one band")
        if source.crs is None or source.crs.to_epsg() != 4326:
            raise ValueError("WorldPop population raster must use EPSG:4326")
        if source.nodata is None:
            raise ValueError("WorldPop population raster must declare nodata")
        if source.dtypes[0] not in {"float32", "float64"}:
            raise ValueError("WorldPop population raster must use a floating-point dtype")

        values = source.read(1, masked=True).astype(np.float64)
        data = np.asarray(values.data)
        masked = np.ma.getmaskarray(values) | ~np.isfinite(data)
        valid = ~masked
        valid_values = data[valid]
        if np.any(valid_values < 0):
            raise ValueError("WorldPop valid cells contain negative population values")

        population_sum = float(valid_values.sum(dtype=np.float64))
        valid_count = int(valid.sum())
        total_count = int(data.size)
        zero_count = int(np.count_nonzero(valid_values == 0))
        result: dict[str, int | float | str | None] = {
            "path": str(raster_path),
            "crs": source.crs.to_string(),
            "width": int(source.width),
            "height": int(source.height),
            "pixel_count": total_count,
            "valid_pixel_count": valid_count,
            "nodata_or_nonfinite_pixel_count": total_count - valid_count,
            "valid_pixel_fraction": valid_count / total_count if total_count else 0.0,
            "zero_population_pixel_count": zero_count,
            "nodata_value": float(source.nodata),
            "population_sum_people": population_sum,
            "minimum_valid_cell_people": float(valid_values.min()) if valid_count else None,
            "maximum_valid_cell_people": float(valid_values.max()) if valid_count else None,
            "expected_total_population_people": expected_total_population,
            "difference_from_expected_people": (
                population_sum - expected_total_population
                if expected_total_population is not None
                else None
            ),
        }
        if expected_total_population is not None and expected_total_population < 0:
            raise ValueError("expected_total_population must not be negative")
        return result

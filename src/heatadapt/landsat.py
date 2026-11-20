"""Small, testable transformations for Landsat Collection 2 Level-2 values.

These helpers operate on pixel arrays supplied by a raster reader. They do not
open files, perform reprojection, or certify the quality of a scene.
"""

from __future__ import annotations

from collections.abc import Sequence

LANDSAT_C2_ST_SCALE = 0.00341802
LANDSAT_C2_ST_OFFSET_K = 149.0
KELVIN_TO_CELSIUS = 273.15
LANDSAT_C2_FILL_VALUE = 0

# QA_PIXEL bits to exclude: fill, dilated cloud, cirrus, cloud, cloud shadow, snow.
LANDSAT_C2_EXCLUDED_QA_PIXEL_BITS = (1 << 0) | (1 << 1) | (1 << 2) | (1 << 3) | (1 << 4) | (1 << 5)


def landsat_surface_temperature_celsius(
    digital_numbers: Sequence[int],
    qa_pixel: Sequence[int],
    qa_radsat: Sequence[int] | None = None,
) -> list[float | None]:
    """Convert ST_B10/ST_B6 DN values to Celsius, masking invalid/contaminated pixels.

    Collection 2 surface-temperature DN values use scale 0.00341802 and offset
    149 K. Fill pixels and selected QA_PIXEL flags are masked. Saturated pixels
    are also masked when QA_RADSAT is supplied.
    """
    if len(digital_numbers) != len(qa_pixel):
        raise ValueError("digital_numbers and qa_pixel must have equal lengths")
    if qa_radsat is not None and len(digital_numbers) != len(qa_radsat):
        raise ValueError("qa_radsat must have the same length as digital_numbers")

    output: list[float | None] = []
    for index, (digital_number, qa_value) in enumerate(zip(digital_numbers, qa_pixel, strict=True)):
        if digital_number < 0 or qa_value < 0:
            raise ValueError("Raster values must be non-negative integers")
        invalid = (
            digital_number == LANDSAT_C2_FILL_VALUE
            or bool(qa_value & LANDSAT_C2_EXCLUDED_QA_PIXEL_BITS)
        )
        if qa_radsat is not None:
            saturation = qa_radsat[index]
            if saturation < 0:
                raise ValueError("QA_RADSAT values must be non-negative integers")
            invalid = invalid or saturation != 0
        if invalid:
            output.append(None)
            continue

        kelvin = digital_number * LANDSAT_C2_ST_SCALE + LANDSAT_C2_ST_OFFSET_K
        output.append(kelvin - KELVIN_TO_CELSIUS)
    return output


def normalized_difference(
    band_a: Sequence[float],
    band_b: Sequence[float],
) -> list[float | None]:
    """Calculate a normalized difference index, returning None where undefined.

    Inputs must already be converted to comparable surface-reflectance values.
    This function does not apply sensor-specific scaling or cloud masking.
    """
    if len(band_a) != len(band_b):
        raise ValueError("band_a and band_b must have equal lengths")
    output: list[float | None] = []
    for first, second in zip(band_a, band_b, strict=True):
        denominator = first + second
        if denominator == 0:
            output.append(None)
        else:
            output.append((first - second) / denominator)
    return output


def ndvi(nir_reflectance: Sequence[float], red_reflectance: Sequence[float]) -> list[float | None]:
    """Calculate NDVI from pre-scaled NIR and red surface reflectance."""
    return normalized_difference(nir_reflectance, red_reflectance)

"""Tests for satellite pixel transformations."""

import pytest

from heatadapt.landsat import (
    LANDSAT_C2_EXCLUDED_QA_PIXEL_BITS,
    landsat_surface_temperature_celsius,
    ndvi,
)


def test_landsat_surface_temperature_uses_collection_two_scale() -> None:
    result = landsat_surface_temperature_celsius([44_947], [0])
    assert result[0] == pytest.approx(29.45, abs=0.02)


def test_fill_cloud_and_shadow_pixels_are_masked() -> None:
    qa = [0, 1, 1 << 3, 1 << 4]
    result = landsat_surface_temperature_celsius([30_000, 30_000, 30_000, 30_000], qa)
    assert result[0] is not None
    assert result[1:] == [None, None, None]


def test_all_selected_quality_bits_are_excluded() -> None:
    for bit in range(6):
        result = landsat_surface_temperature_celsius([30_000], [1 << bit])
        assert result == [None]
    assert LANDSAT_C2_EXCLUDED_QA_PIXEL_BITS > 0


def test_saturated_pixel_is_masked_when_band_is_provided() -> None:
    assert landsat_surface_temperature_celsius([30_000], [0], [1]) == [None]
    assert landsat_surface_temperature_celsius([30_000], [0], [0])[0] is not None


def test_quality_arrays_must_have_matching_lengths() -> None:
    with pytest.raises(ValueError, match="equal lengths"):
        landsat_surface_temperature_celsius([30_000], [])


def test_negative_pixel_value_is_rejected() -> None:
    with pytest.raises(ValueError, match="non-negative"):
        landsat_surface_temperature_celsius([-1], [0])


def test_ndvi_uses_pre_scaled_reflectance() -> None:
    result = ndvi([0.6, 0.2, 0.4], [0.2, 0.2, 0.0])
    assert result == pytest.approx([0.5, 0.0, 1.0])


def test_ndvi_handles_zero_denominator() -> None:
    assert ndvi([0.0], [0.0]) == [None]


def test_normalized_difference_requires_equal_lengths() -> None:
    with pytest.raises(ValueError, match="equal lengths"):
        ndvi([0.5], [0.2, 0.3])

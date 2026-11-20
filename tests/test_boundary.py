from __future__ import annotations

import geopandas as gpd
import pytest
from shapely.geometry import Point, Polygon

from heatadapt.boundary import prepare_boundary_frame


def test_prepare_boundary_frame_preserves_features_and_reprojects():
    frame = gpd.GeoDataFrame(
        {"ward_id": ["W01"]},
        geometry=[
            Polygon(
                [
                    (700000, 8290000),
                    (701000, 8290000),
                    (701000, 8291000),
                    (700000, 8290000),
                ]
            )
        ],
        crs="EPSG:32736",
    )

    prepared = prepare_boundary_frame(frame)

    assert len(prepared) == 1
    assert prepared.crs.to_epsg() == 4326
    assert prepared.iloc[0]["ward_id"] == "W01"
    assert prepared.geometry.iloc[0].geom_type == "Polygon"


def test_prepare_boundary_frame_rejects_missing_crs():
    frame = gpd.GeoDataFrame(
        {"ward_id": ["W01"]},
        geometry=[Polygon([(0, 0), (1, 0), (1, 1), (0, 0)])],
    )

    with pytest.raises(ValueError, match="no CRS"):
        prepare_boundary_frame(frame)


def test_prepare_boundary_frame_rejects_non_polygon_geometry():
    frame = gpd.GeoDataFrame(
        {"name": ["point"]},
        geometry=[Point(1, 2)],
        crs="EPSG:4326",
    )

    with pytest.raises(ValueError, match="polygon"):
        prepare_boundary_frame(frame)

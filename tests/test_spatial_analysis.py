import pytest

from apps.analysis.services.spatial_analysis import (
    validate_and_parse_geometry,
    compute_area_km2,
    run_full_analysis,
    InvalidGeometryError,
)

VALID_POLYGON = {
    "type": "Polygon",
    "coordinates": [[
        [91.70, 26.10],
        [91.75, 26.10],
        [91.75, 26.15],
        [91.70, 26.15],
        [91.70, 26.10],
    ]],
}


@pytest.mark.django_db
class TestGeometryValidation:
    def test_valid_polygon_parses_successfully(self):
        geom = validate_and_parse_geometry(VALID_POLYGON)
        assert geom.valid

    def test_rejects_non_polygon_type(self):
        point_geometry = {"type": "Point", "coordinates": [91.7, 26.1]}
        with pytest.raises(InvalidGeometryError):
            validate_and_parse_geometry(point_geometry)

    def test_rejects_empty_geometry(self):
        with pytest.raises(InvalidGeometryError):
            validate_and_parse_geometry({})

    def test_rejects_missing_coordinates(self):
        with pytest.raises(InvalidGeometryError):
            validate_and_parse_geometry({"type": "Polygon"})

    def test_rejects_malformed_coordinates(self):
        bad_geometry = {"type": "Polygon", "coordinates": "not-a-list"}
        with pytest.raises(InvalidGeometryError):
            validate_and_parse_geometry(bad_geometry)

    def test_rejects_self_intersecting_polygon(self):
        # bowtie shape - classic invalid polygon
        bowtie = {
            "type": "Polygon",
            "coordinates": [[
                [91.70, 26.10],
                [91.75, 26.15],
                [91.75, 26.10],
                [91.70, 26.15],
                [91.70, 26.10],
            ]],
        }
        with pytest.raises(InvalidGeometryError):
            validate_and_parse_geometry(bowtie)

    def test_rejects_extremely_large_polygon(self):
        huge_polygon = {
            "type": "Polygon",
            "coordinates": [[
                [60.0, 10.0],
                [110.0, 10.0],
                [110.0, 40.0],
                [60.0, 40.0],
                [60.0, 10.0],
            ]],
        }
        with pytest.raises(InvalidGeometryError):
            validate_and_parse_geometry(huge_polygon)


@pytest.mark.django_db
class TestAreaComputation:
    def test_area_is_positive_and_reasonable(self):
        geom = validate_and_parse_geometry(VALID_POLYGON)
        area = compute_area_km2(geom)
        # ~0.05deg x 0.05deg box at this latitude should be roughly 25-30 km2
        assert 20 < area < 35


@pytest.mark.django_db
class TestFullAnalysisPipeline:
    def test_run_full_analysis_returns_expected_keys(self):
        result = run_full_analysis(VALID_POLYGON)
        expected_keys = {
            "geometry", "area_km2", "flood_risk", "mean_elevation_m",
            "water_coverage_percent", "water_bodies_intersecting",
            "population_exposed", "result_metadata", "processing_status",
        }
        assert expected_keys.issubset(result.keys())
        assert result["processing_status"] == "COMPLETE"
        assert result["flood_risk"] in ["LOW", "MODERATE", "HIGH", "INSUFFICIENT_DATA"]
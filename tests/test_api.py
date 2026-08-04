import pytest
from rest_framework.test import APIClient

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


@pytest.fixture
def api_client():
    return APIClient()


@pytest.mark.django_db
class TestAnalysisCreateEndpoint:
    def test_valid_polygon_returns_201(self, api_client):
        response = api_client.post(
            "/api/v1/analysis/", {"geometry": VALID_POLYGON}, format="json"
        )
        assert response.status_code == 201
        assert "area_km2" in response.data
        assert "flood_risk" in response.data

    def test_missing_geometry_returns_400(self, api_client):
        response = api_client.post("/api/v1/analysis/", {}, format="json")
        assert response.status_code == 400

    def test_invalid_geometry_type_returns_400(self, api_client):
        response = api_client.post(
            "/api/v1/analysis/",
            {"geometry": {"type": "Point", "coordinates": [91.7, 26.1]}},
            format="json",
        )
        assert response.status_code == 400

    def test_malformed_json_body_returns_400(self, api_client):
        response = api_client.post(
            "/api/v1/analysis/", {"geometry": "not-a-geometry"}, format="json"
        )
        assert response.status_code == 400


@pytest.mark.django_db
class TestAnalysisListEndpoint:
    def test_list_returns_200_and_paginated_shape(self, api_client):
        response = api_client.get("/api/v1/analyses/")
        assert response.status_code == 200
        assert "count" in response.data
        assert "results" in response.data

    def test_created_analysis_appears_in_list(self, api_client):
        api_client.post("/api/v1/analysis/", {"geometry": VALID_POLYGON}, format="json")
        response = api_client.get("/api/v1/analyses/")
        assert response.data["count"] >= 1


@pytest.mark.django_db
class TestHealthCheckEndpoint:
    def test_health_check_returns_ok(self, api_client):
        response = api_client.get("/api/v1/health/")
        assert response.status_code == 200
        assert response.data["status"] == "ok"
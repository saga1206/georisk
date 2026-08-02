import json

from rest_framework import serializers

from apps.analysis.models import Analysis


class AnalysisRequestSerializer(serializers.Serializer):
    """Validates the incoming request body: { "geometry": {...GeoJSON Polygon...} }"""

    geometry = serializers.JSONField()

    def validate_geometry(self, value):
        if not isinstance(value, dict):
            raise serializers.ValidationError("geometry must be a GeoJSON object.")
        if value.get("type") != "Polygon":
            raise serializers.ValidationError("geometry.type must be 'Polygon'.")
        if "coordinates" not in value:
            raise serializers.ValidationError("geometry.coordinates is required.")
        return value


class AnalysisResultSerializer(serializers.ModelSerializer):
    geometry = serializers.SerializerMethodField()

    class Meta:
        model = Analysis
        fields = [
            "id",
            "geometry",
            "area_km2",
            "flood_risk",
            "mean_elevation_m",
            "water_coverage_percent",
            "population_exposed",
            "water_bodies_intersecting",
            "result_metadata",
            "processing_status",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields

    def get_geometry(self, obj):
        # Return as GeoJSON dict rather than WKT for direct Leaflet consumption
        return json.loads(obj.geometry.geojson)
from django.contrib.gis.db import models


class WaterBody(models.Model):
    """Reference layer of rivers, lakes, reservoirs used for proximity/intersection analysis."""

    WATER_TYPE_CHOICES = [
        ("river", "River"),
        ("lake", "Lake"),
        ("reservoir", "Reservoir"),
        ("wetland", "Wetland"),
    ]

    name = models.CharField(max_length=255)
    water_type = models.CharField(max_length=20, choices=WATER_TYPE_CHOICES)
    geometry = models.MultiPolygonField(srid=4326)
    source = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "Water bodies"

    def __str__(self):
        return f"{self.name} ({self.water_type})"


class FloodZone(models.Model):
    """Known flood-prone zones, if such reference data is available for the region."""

    RISK_CHOICES = [
        ("LOW", "Low"),
        ("MODERATE", "Moderate"),
        ("HIGH", "High"),
    ]

    name = models.CharField(max_length=255)
    risk_level = models.CharField(max_length=20, choices=RISK_CHOICES)
    geometry = models.MultiPolygonField(srid=4326)
    source = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} - {self.risk_level}"


class AdministrativeBoundary(models.Model):
    """District/state/ward boundaries used for context and population lookups."""

    name = models.CharField(max_length=255)
    admin_level = models.CharField(max_length=50)  # e.g. "district", "state", "ward"
    geometry = models.MultiPolygonField(srid=4326)
    source = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.admin_level})"


class GeospatialLayer(models.Model):
    """
    Metadata describing a toggleable map layer for the frontend.
    Powers GET /api/v1/layers/ so the UI doesn't hardcode layer definitions.
    """

    LAYER_TYPE_CHOICES = [
        ("water", "Water Bodies"),
        ("flood_zone", "Flood Zones"),
        ("admin_boundary", "Administrative Boundary"),
        ("elevation", "Elevation"),
        ("population", "Population Density"),
    ]

    name = models.CharField(max_length=255)
    layer_type = models.CharField(max_length=50, choices=LAYER_TYPE_CHOICES)
    description = models.TextField(blank=True)
    style_config = models.JSONField(default=dict, blank=True)  # e.g. {"color": "#2563eb", "opacity": 0.5}
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name
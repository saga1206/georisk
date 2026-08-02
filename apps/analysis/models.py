import uuid

from django.contrib.gis.db import models


class Analysis(models.Model):
    """
    A single user-triggered spatial analysis over a drawn polygon.
    Results are computed synchronously (for now) by the services layer
    and stored here for history/dashboard display.
    """

    RISK_CHOICES = [
        ("LOW", "Low"),
        ("MODERATE", "Moderate"),
        ("HIGH", "High"),
        ("INSUFFICIENT_DATA", "Insufficient Data"),
    ]

    STATUS_CHOICES = [
        ("PENDING", "Pending"),
        ("COMPLETE", "Complete"),
        ("FAILED", "Failed"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    geometry = models.PolygonField(srid=4326)

    area_km2 = models.FloatField(null=True, blank=True)
    flood_risk = models.CharField(max_length=20, choices=RISK_CHOICES, null=True, blank=True)
    mean_elevation_m = models.FloatField(null=True, blank=True)
    water_coverage_percent = models.FloatField(null=True, blank=True)
    population_exposed = models.IntegerField(null=True, blank=True)
    water_bodies_intersecting = models.IntegerField(null=True, blank=True)

    # Stores scoring breakdown, dataset versions used, intermediate values —
    # keeps the methodology auditable without needing extra columns per detail.
    result_metadata = models.JSONField(default=dict, blank=True)

    processing_status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default="PENDING"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Analyses"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Analysis {self.id} - {self.flood_risk or 'PENDING'}"
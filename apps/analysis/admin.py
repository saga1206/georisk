from django.contrib.gis import admin

from .models import Analysis


@admin.register(Analysis)
class AnalysisAdmin(admin.GISModelAdmin):
    list_display = (
        "id",
        "flood_risk",
        "area_km2",
        "processing_status",
        "created_at",
    )
    list_filter = ("flood_risk", "processing_status")
    readonly_fields = ("id", "created_at", "updated_at")
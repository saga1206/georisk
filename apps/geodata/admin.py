from django.contrib.gis import admin

from .models import WaterBody, FloodZone, AdministrativeBoundary, GeospatialLayer


@admin.register(WaterBody)
class WaterBodyAdmin(admin.GISModelAdmin):
    list_display = ("name", "water_type", "source", "created_at")
    list_filter = ("water_type",)


@admin.register(FloodZone)
class FloodZoneAdmin(admin.GISModelAdmin):
    list_display = ("name", "risk_level", "source", "created_at")
    list_filter = ("risk_level",)


@admin.register(AdministrativeBoundary)
class AdministrativeBoundaryAdmin(admin.GISModelAdmin):
    list_display = ("name", "admin_level", "source", "created_at")
    list_filter = ("admin_level",)


@admin.register(GeospatialLayer)
class GeospatialLayerAdmin(admin.ModelAdmin):
    list_display = ("name", "layer_type", "is_active", "created_at")
    list_filter = ("layer_type", "is_active")
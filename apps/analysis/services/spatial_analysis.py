"""
Main orchestrator for a single analysis request.

Flow:
1. Validate and load the incoming GeoJSON polygon (SRID 4326).
2. Transform to a projected CRS (EPSG:32646 - UTM zone 46N, correct for
   the Assam/Guwahati region) to compute accurate area in km^2.
   NEVER compute area directly from lat/lon degrees - that distorts badly.
3. Query PostGIS for intersecting WaterBody records using GeoDjango's
   ORM spatial lookups (translates to ST_Intersects under the hood).
4. Compute water coverage % using the intersection geometry area.
5. Call elevation_analysis for mean elevation from the local DEM.
6. Call flood_analysis for the rule-based risk score.
7. Call population_analysis for the exposure estimate.
"""

from django.contrib.gis.geos import GEOSGeometry, Polygon
from django.contrib.gis.gdal import CoordTransform, SpatialReference

from apps.geodata.models import WaterBody
from apps.analysis.services import elevation_analysis, flood_analysis, population_analysis

PROJECTED_SRID = 32646  # UTM zone 46N - accurate for Guwahati/Assam region

# Approximate bounding box of the region we actually have reference data for
# (matches the Overpass query used to import WaterBody records). Used only
# to decide whether "0 water bodies found" means "genuinely no water nearby"
# vs "we have no data for this area at all".
DATA_COVERAGE_EXTENT = (91.60, 26.05, 91.85, 26.25)  # (minx, miny, maxx, maxy)


class InvalidGeometryError(Exception):
    pass


def _extent_overlaps_coverage(geom_extent: tuple) -> bool:
    minx, miny, maxx, maxy = geom_extent
    cov_minx, cov_miny, cov_maxx, cov_maxy = DATA_COVERAGE_EXTENT
    return not (maxx < cov_minx or minx > cov_maxx or maxy < cov_miny or miny > cov_maxy)


def validate_and_parse_geometry(geojson_geometry: dict) -> Polygon:
    """
    Parses and validates a GeoJSON geometry dict into a GEOSGeometry Polygon.
    Raises InvalidGeometryError for anything unusable.
    """
    if not geojson_geometry or geojson_geometry.get("type") != "Polygon":
        raise InvalidGeometryError("Geometry must be a GeoJSON Polygon.")

    try:
        import json
        geom = GEOSGeometry(json.dumps(geojson_geometry))
    except Exception as e:
        raise InvalidGeometryError(f"Could not parse geometry: {e}")

    if not isinstance(geom, Polygon):
        raise InvalidGeometryError("Parsed geometry is not a Polygon.")

    geom.srid = 4326

    if not geom.valid:
        raise InvalidGeometryError(f"Geometry is not valid: {geom.valid_reason}")

    if geom.empty:
        raise InvalidGeometryError("Geometry is empty.")

    # sanity bound: reject absurdly large polygons (e.g. spanning half the globe)
    # a rough guard using the bounding box extent in degrees
    minx, miny, maxx, maxy = geom.extent
    if (maxx - minx) > 5 or (maxy - miny) > 5:
        raise InvalidGeometryError(
            "Polygon extent is too large for this analysis (max ~5 degrees per side)."
        )

    return geom


def compute_area_km2(geom_4326: Polygon) -> float:
    """Transforms geometry to a projected CRS and returns area in km^2."""
    geom_projected = geom_4326.transform(PROJECTED_SRID, clone=True)
    area_m2 = geom_projected.area
    return area_m2 / 1_000_000.0


def compute_water_analysis(geom_4326: Polygon) -> dict:
    """
    Uses GeoDjango ORM spatial lookups (translates to ST_Intersects) to find
    water bodies touching the polygon, then computes coverage percentage
    using the intersection area in the projected CRS.
    """
    intersecting = WaterBody.objects.filter(geometry__intersects=geom_4326)
    count = intersecting.count()

    if count == 0:
        return {"water_bodies_intersecting": 0, "water_coverage_percent": 0.0}

    geom_projected = geom_4326.transform(PROJECTED_SRID, clone=True)
    polygon_area_m2 = geom_projected.area

    total_intersection_area_m2 = 0.0
    for water_body in intersecting:
        water_geom_projected = water_body.geometry.transform(PROJECTED_SRID, clone=True)
        intersection = geom_projected.intersection(water_geom_projected)
        total_intersection_area_m2 += intersection.area

    coverage_percent = min((total_intersection_area_m2 / polygon_area_m2) * 100, 100.0)

    return {
        "water_bodies_intersecting": count,
        "water_coverage_percent": round(coverage_percent, 2),
    }


def run_full_analysis(geojson_geometry: dict) -> dict:
    """
    Entry point called by the API view. Returns a dict matching the fields
    needed to populate an Analysis model instance.
    """
    geom = validate_and_parse_geometry(geojson_geometry)

    area_km2 = compute_area_km2(geom)
    water_data = compute_water_analysis(geom)

    mean_elevation_m = elevation_analysis.compute_mean_elevation(geojson_geometry)

    has_water_data_coverage = _extent_overlaps_coverage(geom.extent)

    flood_risk, flood_breakdown = flood_analysis.compute_flood_risk(
        mean_elevation_m=mean_elevation_m,
        water_coverage_percent=water_data["water_coverage_percent"],
        water_bodies_intersecting=water_data["water_bodies_intersecting"],
        has_water_data_coverage=has_water_data_coverage,
    )

    population_exposed = population_analysis.estimate_population_exposed(area_km2)

    return {
        "geometry": geom,
        "area_km2": round(area_km2, 4),
        "flood_risk": flood_risk,
        "mean_elevation_m": round(mean_elevation_m, 2) if mean_elevation_m is not None else None,
        "water_coverage_percent": water_data["water_coverage_percent"],
        "water_bodies_intersecting": water_data["water_bodies_intersecting"],
        "population_exposed": population_exposed,
        "result_metadata": {
            "flood_risk_breakdown": flood_breakdown,
            "projected_srid_used": PROJECTED_SRID,
        },
        "processing_status": "COMPLETE",
    }
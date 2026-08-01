"""
Population exposure estimate.

IMPORTANT (documented honestly): this MVP version does NOT yet use a real
population raster (WorldPop/Meta HRSL). It uses a documented average density
assumption for the Guwahati urban/peri-urban area (~1,200 people/km², a
published approximate figure for this region) multiplied by analyzed area.

This is intentionally isolated in its own function so it can be swapped for
a real rasterio-based zonal population count later without touching any
other part of the codebase. This limitation must be stated in the README
methodology section — do not present this as satellite-derived data.
"""

ASSUMED_DENSITY_PER_KM2 = 1200.0


def estimate_population_exposed(area_km2: float) -> int:
    """
    Args:
        area_km2: analyzed polygon area in square kilometers.

    Returns:
        Estimated population count (int), using a fixed density assumption.
    """
    return int(round(area_km2 * ASSUMED_DENSITY_PER_KM2))
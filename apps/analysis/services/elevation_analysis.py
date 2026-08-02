"""
Computes mean elevation for a given polygon by masking a local SRTM DEM tile.

Limitation (documented honestly for portfolio purposes): the MVP only has
one SRTM tile loaded (N26E091, covering Guwahati/Brahmaputra). If a polygon
falls outside this tile's bounds, elevation analysis returns None and the
caller should handle that gracefully rather than crash.
"""

import os
from pathlib import Path

import numpy as np
import rasterio
from rasterio.mask import mask
from django.conf import settings

DEM_PATH = Path(settings.BASE_DIR) / "data" / "raw" / "elevation" / "assam_dem.tif"


def compute_mean_elevation(geojson_geometry: dict) -> float | None:
    """
    Args:
        geojson_geometry: a GeoJSON Polygon dict in EPSG:4326.

    Returns:
        Mean elevation in meters, or None if the DEM tile doesn't cover
        this geometry or the file is missing.
    """
    if not DEM_PATH.exists():
        return None

    try:
        with rasterio.open(DEM_PATH) as src:
            out_image, _ = mask(src, [geojson_geometry], crop=True, filled=True, nodata=src.nodata)
            data = out_image[0].astype(float)

            if src.nodata is not None:
                data = np.where(data == src.nodata, np.nan, data)

            if np.all(np.isnan(data)):
                return None

            return float(np.nanmean(data))
    except ValueError:
        # rasterio raises ValueError when the geometry doesn't overlap the raster at all
        return None
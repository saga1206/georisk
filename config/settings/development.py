from .base import *  # noqa

DEBUG = True
ALLOWED_HOSTS = ["localhost", "127.0.0.1"]
CSRF_COOKIE_HTTPONLY = False

# GDAL/GEOS library paths — uncomment and set if Django can't auto-detect them
# GDAL_LIBRARY_PATH = "/usr/lib/x86_64-linux-gnu/libgdal.so"
# GEOS_LIBRARY_PATH = "/usr/lib/x86_64-linux-gnu/libgeos_c.so"
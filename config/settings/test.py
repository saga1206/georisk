from .base import *  # noqa

DEBUG = False
ALLOWED_HOSTS = ["*"]

DATABASES["default"]["NAME"] = "georisk_test_db"
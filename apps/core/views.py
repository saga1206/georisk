from django.shortcuts import render
from django.db import connection
from rest_framework.decorators import api_view
from rest_framework.response import Response


def home(request):
    return render(request, "home.html")


@api_view(["GET"])
def health_check(request):
    """GET /api/v1/health/ - confirms DB + PostGIS connectivity."""
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT PostGIS_Version();")
            postgis_version = cursor.fetchone()[0]
        return Response({"status": "ok", "postgis_version": postgis_version})
    except Exception as e:
        return Response({"status": "error", "detail": str(e)}, status=503)
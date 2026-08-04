import logging

from django.db.models import Avg, Count
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.generics import ListAPIView, RetrieveDestroyAPIView
from rest_framework.views import APIView
from rest_framework.response import Response

from apps.analysis.models import Analysis
from apps.analysis.serializers import AnalysisRequestSerializer, AnalysisResultSerializer
from apps.analysis.services.spatial_analysis import run_full_analysis, InvalidGeometryError
from apps.geodata.models import WaterBody

logger = logging.getLogger(__name__)


class AnalysisCreateView(APIView):
    """POST /api/v1/analysis/ - runs spatial analysis on a submitted polygon."""

    def post(self, request):
        request_serializer = AnalysisRequestSerializer(data=request.data)
        if not request_serializer.is_valid():
            return Response(request_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        geometry = request_serializer.validated_data["geometry"]

        try:
            result = run_full_analysis(geometry)
        except InvalidGeometryError as e:
            logger.warning("Invalid geometry submitted: %s", e)
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception:
            logger.exception("Unexpected error during spatial analysis")
            return Response(
                {"error": "Analysis failed due to an internal error."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        analysis = Analysis.objects.create(**result)
        logger.info(
            "Analysis %s created: risk=%s area=%.2fkm2",
            analysis.id, analysis.flood_risk, analysis.area_km2,
        )

        response_serializer = AnalysisResultSerializer(analysis)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)


class AnalysisListView(ListAPIView):
    """GET /api/v1/analyses/ - paginated history."""

    queryset = Analysis.objects.all()
    serializer_class = AnalysisResultSerializer


class AnalysisDetailView(RetrieveDestroyAPIView):
    """GET/DELETE /api/v1/analyses/{id}/"""

    queryset = Analysis.objects.all()
    serializer_class = AnalysisResultSerializer


@api_view(["GET"])
def dashboard_stats(request):
    """
    GET /api/v1/stats/ - aggregate numbers for the dashboard.
    Kept as a thin view; all aggregation is plain ORM, no business logic here.
    """
    total_analyses = Analysis.objects.count()

    risk_breakdown = dict(
        Analysis.objects.values_list("flood_risk")
        .annotate(count=Count("id"))
        .values_list("flood_risk", "count")
    )

    avg_area = Analysis.objects.aggregate(avg=Avg("area_km2"))["avg"]
    total_population_exposed = sum(
        Analysis.objects.exclude(population_exposed__isnull=True).values_list(
            "population_exposed", flat=True
        )
    )

    recent = Analysis.objects.all()[:5]
    recent_data = AnalysisResultSerializer(recent, many=True).data

    return Response({
        "total_analyses": total_analyses,
        "risk_breakdown": {
            "LOW": risk_breakdown.get("LOW", 0),
            "MODERATE": risk_breakdown.get("MODERATE", 0),
            "HIGH": risk_breakdown.get("HIGH", 0),
            "INSUFFICIENT_DATA": risk_breakdown.get("INSUFFICIENT_DATA", 0),
        },
        "average_area_km2": round(avg_area, 2) if avg_area else 0,
        "total_population_exposed": total_population_exposed,
        "water_bodies_loaded": WaterBody.objects.count(),
        "recent_analyses": recent_data,
    })
import logging

from rest_framework import status
from rest_framework.generics import ListAPIView, RetrieveDestroyAPIView
from rest_framework.views import APIView
from rest_framework.response import Response

from apps.analysis.models import Analysis
from apps.analysis.serializers import AnalysisRequestSerializer, AnalysisResultSerializer
from apps.analysis.services.spatial_analysis import run_full_analysis, InvalidGeometryError

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
from django.urls import path

from apps.analysis.views import AnalysisCreateView, AnalysisListView, AnalysisDetailView
from apps.geodata.views import GeospatialLayerListView
from apps.core.views import health_check

urlpatterns = [
    path("analysis/", AnalysisCreateView.as_view(), name="analysis-create"),
    path("analyses/", AnalysisListView.as_view(), name="analysis-list"),
    path("analyses/<uuid:pk>/", AnalysisDetailView.as_view(), name="analysis-detail"),
    path("layers/", GeospatialLayerListView.as_view(), name="layer-list"),
    path("health/", health_check, name="health-check"),
]
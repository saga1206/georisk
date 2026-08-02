from django.shortcuts import render

# Create your views here.
from rest_framework.generics import ListAPIView
from rest_framework import serializers

from apps.geodata.models import GeospatialLayer


class GeospatialLayerSerializer(serializers.ModelSerializer):
    class Meta:
        model = GeospatialLayer
        fields = ["id", "name", "layer_type", "description", "style_config", "is_active"]


class GeospatialLayerListView(ListAPIView):
    """GET /api/v1/layers/ - powers the frontend layer toggle panel."""

    queryset = GeospatialLayer.objects.filter(is_active=True)
    serializer_class = GeospatialLayerSerializer
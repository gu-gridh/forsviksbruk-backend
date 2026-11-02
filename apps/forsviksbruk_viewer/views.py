"""
Example Views

Demonstrates how to use the abstract viewsets.
"""

from forsviksbruk_backend.abstract.views import DynamicDepthViewSet, GeoViewSet

from .models import Place, Tag
from .serializers import PlaceSerializer, TagSerializer


class PlaceViewSet(GeoViewSet):
    """API endpoint for Places"""
    queryset = Place.objects.filter(published=True)
    serializer_class = PlaceSerializer
    bbox_filter_field = "geometry"


class TagViewSet(DynamicDepthViewSet):
    """API endpoint for Tags"""
    queryset = Tag.objects.filter(published=True)
    serializer_class = TagSerializer

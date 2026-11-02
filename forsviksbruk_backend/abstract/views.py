"""
Abstract Views

Generic views and viewsets for digital humanities projects.
"""

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status
from rest_framework import viewsets, pagination
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework_gis.filters import InBBoxFilter
from rest_framework_gis.pagination import GeoJsonPagination
from rest_framework import filters

from forsviksbruk_backend.abstract.schemas import GenericSchema
from . import serializers


class CountModelMixin:
    """Mixin to add count functionality to viewsets"""
    pass


class GenericPagination(pagination.LimitOffsetPagination):
    """
    The pagination of choice is limit-offset pagination.
    """
    default_limit = 20
    limit_query_param = 'limit'
    offset_query_param = 'offset'
    max_limit = 100


class GenericModelViewSet(viewsets.ReadOnlyModelViewSet):
    """
    The GenericModelViewSet allows the creation of a model agnostic model view
    with elementary filtering support and pagination.
    """
    filter_backends = [DjangoFilterBackend]
    filterset_fields = '__all__'
    pagination_class = GenericPagination
    schema = GenericSchema()

    def get_serializer_class(self):
        if self.action == 'count':
            return serializers.CountSerializer
        else:
            return self.serializer_class

    @action(detail=False, methods=["get"])
    def count(self, request, pk=None, *args, **kwargs):
        """Return count of objects matching current filters"""
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(data={'count': queryset.count()})
        
        if serializer.is_valid():        
            return Response(serializer.validated_data, status=status.HTTP_200_OK)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class DynamicDepthViewSet(GenericModelViewSet):
    """ViewSet with configurable serialization depth"""

    def get_serializer_context(self):
        context = super().get_serializer_context()
        depth = 0
        try:
            depth = int(self.request.query_params.get('depth', 0))
        except ValueError:
            pass  # Ignore non-numeric parameters and keep default 0 depth
        
        context['depth'] = depth
        return context
class GeoJsonPagePagination(GeoJsonPagination):
    """Pagination for GeoJSON responses"""
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100


class GeoViewSet(GenericModelViewSet):
    """ViewSet for geographic models with spatial filtering"""

    filter_backends = [InBBoxFilter, DjangoFilterBackend, filters.SearchFilter]
    
    # GIS filters
    # Default field name
    bbox_filter_field = 'geometry'

    # Specialized pagination
    pagination_class = GeoJsonPagePagination
    page_size = 10

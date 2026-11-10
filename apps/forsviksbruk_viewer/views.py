"""
Forsviksbruk Viewer Views

Read-only API endpoints for the multimodal map and the Digicure viewer.
"""

from digicure_viewer import views as digicure_views
from digicure_viewer.models import PointCloud
from digicure_viewer.serializers import PointCloudSerializer
from forsviksbruk_backend.abstract.views import DynamicDepthViewSet

from .models import Area, Article, Page, PointcloudAnnotation
from .serializers import (
    AreaSerializer,
    ArticleSerializer,
    PageSerializer,
    PointcloudAnnotationSerializer,
)


class AreaViewSet(DynamicDepthViewSet):
    """API endpoint for areas (e.g. Forge, Smithery)"""
    queryset = Area.objects.filter(published=True)
    serializer_class = AreaSerializer
    filterset_fields = ["id"]


class PageViewSet(DynamicDepthViewSet):
    """API endpoint for static page texts, filter with ?slug=start"""
    queryset = Page.objects.filter(published=True)
    serializer_class = PageSerializer
    filterset_fields = ["slug"]


class ArticleViewSet(DynamicDepthViewSet):
    """API endpoint for mini-articles including their spaces and links"""
    queryset = Article.objects.filter(published=True).prefetch_related("spaces", "links")
    serializer_class = ArticleSerializer
    filterset_fields = ["area"]


class PointcloudAnnotationViewSet(DynamicDepthViewSet):
    """API endpoint for annotations inside a point cloud, filter with ?pointcloud=<id>"""
    queryset = PointcloudAnnotation.objects.filter(published=True)
    serializer_class = PointcloudAnnotationSerializer
    filterset_fields = ["pointcloud", "article"]


class PointCloudViewSet(DynamicDepthViewSet):
    """API endpoint for Digicure point clouds"""
    queryset = PointCloud.objects.filter(published=True)
    serializer_class = PointCloudSerializer
    filterset_fields = ["id", "place"]


class PanoramaViewSet(digicure_views.PanoramaViewSet):
    """API endpoint for Digicure panoramas"""
    # digicure_viewer's auto-generated filterset fails on its ImageField
    filterset_fields = ["id", "place"]

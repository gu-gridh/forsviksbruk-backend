"""
Forsviksbruk Viewer Views

Read-only API endpoints for the multimodal map and the Digicure viewer.
"""

import django_filters
from digicure_viewer import views as digicure_views
from digicure_viewer.models import PointCloud
from digicure_viewer.serializers import PointCloudSerializer
from forsviksbruk_backend.abstract.views import DynamicDepthViewSet

from .models import Area, Article, ArticleMedia, Page, PointcloudAnnotation
from .serializers import (
    AreaSerializer,
    ArticleInfoSerializer,
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


class ArticleFilter(django_filters.FilterSet):
    """Filter articles with ?area=<id>"""
    area = django_filters.NumberFilter(field_name="area_link__area")

    class Meta:
        model = Article
        fields = ["area"]


class ArticleViewSet(DynamicDepthViewSet):
    """API endpoint for mini-articles including their area, spaces, links and advanced media"""
    queryset = Article.objects.filter(published=True).select_related(
        "area_link__area", *(f"advanced_media__{field}" for field in ArticleMedia.RESOURCE_FIELDS)
    ).prefetch_related("spaces", "links")
    serializer_class = ArticleSerializer
    filterset_class = ArticleFilter


class ArticleInfoFilter(ArticleFilter):
    """Filter with ?id=<id> (or ?area=<id>)"""

    class Meta(ArticleFilter.Meta):
        fields = ["id", "area"]


class ArticleInfoViewSet(DynamicDepthViewSet):
    """
    API endpoint with all details of articles: area, content spaces, links,
    advanced media with its metadata and point cloud annotations.
    Get one article with ?id=<id> (or /api/article_info/<id>/).
    """
    queryset = ArticleViewSet.queryset.prefetch_related(
        "pointcloud_annotations",
        "advanced_media__image__type_of_image",
        "advanced_media__image__author",
        "advanced_media__panorama__author",
        "advanced_media__pointcloud__author",
        "advanced_media__pointcloud__technique",
        "advanced_media__textured_model__author",
        "advanced_media__textured_model__technique",
    )
    serializer_class = ArticleInfoSerializer
    filterset_class = ArticleInfoFilter


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

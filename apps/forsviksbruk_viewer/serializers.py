"""
Forsviksbruk Viewer Serializers

Translated fields are returned in the active language (e.g. /sv/api/..., /de/api/...),
falling back to the default language when a translation is missing.
"""

from rest_framework import serializers
from forsviksbruk_backend.abstract.serializers import GenericSerializer, DynamicDepthSerializer
from .models import Area, Article, ArticleLink, ArticleSpace, Page, PointcloudAnnotation


class AreaSerializer(GenericSerializer):
    class Meta(GenericSerializer.Meta):
        model = Area
        fields = ["id", "name", "description"]


class PageSerializer(GenericSerializer):
    class Meta(GenericSerializer.Meta):
        model = Page
        fields = ["id", "slug", "title", "text"]


class ArticleSpaceSerializer(serializers.ModelSerializer):
    class Meta:
        model = ArticleSpace
        fields = ["order", "text", "image", "sound", "video_url", "caption"]


class ArticleLinkSerializer(serializers.ModelSerializer):
    class Meta:
        model = ArticleLink
        fields = ["order", "url", "label"]


class ArticleSerializer(DynamicDepthSerializer):
    area_name = serializers.CharField(source="area.name", read_only=True, default=None)
    spaces = ArticleSpaceSerializer(many=True, read_only=True)
    links = ArticleLinkSerializer(many=True, read_only=True)

    class Meta(DynamicDepthSerializer.Meta):
        model = Article
        fields = ["id", "area", "area_name", "title", "location", "spaces", "links"]


class PointcloudAnnotationSerializer(DynamicDepthSerializer):
    class Meta(DynamicDepthSerializer.Meta):
        model = PointcloudAnnotation
        fields = ["id", "pointcloud", "position", "article"]

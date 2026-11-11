"""
Forsviksbruk Viewer Serializers

Translated fields are returned in the active language (e.g. /sv/api/..., /de/api/...),
falling back to the default language when a translation is missing.
"""

from rest_framework import serializers
from forsviksbruk_backend.abstract.serializers import GenericSerializer, DynamicDepthSerializer
from .models import Area, Article, ArticleLink, ArticleMedia, ArticleSpace, Page, PointcloudAnnotation


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


class ArticleMediaSerializer(serializers.ModelSerializer):
    """The advanced media: its type (image, panorama, pointcloud, textured_model), id and title.
    The full resource is available from its own endpoint."""
    type = serializers.CharField(source="media_type", read_only=True)
    id = serializers.SerializerMethodField()
    title = serializers.SerializerMethodField()

    class Meta:
        model = ArticleMedia
        fields = ["type", "id", "title"]

    def get_id(self, obj):
        return obj.resource.pk if obj.resource else None

    def get_title(self, obj):
        return obj.resource.title if obj.resource else None


class ArticleSerializer(DynamicDepthSerializer):
    area = serializers.PrimaryKeyRelatedField(read_only=True)
    area_name = serializers.CharField(source="area.name", read_only=True, default=None)
    spaces = ArticleSpaceSerializer(many=True, read_only=True)
    links = ArticleLinkSerializer(many=True, read_only=True)
    advanced_media = ArticleMediaSerializer(read_only=True, default=None)

    class Meta(DynamicDepthSerializer.Meta):
        model = Article
        fields = ["id", "area", "area_name", "title", "location", "spaces", "links", "advanced_media"]


class PointcloudAnnotationSerializer(DynamicDepthSerializer):
    class Meta(DynamicDepthSerializer.Meta):
        model = PointcloudAnnotation
        fields = ["id", "pointcloud", "position", "article"]

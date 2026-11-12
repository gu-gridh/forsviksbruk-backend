"""
Forsviksbruk Viewer Serializers

Translated fields are returned in the active language (e.g. /sv/api/..., /de/api/...),
falling back to the default language when a translation is missing.
"""

from django.conf import settings
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
    """
    The advanced media: its type (image, panorama, pointcloud, textured_model),
    id, title and URLs.

    - url: the original image file, or the public URL of a panorama, point cloud
      or textured model
    - iiif_url: IIIF image URL (images only); add "/info.json" for a viewer such
      as OpenSeadragon, or "/full/,300/0/default.jpg" for a thumbnail
    - preview_url: preview image (point clouds and textured models, if set)
    """
    type = serializers.CharField(source="media_type", read_only=True)
    id = serializers.SerializerMethodField()
    title = serializers.SerializerMethodField()
    url = serializers.SerializerMethodField()
    iiif_url = serializers.SerializerMethodField()
    preview_url = serializers.SerializerMethodField()

    class Meta:
        model = ArticleMedia
        fields = ["type", "id", "title", "url", "iiif_url", "preview_url"]

    def _absolute(self, url):
        request = self.context.get("request")
        if url and request is not None and url.startswith("/"):
            return request.build_absolute_uri(url)
        return url or None

    def get_id(self, obj):
        return obj.resource.pk if obj.resource else None

    def get_title(self, obj):
        return obj.resource.title if obj.resource else None

    def get_url(self, obj):
        resource = obj.resource
        if resource is None:
            return None
        if obj.media_type == ArticleMedia.Type.IMAGE:
            return self._absolute(resource.file.url) if resource.file else None
        return resource.url_public or None

    def get_iiif_url(self, obj):
        if obj.media_type != ArticleMedia.Type.IMAGE or obj.resource is None:
            return None
        iiif_file = obj.resource.iiif_file
        if not iiif_file or not settings.IIIF_URL:
            return None
        return f"{settings.IIIF_URL}{iiif_file.name}"

    def get_preview_url(self, obj):
        preview = getattr(obj.resource, "preview_image", None)
        return self._absolute(preview.url) if preview else None


class ArticleSerializer(DynamicDepthSerializer):
    area = serializers.PrimaryKeyRelatedField(read_only=True)
    area_name = serializers.CharField(source="area.name", read_only=True, default=None)
    spaces = ArticleSpaceSerializer(many=True, read_only=True)
    links = ArticleLinkSerializer(many=True, read_only=True)
    advanced_media = serializers.SerializerMethodField()
    location = serializers.SerializerMethodField()

    class Meta(DynamicDepthSerializer.Meta):
        model = Article
        fields = ["id", "area", "area_name", "title", "location", "spaces", "links", "advanced_media"]

    def get_advanced_media(self, obj):
        """The advanced media, or None if there is none or its resource was deleted."""
        media = getattr(obj, "advanced_media", None)
        if media is None or media.resource is None:
            return None
        return ArticleMediaSerializer(media, context=self.context).data

    def get_location(self, obj):
        """Place on the map as {"lat": ..., "lng": ...} (Leaflet order), or None."""
        if obj.location is None:
            return None
        return {"lat": obj.location.y, "lng": obj.location.x}


class PointcloudAnnotationSerializer(DynamicDepthSerializer):
    class Meta(DynamicDepthSerializer.Meta):
        model = PointcloudAnnotation
        fields = ["id", "pointcloud", "position", "article"]

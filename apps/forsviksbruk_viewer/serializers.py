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


class ArticleMediaInfoSerializer(ArticleMediaSerializer):
    """
    The advanced media with all its metadata, for the article_info endpoint.
    Adds subtitle, description, date, authors, download URL and the fields of
    the chosen type (size for images, camera for point clouds and models...).
    """
    # Type-specific fields, read from the resource when present
    EXTRA_FIELDS = {
        ArticleMedia.Type.IMAGE: ["width", "height"],
        ArticleMedia.Type.PANORAMA: ["start_position", "north_offset"],
        ArticleMedia.Type.POINTCLOUD: ["camera_position", "look_at"],
        ArticleMedia.Type.TEXTURED_MODEL: ["camera_position", "look_at", "movement_speed", "scaled", "polygons"],
    }

    def to_representation(self, obj):
        data = super().to_representation(obj)
        resource = obj.resource
        if resource is None:
            return data
        data.update({
            "uuid": str(resource.uuid) if getattr(resource, "uuid", None) else None,
            "subtitle": getattr(resource, "subtitle", None),
            "description": resource.description,
            "date": resource.date.isoformat() if resource.date else None,
            "authors": self.get_authors(resource),
            "download_url": self.get_download_url(obj),
        })
        technique = getattr(resource, "technique", None)
        if hasattr(resource, "technique"):
            data["technique"] = technique.text if technique else None
        if obj.media_type == ArticleMedia.Type.IMAGE:
            data["types_of_image"] = [t.text for t in resource.type_of_image.all()]
        if obj.media_type == ArticleMedia.Type.TEXTURED_MODEL:
            data["format_3d"] = resource.get_format_3d_display()
        for field in self.EXTRA_FIELDS.get(obj.media_type, []):
            data[field] = getattr(resource, field)
        if obj.media_type == ArticleMedia.Type.POINTCLOUD:
            data["annotations"] = [
                {"id": a.pk, "position": a.position, "article": a.article_id}
                for a in resource.annotations.filter(published=True)
            ]
        return data

    def get_authors(self, resource):
        # Image has one author (ForeignKey), the other types several (ManyToMany)
        if obj_author := getattr(resource, "author", None):
            authors = obj_author.all() if hasattr(obj_author, "all") else [obj_author]
        else:
            authors = []
        return [{"id": a.pk, "firstname": a.firstname, "lastname": a.lastname} for a in authors]

    def get_download_url(self, obj):
        if obj.media_type == ArticleMedia.Type.IMAGE:
            return self.get_url(obj)
        return obj.resource.url_download or None


class ArticleInfoSerializer(ArticleSerializer):
    """
    Everything about one article: its metadata, area, content spaces, links,
    advanced media with all its metadata, and the point cloud annotations
    that open this article.
    """
    area = serializers.SerializerMethodField()
    pointcloud_annotations = serializers.SerializerMethodField()

    class Meta(ArticleSerializer.Meta):
        fields = [
            "id", "title", "created_at", "updated_at", "location", "area",
            "spaces", "links", "advanced_media", "pointcloud_annotations",
        ]

    def get_area(self, obj):
        area = obj.area
        if area is None:
            return None
        return {"id": area.pk, "name": area.name, "description": area.description}

    def get_advanced_media(self, obj):
        media = getattr(obj, "advanced_media", None)
        if media is None or media.resource is None:
            return None
        return ArticleMediaInfoSerializer(media, context=self.context).data

    def get_pointcloud_annotations(self, obj):
        return [
            {"id": a.pk, "pointcloud": a.pointcloud_id, "position": a.position}
            for a in obj.pointcloud_annotations.all()
            if a.published
        ]


class PointcloudAnnotationSerializer(DynamicDepthSerializer):
    class Meta(DynamicDepthSerializer.Meta):
        model = PointcloudAnnotation
        fields = ["id", "pointcloud", "position", "article"]

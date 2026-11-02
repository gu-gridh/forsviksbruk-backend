"""
Example Serializers

Demonstrates how to create serializers using the abstract framework.
"""

from forsviksbruk_backend.abstract.serializers import GenericSerializer, DynamicDepthSerializer
from .models import Place, Tag, PlaceImage


class TagSerializer(GenericSerializer):
    class Meta(GenericSerializer.Meta):
        model = Tag
        fields = ["id", "text"]


class PlaceImageSerializer(GenericSerializer):
    class Meta(GenericSerializer.Meta):
        model = PlaceImage
        fields = ["id", "uuid", "file", "caption"]


class PlaceSerializer(DynamicDepthSerializer):
    class Meta(DynamicDepthSerializer.Meta):
        model = Place
        fields = "__all__"

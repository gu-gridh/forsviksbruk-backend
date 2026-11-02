"""
Abstract Serializers

Generic serializers for digital humanities projects.
"""

from rest_framework import serializers
from drf_dynamic_fields import DynamicFieldsMixin
from django.utils.translation import gettext_lazy as _


class GenericSerializer(serializers.ModelSerializer, DynamicFieldsMixin):
    """Generic model serializer with dynamic fields support"""

    class Meta:
        model = None
        fields = '__all__'
        depth = 1


class DynamicDepthSerializer(GenericSerializer):
    """Serializer with configurable depth"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.Meta.depth = self.context.get('depth', 0)


class CountSerializer(serializers.Serializer):
    """Serializer for count endpoints"""

    count = serializers.IntegerField(
        min_value=0, 
        required=True, 
        help_text=_('Number of objects in the database.')
    )

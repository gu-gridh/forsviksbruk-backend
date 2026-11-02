"""
Project Utils

Utility functions for digital humanities projects.
"""

import json
from typing import *
from django.apps import apps
from django.urls import URLPattern, re_path, path, include
from forsviksbruk_backend.abstract import views
from rest_framework import serializers
from django.db import models
from rest_framework import routers, permissions
from rest_framework.schemas import get_schema_view
from django.views.generic import TemplateView


DEFAULT_FIELDS = ['created_at', 'updated_at', 'id']
DEFAULT_EXCLUDE = ['polymorphic_ctype']


def get_fields(model: models.Model, exclude: List[str] = DEFAULT_EXCLUDE) -> List[str]:
    """Get all field names for a model, excluding specified fields"""
    return [field.name for field in (model._meta.fields + model._meta.many_to_many) if field.name not in exclude]


def get_many_to_many_fields(model: models.Model, exclude: List[str] = DEFAULT_EXCLUDE) -> List[str]:
    """Get many-to-many field names for a model"""
    return [field.name for field in (model._meta.many_to_many) if field.name not in exclude]


def read_json(path: str, encoding='utf-8', **kwargs) -> Dict:
    """Read JSON file and return parsed content"""
    with open(path, 'r', encoding=encoding) as f:
        return json.load(f, **kwargs)


def get_serializer(model: models.Model, fields: Callable[[models.Model], List[str]] = get_fields, depth: int = 0) -> serializers.ModelSerializer:
    """Dynamically create a serializer for a model"""
    
    class Meta:
        model = model
        fields = fields(model)
        depth = depth
    
    serializer_class_name = f"{model.__name__}Serializer"
    serializer_attrs = {
        'Meta': Meta
    }
    
    return type(serializer_class_name, (serializers.ModelSerializer,), serializer_attrs)


def get_model_urls(app_label: str, base_url: str, exclude: List[str]) -> List[URLPattern]:
    """
    Dynamically generates Django URLPatterns with a basic view and serialization for models in a given app.

    Args:
        app_label (str): The app name 
        base_url (str): The base url endpoint for the model view
        exclude (List[str]): A list of model names to exclude

    Returns:
        List[URLPattern]: A list of URLPatterns to insert in the urls.py
    """

    # Fetch the application, with registered models
    app = apps.get_app_config(app_label)
    patterns = []

    # Create endpoint for each models, except the excluded ones
    for model_name, model in app.models.items():

        # Endpoints
        urls = {
            'list': rf'{base_url}/{model_name}/?$',
            'retrieve': rf'{base_url}/{model_name}/(?P<pk>[0-9]+)/',
            'count': rf'{base_url}/{model_name}/count/?$',
        }

        for action, url in urls.items():
            if model_name not in exclude:
                patterns.append(
                    re_path(
                        url, 
                        views.GenericModelViewSet.as_view({'get': action}), 
                        {
                            'queryset': model.objects.all(), 
                            'serializer_class': get_serializer(model),
                            'model': model
                        }
                    )
                )

    return patterns


def build_app_api_documentation(app_name: str, endpoint: str, template="redoc", default_version="v1", license="BSD License", **kwargs):
    """Build API documentation endpoints for an app"""

    schema = path(f'{endpoint}/schema/', 
        get_schema_view(
            title=f"{app_name.capitalize()}",
            description=f"Schema for the {app_name.capitalize()} API at the Centre for Digital Humanities",
            version="1.0.0",
            urlconf=f"apps.{app_name}.urls"
        ), 
        name=f'{app_name}-openapi-schema'
    )

    documentation = path(f'{endpoint}/documentation/', 
        TemplateView.as_view(
            template_name='templates/redoc.html',
            extra_context={'schema_url': f'{app_name}-openapi-schema'},
        ), 
        name=f'{app_name}-documentation')

    return [schema, documentation]


def build_app_endpoint(name: str):
    """Build API endpoint path for an app"""
    return f"api/{name}"


def build_contact_form_endpoint(name: str):
    """Build contact form endpoint for an app"""
    return f"{name}/contact"

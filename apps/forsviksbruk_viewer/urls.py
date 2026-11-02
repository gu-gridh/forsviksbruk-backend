"""
Example URL Configuration

Wire up the example app viewsets to URLs.
"""

from django.urls import path, include
from rest_framework import routers
from . import views

router = routers.DefaultRouter()
router.register(r"places", views.PlaceViewSet)
router.register(r"tags", views.TagViewSet)

urlpatterns = [
    path("api/example/", include(router.urls)),
]

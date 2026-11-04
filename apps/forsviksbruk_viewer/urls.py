"""
Forsviksbruk Viewer URL Configuration

Wire up the viewer app and Digicure viewsets to URLs.
"""

from django.urls import path, include
from rest_framework import routers
from digicure_viewer.urls import register_routes
from . import views

router = routers.DefaultRouter()
router.register(r"areas", views.AreaViewSet)
router.register(r"pages", views.PageViewSet)
router.register(r"articles", views.ArticleViewSet)
router.register(r"plan-annotations", views.PlanAnnotationViewSet)
router.register(r"pointcloud-annotations", views.PointcloudAnnotationViewSet)
router.register(r"pointcloud", views.PointCloudViewSet)
router.register(r"panorama", views.PanoramaViewSet, basename="panoramas")
register_routes(router, ["image", "mesh"])

urlpatterns = [
    path("api/viewer/", include(router.urls)),
]

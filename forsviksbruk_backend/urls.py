"""
forsviksbruk URL Configuration

The `urlpatterns` list routes URLs to views.
"""

from django.contrib import admin
from django.urls import path, include
from django.conf.urls.i18n import i18n_patterns
from django.utils.translation import gettext_lazy as _
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.conf.urls.static import static
from django.conf import settings
from rest_framework import routers

# Configure admin site
admin.site.index_title = _('admin.site.index_title')
admin.site.site_header = _('admin.site.site_header')
admin.site.site_title = _('admin.site.site_title')

# Create main router
router = routers.DefaultRouter()

# Basic URL patterns
urlpatterns = [
    path("i18n/", include("django.conf.urls.i18n")),
]

# Include app URLs if they exist
apps = []
for app in getattr(settings, 'APPS_LOCAL', []):
    try:
        apps.append(path('', include(f"apps.{app['name']}.urls")))
    except ImportError:
        # App doesn't have URLs defined yet
        pass

# Add i18n patterns
urlpatterns += i18n_patterns(
    path('', include(router.urls)),
    path('admin/', admin.site.urls), 
    *apps,
    prefix_default_language=False
)

# Static and media files
urlpatterns += staticfiles_urlpatterns()
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

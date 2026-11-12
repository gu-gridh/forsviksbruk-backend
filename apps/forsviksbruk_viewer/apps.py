from django.apps import AppConfig


class ForsviksbrukViewerConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.forsviksbruk_viewer'
    verbose_name = 'Forsviksbruk Viewer'


class MediaLibraryConfig(AppConfig):
    """digicure_viewer, shown as "Media library" in the admin sidebar."""
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'digicure_viewer'
    verbose_name = 'Media library'

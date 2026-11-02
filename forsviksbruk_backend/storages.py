"""
Storage Classes

Custom file storage classes for handling original and IIIF files.
Provides specialized storage for digital humanities projects.
"""

from django.core.files.storage import FileSystemStorage
from django.conf import settings


class OriginalFileStorage(FileSystemStorage):
    """Storage for original uploaded files"""
    
    def __init__(self) -> None:
        location = settings.MEDIA_ROOT
        base_url = getattr(settings, 'ORIGINAL_URL', settings.MEDIA_URL)
        super().__init__(location, base_url)


class IIIFFileStorage(FileSystemStorage):
    """Storage for IIIF-processed files"""
    
    def __init__(self) -> None:
        location = settings.MEDIA_ROOT
        base_url = getattr(settings, 'IIIF_URL', settings.MEDIA_URL)
        super().__init__(location, base_url)

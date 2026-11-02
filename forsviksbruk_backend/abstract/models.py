"""
Abstract Models

Abstract base models for digital humanities projects.
"""
from django.contrib.gis.db import models
from django.core.files import File
from django.utils.translation import gettext_lazy as _
from django.contrib.postgres.search import SearchVectorField
from django.contrib.postgres.indexes import GinIndex 
from forsviksbruk_backend.storages import OriginalFileStorage, IIIFFileStorage

from typing import *
import uuid
import os
from PIL import Image
import pyvips

Image.MAX_IMAGE_PIXELS = None  # Disable the image size limit

TIFF_KWARGS = {
    "tile": True, 
    "pyramid": True, 
    "Q": 89, 
    "tile_width": 256, 
    "tile_height": 256
}

DEFAULT_FIELDS = ['created_at', 'updated_at', 'published']
DEFAULT_EXCLUDE = ['created_at', 'updated_at', 'published', 'polymorphic_ctype']


def get_fields(model: models.Model, exclude=DEFAULT_EXCLUDE):
    """Get all field names for a model, excluding specified fields"""
    return [field.name for field in (model._meta.fields + model._meta.many_to_many) if field.name not in exclude]


def get_many_to_many_fields(model: models.Model, exclude=DEFAULT_EXCLUDE):
    """Get many-to-many field names for a model"""
    return [field.name for field in (model._meta.many_to_many) if field.name not in exclude]


def get_media_directory(instance: models.Model, label: str):
    """Get media directory path for instance"""
    # Fetches the app name, e.g. 'arosenius'
    app = instance._meta.app_label
    # Resulting directory is e.g. 'arosenius/iiif/'
    return os.path.join(app, label)


def get_save_path(instance: models.Model, filename, label: str):
    """Get save path for uploaded files"""
    # Fetches the closest directory
    directory = get_media_directory(instance, label)
    # Resulting directory is e.g. 'arosenius/iiif/picture.jpg'
    return os.path.join(directory, filename)


def get_original_path(instance: models.Model, filename):
    """Get original file save path"""
    return get_save_path(instance, filename, "original")
def get_iiif_path(instance: models.Model, filename):
    """Get IIIF file save path"""
    return get_save_path(instance, filename, "iiif")


def save_tiled_pyramid_tif(obj, path=None):
    """
    Save a tiled pyramid TIFF for IIIF serving
    """
    if not path:
        path = IIIFFileStorage().location
        
    if obj.file and hasattr(obj.file, 'path'):
        try:
            # Create IIIF pyramidized TIFF
            image = pyvips.Image.new_from_file(obj.file.path, access='sequential')
            
            # Generate IIIF file path
            iiif_filename = f"{obj.uuid}.tif"
            iiif_path = os.path.join(path, get_media_directory(obj, "iiif"), iiif_filename)
            
            # Ensure directory exists
            os.makedirs(os.path.dirname(iiif_path), exist_ok=True)
            
            # Save pyramidized TIFF
            image.tiffsave(iiif_path, **TIFF_KWARGS)
            
            # Update the model's iiif_file field
            obj.iiif_file.name = get_iiif_path(obj, iiif_filename)
            
        except Exception as e:
            # Log error but don't fail the save
            print(f"Error creating IIIF file: {e}")


class CINameField(models.CharField):
    """Case-insensitive CharField"""
    
    def __init__(self, *args, **kwargs):
        super(CINameField, self).__init__(*args, **kwargs)

    def get_prep_value(self, value):
        return str(value).lower()


class AbstractBaseModel(models.Model):
    """
    Abstract base model for all models in digital humanities projects.
    Supplies all rows with datetimes for publication and modification, 
    as well as a toggle for publication.
    """
    
    created_at = models.DateTimeField(
        auto_now_add=True, 
        verbose_name=_("abstract.created_at")
    )
    updated_at = models.DateTimeField(
        auto_now=True, 
        verbose_name=_("abstract.updated_at")
    )
    published = models.BooleanField(
        default=True, 
        verbose_name=_("abstract.published")
    )

    class Meta:
        abstract = True


class AbstractTagModel(AbstractBaseModel):
    """
    Abstract model which creates a simple tag with a case-insensitive text field.
    """
    
    text = models.CharField(
        max_length=256, 
        unique=True, 
        verbose_name=_("general.text")
    )

    class Meta:
        abstract = True

    def __str__(self):
        return self.text
    

class AbstractMetaDataModel(AbstractBaseModel):
    """
    Abstract model which creates a simple metadata structure.
    """

    text = models.CharField(
        max_length=256,
        verbose_name=_("general.text")
    )

    translation = models.CharField(
        max_length=256,
        blank=True,
        null=True,
        verbose_name=_("abstract.translation")
    )

    class Meta:
        abstract = True


class AbstractImageModel(AbstractBaseModel):
    """
    Abstract image model for digital humanities projects. 
    Supplies all images with a corresponding UUID and file upload.
    """

    # Create an automatic UUID signifier
    # This is used mainly for saving the images on the IIIF server
    uuid = models.UUIDField(
        unique=True, 
        default=uuid.uuid4, 
        editable=False
    )

    # The name of a supplied field is available in file.name
    file = models.ImageField(
        max_length=256, 
        storage=OriginalFileStorage, 
        upload_to=get_original_path, 
        verbose_name=_("general.file")
    )

    class Meta:
        abstract = True

    def __str__(self) -> str:
        return f"{self.file}"
class AbstractTIFFImageModel(AbstractImageModel):
    """
    Abstract TIFF image model for digital humanities projects. 
    Besides supplying all images with a UUID and file, it also dynamically 
    generates a pyramidization of the input file, saving it to the IIIF storage.
    """

    class Meta:
        abstract = True

    # The path to the IIIF file
    iiif_file = models.ImageField(
        max_length=256, 
        storage=IIIFFileStorage, 
        upload_to=get_iiif_path, 
        blank=True, 
        null=True, 
        verbose_name=_("abstract.iiif_file")
    )

    def save(self, **kwargs) -> None:
        # Generate IIIF pyramidized TIFF
        save_tiled_pyramid_tif(self)
        super().save(**kwargs)


class AbstractDocumentModel(AbstractBaseModel):
    """
    The abstract document model supplies a model with an automatic UUID field, 
    a text field as well as a text_vector field. The text_vector may be used 
    as a generated column to hold a tokenized version of the text field. 
    This must be generated for example by means of a PostgreSQL trigger.
    """

    # Create an automatic UUID signifier
    # This is used mainly for saving the images on the IIIF server
    uuid = models.UUIDField(
        unique=True, 
        default=uuid.uuid4, 
        editable=False
    )

    # The textual content
    text = models.TextField(
        default="", 
        verbose_name=_("general.text")
    )

    # The text vector is a generated column which holds
    # tokenized versions of all columns which should be searchable
    # Performance is vastly improved if accompanied by a manual migration 
    # which adds this column automatically, instead of at runtime
    # text_vector = SearchVectorField(
    #     null=True, 
    #     verbose_name=_("abstract.text_vector")
    # )

    class Meta:
        abstract = True
        # indexes = (GinIndex(fields=["text_vector"]),)

    def __str__(self) -> str:
        return f"{self.text[0:50]}"
    

class PlaceAbstractModel(models.Model):
    """
    Abstract model for geographical places.
    """

    place_name = models.CharField(
        max_length=256,
        verbose_name=_("general.place_name")
    )

    coordinates = models.PointField(
        geography=True,
        blank=True,
        null=True,
        verbose_name=_("abstract.coordinates")
    )

    def __str__(self) -> str:
        return self.place_name

    class Meta:
        abstract = True


class PageAbstractModel(AbstractBaseModel):
    """
    Abstract model for pages in a book or document.
    """

    page_number = models.CharField(
        max_length=50,
        verbose_name=_("abstract.page_number")
    )

    text = models.TextField(
        blank=True,
        null=True,
        verbose_name=_("general.text")
    )

    language = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name=_("abstract.language")
    )

    class Meta:
        abstract = True
        unique_together = ('page_number',)

    def __str__(self) -> str:
        return self.page_number


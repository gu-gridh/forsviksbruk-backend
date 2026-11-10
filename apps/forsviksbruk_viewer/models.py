"""
Forsviksbruk Viewer Models

Data model for the multimodal map and the Digicure viewer:

- Area: named area on the plan (e.g. "Forge"), used as DIGICURE_PLACE_MODEL
- Page: static texts for start, guide and about pages
- Article: mini-article shown next to the Digicure viewer
- ArticleSpace / ArticleLink: up to 4 content spaces and 5 end-space URLs
- PlanAnnotation: symbol on the multimodal map opening a Digicure resource
- PointcloudAnnotation: annotation symbol inside a point cloud

Media resources (PointCloud, Panorama, Object3js, Image) come from digicure_viewer.
Translatable fields are registered in translation.py.
"""

from django.contrib.gis.db import models
from django.contrib.postgres.fields import ArrayField
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.utils.translation import gettext_lazy as _
from forsviksbruk_backend.abstract.models import AbstractBaseModel
from digicure_viewer.models import Image, Object3js, Panorama, PointCloud, get_list_zeros

MAX_ARTICLE_SPACES = 4
MAX_ARTICLE_LINKS = 5


class Area(AbstractBaseModel):
    """
    A named area of the works, e.g. "Forge" or "Smithery".
    """

    name = models.CharField(
        max_length=256,
        verbose_name=_("Name"),
    )
    description = models.TextField(
        blank=True,
        verbose_name=_("Description"),
    )

    class Meta:
        verbose_name = _("Area")
        verbose_name_plural = _("Areas")
        ordering = ["name"]

    def __str__(self):
        return self.name


class Page(AbstractBaseModel):
    """
    Static text content for the frontend (start page, guide, about, map intro).
    """

    class Slug(models.TextChoices):
        START = "start", _("Start page")
        GUIDE = "guide", _("Guide page")
        ABOUT = "about", _("About page")
        MAP = "map", _("Map intro text")

    slug = models.CharField(
        max_length=32,
        choices=Slug.choices,
        unique=True,
        verbose_name=_("Page"),
    )
    title = models.CharField(
        max_length=256,
        blank=True,
        verbose_name=_("Title"),
    )
    text = models.TextField(
        blank=True,
        verbose_name=_("Text"),
    )

    class Meta:
        verbose_name = _("Page")
        verbose_name_plural = _("Pages")
        ordering = ["slug"]

    def __str__(self):
        return self.get_slug_display()


class Article(AbstractBaseModel):
    """
    Mini-article shown in the annotation panel of the Digicure viewer.
    Content is split into up to 4 spaces and an end space with up to 5 URLs.
    """

    area = models.ForeignKey(
        Area,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="articles",
        verbose_name=_("Area"),
    )
    title = models.CharField(
        max_length=256,
        verbose_name=_("Title"),
    )
    location = models.PointField(
        null=True,
        blank=True,
        verbose_name=_("Place on map"),
    )

    class Meta:
        verbose_name = _("Article")
        verbose_name_plural = _("Articles")
        ordering = ["area__name", "title"]

    def __str__(self):
        return self.title


class ArticleSpace(models.Model):
    """
    One content space of an article: free text and one media object
    (image, sound or embedded video) with a caption.
    """

    article = models.ForeignKey(
        Article,
        on_delete=models.CASCADE,
        related_name="spaces",
        verbose_name=_("Article"),
    )
    order = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(MAX_ARTICLE_SPACES)],
        verbose_name=_("Order"),
    )
    text = models.TextField(
        blank=True,
        verbose_name=_("Text"),
    )
    image = models.ImageField(
        upload_to="articles/images/",
        blank=True,
        null=True,
        verbose_name=_("Image"),
    )
    sound = models.FileField(
        upload_to="articles/sounds/",
        blank=True,
        null=True,
        verbose_name=_("Sound"),
    )
    video_url = models.URLField(
        max_length=1024,
        blank=True,
        verbose_name=_("Video URL for embed"),
    )
    caption = models.CharField(
        max_length=1024,
        blank=True,
        verbose_name=_("Caption"),
    )

    class Meta:
        verbose_name = _("Article space")
        verbose_name_plural = _("Article spaces")
        ordering = ["article", "order"]
        constraints = [
            models.UniqueConstraint(fields=["article", "order"], name="unique_article_space_order"),
        ]

    def __str__(self):
        return f"{self.article} – {self.order}"

    def clean(self):
        media = [bool(self.image), bool(self.sound), bool(self.video_url)]
        if sum(media) > 1:
            raise ValidationError(_("A space can only hold one media object: image, sound or video."))


class ArticleLink(models.Model):
    """
    URL in the end space of an article.
    """

    article = models.ForeignKey(
        Article,
        on_delete=models.CASCADE,
        related_name="links",
        verbose_name=_("Article"),
    )
    order = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(MAX_ARTICLE_LINKS)],
        verbose_name=_("Order"),
    )
    url = models.URLField(
        max_length=1024,
        verbose_name=_("URL"),
    )
    label = models.CharField(
        max_length=256,
        blank=True,
        verbose_name=_("Label"),
    )

    class Meta:
        verbose_name = _("Article link")
        verbose_name_plural = _("Article links")
        ordering = ["article", "order"]
        constraints = [
            models.UniqueConstraint(fields=["article", "order"], name="unique_article_link_order"),
        ]

    def __str__(self):
        return self.label or self.url


class PlanAnnotation(AbstractBaseModel):
    """
    Symbol on the multimodal map. Opens a resource in the Digicure viewer
    together with its initial article.
    """

    class Type(models.TextChoices):
        POINTCLOUD = "pointcloud", _("Point cloud")
        PANORAMA = "panorama", _("Panorama")
        TEXTURED_MODEL = "textured_model", _("Textured model")
        IMAGE = "image", _("Image")

    # Resource field required for each annotation type
    RESOURCE_FIELDS = {
        Type.POINTCLOUD: "pointcloud",
        Type.PANORAMA: "panorama",
        Type.TEXTURED_MODEL: "textured_model",
        Type.IMAGE: "image",
    }

    area = models.ForeignKey(
        Area,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="plan_annotations",
        verbose_name=_("Area"),
    )
    position = models.PointField(
        verbose_name=_("Position on plan"),
    )
    annotation_type = models.CharField(
        max_length=32,
        choices=Type.choices,
        verbose_name=_("Type of annotation"),
    )

    # Resource to be loaded in the Digicure viewer
    pointcloud = models.ForeignKey(
        PointCloud,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="plan_annotations",
        verbose_name=_("Point cloud"),
    )
    panorama = models.ForeignKey(
        Panorama,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="plan_annotations",
        verbose_name=_("Panorama"),
    )
    textured_model = models.ForeignKey(
        Object3js,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="plan_annotations",
        verbose_name=_("Textured model"),
    )
    image = models.ForeignKey(
        Image,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="plan_annotations",
        verbose_name=_("Image"),
    )

    # Start view in the point cloud, only used for point clouds
    camera_position = ArrayField(
        models.FloatField(),
        size=3,
        null=True,
        blank=True,
        verbose_name=_("Point cloud position"),
        help_text=_("Format: 3 comma-separated float numbers, e.g.: 0.0, 1.1, 2.2"),
    )
    look_at = ArrayField(
        models.FloatField(),
        size=3,
        null=True,
        blank=True,
        verbose_name=_("Point cloud target"),
        help_text=_("Format: 3 comma-separated float numbers, e.g.: 0.0, 1.1, 2.2"),
    )

    initial_article = models.ForeignKey(
        Article,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="plan_annotations",
        verbose_name=_("Initial article"),
    )

    class Meta:
        verbose_name = _("Plan annotation")
        verbose_name_plural = _("Plan annotations")
        ordering = ["id"]

    def __str__(self):
        return f"{self.get_annotation_type_display()}: {self.resource or '–'}"

    @property
    def resource(self):
        field = self.RESOURCE_FIELDS.get(self.annotation_type)
        return getattr(self, field) if field else None

    def clean(self):
        errors = {}
        for annotation_type, field in self.RESOURCE_FIELDS.items():
            is_set = getattr(self, f"{field}_id") is not None
            if annotation_type == self.annotation_type and not is_set:
                errors[field] = _("Required for this type of annotation.")
            elif annotation_type != self.annotation_type and is_set:
                errors[field] = _("Only the resource matching the type of annotation can be set.")
        if self.annotation_type != self.Type.POINTCLOUD and (self.camera_position or self.look_at):
            errors["camera_position"] = _("Position and target are only used for point clouds.")
        if errors:
            raise ValidationError(errors)


class PointcloudAnnotation(AbstractBaseModel):
    """
    Annotation symbol inside a point cloud that updates the mini-article.
    """

    pointcloud = models.ForeignKey(
        PointCloud,
        on_delete=models.CASCADE,
        related_name="annotations",
        verbose_name=_("Point cloud"),
    )
    position = ArrayField(
        models.FloatField(),
        size=3,
        default=get_list_zeros,
        verbose_name=_("Position in point cloud"),
        help_text=_("Format: 3 comma-separated float numbers, e.g.: 0.0, 1.1, 2.2"),
    )
    article = models.ForeignKey(
        Article,
        on_delete=models.CASCADE,
        related_name="pointcloud_annotations",
        verbose_name=_("Associated article"),
    )

    class Meta:
        verbose_name = _("Point cloud annotation")
        verbose_name_plural = _("Point cloud annotations")
        ordering = ["id"]

    def __str__(self):
        return f"{self.pointcloud} – {self.article}"

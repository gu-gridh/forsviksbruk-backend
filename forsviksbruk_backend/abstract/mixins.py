"""
Abstract Mixins

Reusable model mixins for digital humanities projects.
"""

from django.db import models
from django.utils.translation import gettext_lazy as _


class GenderedMixin(models.Model):
    """Mixin for models that need gender information"""

    GENDER_CHOICES = (
        ('M', 'Male'),
        ('F', 'Female'),
        ('-', 'Other'),
        ('X', 'Unknown'),
    )

    gender = models.CharField(
        max_length=1, 
        choices=GENDER_CHOICES, 
        blank=True, 
        null=True, 
        verbose_name=_("abstract.gender")
    )

    class Meta:
        abstract = True

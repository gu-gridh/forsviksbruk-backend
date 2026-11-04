"""
Forsviksbruk Viewer Translations

Registers translatable fields with django-modeltranslation.
Each field gets one column per language in settings.LANGUAGES (e.g. title_sv, title_en, title_de).
"""

from modeltranslation.translator import TranslationOptions, register

from .models import Area, Article, ArticleLink, ArticleSpace, Page


@register(Area)
class AreaTranslationOptions(TranslationOptions):
    fields = ("name", "description")


@register(Page)
class PageTranslationOptions(TranslationOptions):
    fields = ("title", "text")


@register(Article)
class ArticleTranslationOptions(TranslationOptions):
    fields = ("title",)


@register(ArticleSpace)
class ArticleSpaceTranslationOptions(TranslationOptions):
    fields = ("text", "caption")


@register(ArticleLink)
class ArticleLinkTranslationOptions(TranslationOptions):
    fields = ("label",)

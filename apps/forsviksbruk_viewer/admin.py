from django.contrib import admin
from leaflet.admin import LeafletGeoAdminMixin
from modeltranslation.admin import TabbedTranslationAdmin, TranslationTabularInline, TranslationStackedInline

from .models import (
    MAX_ARTICLE_LINKS,
    MAX_ARTICLE_SPACES,
    Area,
    Article,
    ArticleLink,
    ArticleSpace,
    Page,
    PointcloudAnnotation,
)


@admin.register(Area)
class AreaAdmin(TabbedTranslationAdmin):
    list_display = ["name", "published", "created_at"]
    list_filter = ["published"]
    search_fields = ["name", "description"]


@admin.register(Page)
class PageAdmin(TabbedTranslationAdmin):
    list_display = ["slug", "title", "published"]


class ArticleSpaceInline(TranslationStackedInline):
    model = ArticleSpace
    extra = 0
    max_num = MAX_ARTICLE_SPACES


class ArticleLinkInline(TranslationTabularInline):
    model = ArticleLink
    extra = 0
    max_num = MAX_ARTICLE_LINKS


@admin.register(Article)
class ArticleAdmin(LeafletGeoAdminMixin, TabbedTranslationAdmin):
    list_display = ["title", "area", "published", "updated_at"]
    list_filter = ["published", "area"]
    search_fields = ["title"]
    inlines = [ArticleSpaceInline, ArticleLinkInline]


@admin.register(PointcloudAnnotation)
class PointcloudAnnotationAdmin(admin.ModelAdmin):
    list_display = ["__str__", "pointcloud", "article", "published"]
    list_filter = ["pointcloud", "published"]
    autocomplete_fields = ["article"]

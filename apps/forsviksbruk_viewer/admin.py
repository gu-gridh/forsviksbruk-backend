from django.contrib import admin
from leaflet.admin import LeafletGeoAdminMixin
from modeltranslation.admin import TabbedTranslationAdmin, TranslationTabularInline, TranslationStackedInline

# Import digicure_viewer's admin now (this app loads first) so its registrations can be adjusted below
import digicure_viewer.admin  # noqa: F401
from digicure_viewer.admin import PreviewImageAdminMixin
from digicure_viewer.models import RTI, Object3js, ThreeDHop

from .models import (
    MAX_ARTICLE_LINKS,
    MAX_ARTICLE_SPACES,
    Area,
    Article,
    ArticleArea,
    ArticleLink,
    ArticleMedia,
    ArticleSpace,
    Page,
    PointcloudAnnotation,
)


@admin.register(Object3js)
class Object3jsAdmin(PreviewImageAdminMixin, admin.ModelAdmin):
    list_display = ["title", "url_public", "technique", "scaled"]
    search_fields = ["title", "place__name"]
    filter_horizontal = ["place", "author"]


# 3D Hop and RTI are not used in this project
admin.site.unregister([ThreeDHop, RTI])


@admin.register(Area)
class AreaAdmin(TabbedTranslationAdmin):
    list_display = ["name", "published", "created_at"]
    list_filter = ["published"]
    search_fields = ["name", "description"]


@admin.register(Page)
class PageAdmin(TabbedTranslationAdmin):
    list_display = ["slug", "title", "published"]


class ArticleAreaInline(admin.TabularInline):
    """Choose an existing area, or create a new one with "+" (edit it with the pencil)."""
    model = ArticleArea
    fields = ["area"]
    autocomplete_fields = ["area"]
    extra = 1
    max_num = 1
    verbose_name = "Area"
    verbose_name_plural = "Area"


class ArticleSpaceInline(TranslationStackedInline):
    model = ArticleSpace
    extra = 0
    max_num = MAX_ARTICLE_SPACES


class ArticleLinkInline(TranslationTabularInline):
    model = ArticleLink
    extra = 0
    max_num = MAX_ARTICLE_LINKS


class ArticleMediaInline(admin.StackedInline):
    """
    One advanced media per article: choose the type, then choose an existing
    resource of that type or upload a new one with "+".
    """
    model = ArticleMedia
    fields = ["media_type", *ArticleMedia.RESOURCE_FIELDS]
    autocomplete_fields = ArticleMedia.RESOURCE_FIELDS
    extra = 1
    max_num = 1
    verbose_name = "Advanced media"
    verbose_name_plural = "Advanced media"

    class Media:
        # Shows only the field of the chosen type
        js = ["forsviksbruk_viewer/advanced-media.js"]


@admin.register(Article)
class ArticleAdmin(LeafletGeoAdminMixin, TabbedTranslationAdmin):
    list_display = ["title", "area", "published", "updated_at"]
    list_filter = ["published", ("area_link__area", admin.RelatedOnlyFieldListFilter)]
    search_fields = ["title", "area_link__area__name"]
    inlines = [ArticleAreaInline, ArticleMediaInline, ArticleSpaceInline, ArticleLinkInline]

    def save_related(self, request, form, formsets, change):
        super().save_related(request, form, formsets, change)
        link = ArticleArea.objects.filter(article=form.instance).select_related("area").first()
        media = ArticleMedia.objects.filter(article=form.instance).first()
        if media:
            media.link_to_area(link.area if link else None)


@admin.register(PointcloudAnnotation)
class PointcloudAnnotationAdmin(admin.ModelAdmin):
    list_display = ["__str__", "pointcloud", "article", "published"]
    list_filter = ["pointcloud", "published"]
    autocomplete_fields = ["article"]

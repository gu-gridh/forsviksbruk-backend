from django.contrib import admin
from leaflet.admin import LeafletGeoAdminMixin
from modeltranslation.admin import TabbedTranslationAdmin, TranslationTabularInline, TranslationStackedInline

# Import digicure_viewer's admin now (this app loads first) so its registrations can be adjusted below
import digicure_viewer.admin  # noqa: F401
from digicure_viewer.models import RTI, Author, Image, Object3js, Panorama, PointCloud, ThreeDHop, TypeOfImage

from .models import (
    MAX_ARTICLE_LINKS,
    MAX_ARTICLE_SPACES,
    Area,
    Article,
    ArticleLink,
    ArticleMedia,
    ArticleSpace,
    Page,
    PointcloudAnnotation,
)


# Digicure media is managed from the Media inline on articles. Its admins stay
# registered, because the inline's add/edit popups and autocomplete use them,
# but they are hidden from the admin index and sidebar.
@admin.register(Object3js)
class Object3jsAdmin(admin.ModelAdmin):
    list_display = ["title", "url_public", "technique", "scaled"]
    search_fields = ["title", "place__name"]
    filter_horizontal = ["place", "author"]


def _hide_from_index(model_admin):
    model_admin.get_model_perms = lambda request: {}


for _model in (Author, TypeOfImage, Image, Object3js, Panorama, PointCloud, ThreeDHop, RTI):
    _hide_from_index(admin.site._registry[_model])


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


class ArticleMediaInline(admin.StackedInline):
    """
    Choose an existing Digicure resource, or upload a new one with the "+" button.
    New resources get the article's area as their place.
    """
    model = ArticleMedia
    extra = 0
    fields = ["order", *ArticleMedia.RESOURCE_FIELDS]
    autocomplete_fields = ArticleMedia.RESOURCE_FIELDS
    verbose_name = "Media"
    verbose_name_plural = "Media"


@admin.register(Article)
class ArticleAdmin(LeafletGeoAdminMixin, TabbedTranslationAdmin):
    list_display = ["title", "area", "published", "updated_at"]
    list_filter = ["published", "area"]
    search_fields = ["title"]
    inlines = [ArticleMediaInline, ArticleSpaceInline, ArticleLinkInline]

    class Media:
        js = ["forsviksbruk_viewer/article-media.js"]

    def save_formset(self, request, form, formset, change):
        super().save_formset(request, form, formset, change)
        if formset.model is ArticleMedia:
            for media in formset.instance.media.all():
                media.link_to_area(formset.instance.area)


@admin.register(PointcloudAnnotation)
class PointcloudAnnotationAdmin(admin.ModelAdmin):
    list_display = ["__str__", "pointcloud", "article", "published"]
    list_filter = ["pointcloud", "published"]
    autocomplete_fields = ["article"]

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
    ArticleArea,
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


for _model in (Author, TypeOfImage, Image, Object3js, Panorama, PointCloud):
    _hide_from_index(admin.site._registry[_model])

# 3D Hop and RTI are not used in this project
admin.site.unregister([ThreeDHop, RTI])


@admin.register(Area)
class AreaAdmin(TabbedTranslationAdmin):
    """Areas are chosen, created ("+") and edited (pencil) from the Article page,
    so they are hidden from the sidebar."""
    list_display = ["name", "published", "created_at"]
    list_filter = ["published"]
    search_fields = ["name", "description"]

    def get_model_perms(self, request):
        return {}


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
    Choose an existing Digicure resource, or upload a new one with the "+" button.
    On save, every resource is linked to the article's area.
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
    list_filter = ["published", ("area_link__area", admin.RelatedOnlyFieldListFilter)]
    search_fields = ["title", "area_link__area__name"]
    inlines = [ArticleAreaInline, ArticleMediaInline, ArticleSpaceInline, ArticleLinkInline]

    def save_related(self, request, form, formsets, change):
        super().save_related(request, form, formsets, change)
        link = ArticleArea.objects.filter(article=form.instance).select_related("area").first()
        for media in form.instance.media.all():
            media.link_to_area(link.area if link else None)


@admin.register(PointcloudAnnotation)
class PointcloudAnnotationAdmin(admin.ModelAdmin):
    list_display = ["__str__", "pointcloud", "article", "published"]
    list_filter = ["pointcloud", "published"]
    autocomplete_fields = ["article"]

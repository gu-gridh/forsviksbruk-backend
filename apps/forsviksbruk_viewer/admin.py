from django.contrib import admin
from .models import Place, Tag, PlaceImage


class PlaceImageInline(admin.TabularInline):
    model = PlaceImage
    extra = 1


@admin.register(Place)
class PlaceAdmin(admin.ModelAdmin):
    list_display = ["name", "published", "created_at"]
    list_filter = ["published"]
    search_fields = ["name", "description"]
    inlines = [PlaceImageInline]


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ["text", "published"]
    search_fields = ["text"]

from django.contrib import admin

from .models import Category, HistoricalEvent, Tag


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "color")
    search_fields = ("name", "description")


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "created_by", "created_at")
    search_fields = ("name",)


@admin.register(HistoricalEvent)
class HistoricalEventAdmin(admin.ModelAdmin):
    list_display = ("title", "owner", "category", "start_year", "start_calendar", "is_published")
    list_filter = ("is_published", "start_calendar", "category")
    search_fields = ("title", "description", "owner__username")
    autocomplete_fields = ("owner",)
    filter_horizontal = ("tags",)

from adminsortable2.admin import SortableAdminMixin
from django.contrib import admin
from django.contrib.admin import register
from django.utils.safestring import mark_safe

from tags import models
from utils.mixins import ViewActionMixin


class TagAdminBase(SortableAdminMixin, ViewActionMixin, admin.ModelAdmin):
    """Base class for Tag Admin"""
    icon_name = "local_offer"
    list_display = ("id", "tag_name", "action", "order")
    search_fields = ["name"]

    @staticmethod
    def tag_name(tag):
        return mark_safe(f"<span class='new badge' data-badge-caption='{tag.name}'></span>")


@register(models.Objective)
class ObjectiveAdmin(admin.ModelAdmin):
    exclude = ("created_at", "deleted_at", "updated_at", "is_deleted")


@register(models.Tag)
class TagAdmin(admin.ModelAdmin):
    """Sortable User Tags admin configuration"""
    list_display = (
        "id",
        "name",
        "order",
        "is_active"
    )
    search_fields = ["name"]


@register(models.ArticleTag)
class ArticleTagAdmin(admin.ModelAdmin):
    """Sortable Curated Article Tags admin configuration"""
    list_display = (
        "id",
        "name",
        "order"
    )
    search_fields = ["name"]


@register(models.SourceWebsite)
class SourceWebsiteAdmin(admin.ModelAdmin):
    """
    Sortable Curated Article Tags admin configuration
    """
    list_display = ("name", "url", "order")


@register(models.EventTag)
class ArticleTagAdmin(admin.ModelAdmin):
    """Sortable Curated Article Tags admin configuration"""
    icon_name = "local_offer"
    list_display = ("id", "name", "order")
    search_fields = ["name"]


@register(models.MasterClassTag)
class MasterClassTagAdmin(admin.ModelAdmin):
    """
    Sortable Master Classes Tags admin configuration
    """
    icon_name = "local_offer"
    list_display = ("id", "name", "order")
    search_fields = ["name"]


@register(models.Industry)
class IndustryTagAdmin(admin.ModelAdmin):
    """Sortable Industry Tag admin configuration"""
    icon_name = "local_offer"
    list_display = ("id", "name", "order")
    search_fields = ["name"]


@register(models.Interests)
class InterestsAdmin(admin.ModelAdmin):
    """Sortable Interests admin configuration"""
    exclude = ("created_at", "deleted_at", "updated_at", "is_deleted")
    icon_name = "local_offer"
    list_display = ("name", "icon")
    search_fields = ["name"]


@register(models.Funding)
class FundingMasterClassTagAdmin(admin.ModelAdmin):
    """Sortable Funding Tag admin configuration"""
    icon_name = "local_offer"
    list_display = ("id", "name", "order")
    search_fields = ["name"]


@register(models.Company)
class CompanyTagAdmin(admin.ModelAdmin):
    """Sortable Company Tag admin configuration"""
    icon_name = "local_offer"
    list_display = ("id", "name", "order")
    search_fields = ["name"]


@register(models.CityProxy)
class CityTagAdmin(TagAdminBase):
    """Sortable Company Tag admin configuration"""
    fields = ("name", "country")
    list_display = ("tag_name", "country", "action", "order")

    def get_queryset(self, request):
        return super().get_queryset(request).filter(is_work=False)


@register(models.WorkCityProxy)
class CityTagAdmin(TagAdminBase):
    """Sortable Company Tag admin configuration"""
    fields = ("name", "country")
    list_display = ("tag_name", "country", "action", "order")

    def get_queryset(self, request):
        return super().get_queryset(request).filter(is_work=True)


@register(models.Faq)
class FaqAdmin(admin.ModelAdmin):
    fields = (
        "category",
        "question",
        "answer",
        "order",
    )
    list_display = ("category", "question")
    exclude = ("created_at", "deleted_at", "updated_at", "is_deleted")

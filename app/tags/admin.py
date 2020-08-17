from adminsortable2.admin import SortableAdminMixin
from django.contrib import admin
from django.contrib.admin import register
from django.utils.safestring import mark_safe
from tags import models
from tags.models import Tag, ArticleTag, MasterClassTag, Industry, Funding, Company, CityProxy, WorkCityProxy, EventTag, \
    SourceWebsite, Interests
from utils.mixins import ViewActionMixin


@register(models.Objective)
class ObjectiveAdmin(admin.ModelAdmin):
    exclude = ('created_at', 'deleted_at', 'updated_at', 'is_deleted')


@register(Tag)
class TagAdmin(SortableAdminMixin, ViewActionMixin, admin.ModelAdmin):
    """
    Sortable User Tags admin configuration
    """
    icon_name = 'local_offer'
    list_display = ('tag_name', 'action', 'order')
    search_fields = ['name']

    @staticmethod
    def tag_name(tag):
        return mark_safe(f'<span class="new badge" data-badge-caption="{tag.name}"></span>')


@register(ArticleTag)
class ArticleTagAdmin(TagAdmin):
    """
    Sortable Curated Article Tags admin configuration
    """


@register(SourceWebsite)
class SourceWebsiteAdmin(TagAdmin):
    """
    Sortable Curated Article Tags admin configuration
    """
    list_display = ('tag_name', 'url', 'action', 'order')


@register(EventTag)
class ArticleTagAdmin(TagAdmin):
    """
    Sortable Curated Article Tags admin configuration
    """


@register(MasterClassTag)
class MasterClassTagAdmin(TagAdmin):
    """
    Sortable Master Classes Tags admin configuration
    """


@register(Industry)
class IndustryTagAdmin(TagAdmin):
    """
    Sortable Industry Tag admin configuration
    """


@register(Interests)
class InterestsAdmin(admin.ModelAdmin):
    """
    Sortable Interests admin configuration
    """
    exclude = ('created_at', 'deleted_at', 'updated_at', 'is_deleted')
    icon_name = 'local_offer'
    list_display = ('name', 'icon')
    search_fields = ['name']

    @staticmethod
    def tag_name(tag):
        return mark_safe(f'<span class="new badge" data-badge-caption="{tag.name}"></span>')


@register(Funding)
class FundingMasterClassTagAdmin(TagAdmin):
    """
    Sortable Funding Tag admin configuration
    """


@register(Company)
class CompanyTagAdmin(TagAdmin):
    """
    Sortable Company Tag admin configuration
    """


@register(CityProxy)
class CityTagAdmin(TagAdmin):
    """
    Sortable Company Tag admin configuration
    """
    fields = ('name', 'country')
    list_display = ('tag_name', 'country', 'action', 'order')

    def get_queryset(self, request):
        return super().get_queryset(request).filter(is_work=False)


@register(WorkCityProxy)
class CityTagAdmin(TagAdmin):
    """
    Sortable Company Tag admin configuration
    """
    fields = ('name', 'country')
    list_display = ('tag_name', 'country', 'action', 'order')

    def get_queryset(self, request):
        return super().get_queryset(request).filter(is_work=True)


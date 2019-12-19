from django.contrib import admin
from django.contrib.admin import register
from django.utils.safestring import mark_safe

from tags.models import Tag, ArticleTag, MasterClassTag
from utils.mixins import ViewActionMixin


@register(Tag)
class TagAdmin(ViewActionMixin, admin.ModelAdmin):
    icon_name = 'local_offer'
    list_display = ('tag_name', 'action')

    @staticmethod
    def tag_name(tag):
        return mark_safe(f'<span class="new badge" data-badge-caption="{tag.name}"></span>')


@register(ArticleTag)
class ArticleTagAdmin(ViewActionMixin, admin.ModelAdmin):
    icon_name = 'local_offer'
    list_display = ('tag_name', 'action')

    @staticmethod
    def tag_name(tag):
        return mark_safe(f'<span class="new badge" data-badge-caption="{tag.name}"></span>')


@register(MasterClassTag)
class MasterClassTagAdmin(ViewActionMixin, admin.ModelAdmin):
    icon_name = 'local_offer'
    list_display = ('tag_name', 'action')

    @staticmethod
    def tag_name(tag):
        return mark_safe(f'<span class="new badge" data-badge-caption="{tag.name}"></span>')

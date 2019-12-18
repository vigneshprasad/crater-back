from django.contrib import admin
from django.contrib.admin import register
from django.utils.safestring import mark_safe

from tags.models import Tag, ArticleTag, MasterClassTag


@register(Tag)
class TagAdmin(admin.ModelAdmin):
    icon_name = 'local_offer'
    list_display = ('tag_name',)

    @staticmethod
    def tag_name(tag):
        return mark_safe(f'<span class="new badge" data-badge-caption="{tag.name}"></span>')


@register(ArticleTag)
class ArticleTagAdmin(admin.ModelAdmin):
    icon_name = 'local_offer'
    list_display = ('tag_name',)

    @staticmethod
    def tag_name(tag):
        return mark_safe(f'<span class="new badge" data-badge-caption="{tag.name}"></span>')


@register(MasterClassTag)
class MasterClassTagAdmin(admin.ModelAdmin):
    icon_name = 'local_offer'
    list_display = ('tag_name',)

    @staticmethod
    def tag_name(tag):
        return mark_safe(f'<span class="new badge" data-badge-caption="{tag.name}"></span>')

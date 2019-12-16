from django.contrib.admin import ModelAdmin, register
from django.utils.safestring import mark_safe
from django.conf import settings

from resources.curated_articles.models import CuratedArticle, Tag, SourceWebsite


@register(CuratedArticle)
class CuratedArticleAdmin(ModelAdmin):
    icon_name = 'local_library'
    list_display = ('title', 'created', 'tags', 'website', 'website_url', 'image')
    list_filter = ('created', 'tag__name')
    search_fields = ('title', 'website__name', 'website__url')

    @staticmethod
    def tags(curated_article):
        return mark_safe(f'<span class="new badge" data-badge-caption="{curated_article.tag}"></span>')

    @staticmethod
    def image(curated_article):
        return mark_safe(
            f'<a href="{settings.MEDIA_URL}{curated_article.picture}">'
            f'<img height="50" width="70" src="{settings.MEDIA_URL}{curated_article.picture}">'
            f'</a>'
        )

    @staticmethod
    def website_url(curated_article):
        if not curated_article.website.url:
            return mark_safe('<i class="material-icons red-color medium-icon">highlight_off</i>')
        return mark_safe(f'<a href="{curated_article.website.url}">{curated_article.website.url}</a>')


@register(Tag)
class TagAdmin(ModelAdmin):
    icon_name = 'local_offer'
    list_display = ('tag_name',)

    @staticmethod
    def tag_name(tag):
        return mark_safe(f'<span class="new badge" data-badge-caption="{tag.name}"></span>')


@register(SourceWebsite)
class SourceWebsiteAdmin(ModelAdmin):
    icon_name = 'launch'
    list_display = ('name', 'url')

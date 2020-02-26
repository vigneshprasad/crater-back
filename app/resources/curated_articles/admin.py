from django.contrib.admin import ModelAdmin, register
from django.utils.safestring import mark_safe
from django.conf import settings

from resources.curated_articles.forms import CuratedArticleForm
from resources.curated_articles.models import CuratedArticle
from utils.mixins import ViewActionMixin


@register(CuratedArticle)
class CuratedArticleAdmin(ViewActionMixin, ModelAdmin):
    icon_name = 'local_library'
    list_display = ('title', 'created', 'tags', 'website', 'image', 'action')
    list_filter = ('created', 'tag__name')
    search_fields = ('title', 'website_tag__name', 'website_tag__url')
    form = CuratedArticleForm

    @staticmethod
    def tags(curated_article):
        return mark_safe(f'<span class="new badge" data-badge-caption="{curated_article.tag}"></span>')

    @staticmethod
    def website(curated_article):
        return mark_safe(f'<span class="new badge" data-badge-caption="{curated_article.website_tag}"></span>')

    @staticmethod
    def image(curated_article):
        return mark_safe(
            f'<a href="{settings.MEDIA_URL}{curated_article.picture}">'
            f'<img height="50" width="70" src="{settings.MEDIA_URL}{curated_article.picture}">'
            f'</a>'
        )

    @staticmethod
    def website_url(curated_article):
        if not curated_article.website_tag or not curated_article.website_tag.url:
            return mark_safe('<i class="material-icons red-color medium-icon">highlight_off</i>')
        return mark_safe(f'<a href="{curated_article.website_tag.url}">{curated_article.website_tag.url}</a>')

    def get_queryset(self, request):
        return CuratedArticle.objects.select_related('website_tag').all()

from django.contrib.admin import ModelAdmin
from django.contrib.admin import register

from resources.curated_articles import models


@register(models.CuratedArticle)
class CuratedArticleAdmin(ModelAdmin):
    icon_name = "local_library"
    list_display = ("title", "tag", "website_tag", "is_topic", "is_active")
    list_filter = ("website_tag", "tag__name", "is_topic")
    search_fields = ("title", "website_tag__name", "website_tag__url")
    exclude = ("created_at", "deleted_at", "updated_at", "is_deleted")

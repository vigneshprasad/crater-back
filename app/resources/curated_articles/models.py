from django.db import models
from django.utils.translation import ugettext_lazy as _

from base import models as base_models


class CuratedArticle(base_models.BaseModel):
    """Curated Article created by Admin."""
    title = models.CharField(_("Title"), max_length=255)
    image = models.ImageField(
        _("Picture"),
        upload_to="articles/%Y/%m/%d",
        blank=True,
        null=True,
    )
    description = models.TextField(_("Short Intro"))
    tag = models.ForeignKey(
        "tags.ArticleTag",
        verbose_name=_("Tag"),
        on_delete=models.CASCADE,
        related_name="curated_articles",
        null=True
    )
    website_tag = models.ForeignKey(
        "tags.SourceWebsite",
        verbose_name=_("Source Website"),
        on_delete=models.CASCADE,
        related_name="website_articles",
        null=True,
    )
    website_url = models.URLField(
        max_length=255,
        verbose_name=_("Website URL"),
        null=True,
    )
    is_topic = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = _("Article")
        verbose_name_plural = _("Articles")
        db_table = "resources_articles"
        ordering = ("-created_at",)

    def __str__(self):
        return self.title

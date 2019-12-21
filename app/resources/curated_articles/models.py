from django.db import models
from django.utils.translation import ugettext_lazy as _
from model_utils.models import TimeStampedModel

from tags.models import ArticleTag


class CuratedArticle(TimeStampedModel):
    """
    Curated Article created by admin
    """
    title = models.CharField(_('Title'), max_length=255)
    picture = models.ImageField(_('Picture'), upload_to='articles/%Y/%m/%d',)
    text = models.TextField(_('Short Intro'))
    tag = models.ForeignKey(
        ArticleTag,
        verbose_name=_('Tag'),
        on_delete=models.CASCADE,
        related_name='curated_articles',
        null=True
    )
    website_tag = models.ForeignKey(
        'tags.SourceWebsite',
        verbose_name=_('Source Website'),
        on_delete=models.CASCADE,
        related_name='website_articles',
        null=True
    )

    class Meta:
        verbose_name = _('Article')
        verbose_name_plural = _('Articles')
        db_table = 'resources_articles'
        ordering = ('-created',)

    def __str__(self):
        return self.title


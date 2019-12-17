from django.db import models
from django.utils.translation import ugettext_lazy as _
from model_utils.models import TimeStampedModel


class Tag(models.Model):
    """
    Tag for Article created by admin
    """
    name = models.CharField(_('Name'), max_length=255)

    class Meta:
        verbose_name = _('Tag')
        verbose_name_plural = _('Tags')
        db_table = 'resources_tags'

    def __str__(self):
        return self.name


class SourceWebsite(models.Model):
    """
    Source Website for Article created by admin
    """
    name = models.CharField(_('Name'), max_length=255)
    url = models.URLField(_('Url'), max_length=255, blank=True, null=True)

    class Meta:
        verbose_name = _('Source Website')
        verbose_name_plural = _('Source Websites')
        db_table = 'resources_websites'

    def __str__(self):
        return self.name


class CuratedArticle(TimeStampedModel):
    """
    Curated Article created by admin
    """
    title = models.CharField(_('Title'), max_length=255)
    picture = models.ImageField(_('Picture'))
    text = models.TextField(_('Short Intro'))
    tag = models.ForeignKey(Tag, verbose_name=_('Tag'), on_delete=models.CASCADE, related_name='curated_articles')
    website = models.ForeignKey(
        SourceWebsite, verbose_name=_('Source Website'), on_delete=models.CASCADE, related_name='website_articles'
    )

    class Meta:
        verbose_name = _('Article')
        verbose_name_plural = _('Articles')
        db_table = 'resources_articles'
        ordering = ('-created',)

    def __str__(self):
        return self.title


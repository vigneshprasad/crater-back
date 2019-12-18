from django.db import models
from django.utils.translation import ugettext_lazy as _


class Tag(models.Model):
    name = models.CharField(
        max_length=100,
        verbose_name=_('Name')
    )

    class Meta:
        verbose_name = _('User Tag')
        verbose_name_plural = _('User Tags')
        ordering = ['name']

    def __str__(self):
        return self.name


class MasterClassTag(models.Model):
    """
    Tag for Master Class created by admin
    """
    name = models.CharField(_('Name'), max_length=20)

    class Meta:
        verbose_name = _('Master Class Tag')
        verbose_name_plural = _('Master Class Tags')
        db_table = 'tags_masterclass_tag'

    def __str__(self):
        return self.name


class ArticleTag(models.Model):
    """
    Tag for Article created by admin
    """
    name = models.CharField(_('Name'), max_length=255)

    class Meta:
        verbose_name = _('Curated Article Tag')
        verbose_name_plural = _('Curated Article Tags')
        db_table = 'tags_article_tags'

    def __str__(self):
        return self.name

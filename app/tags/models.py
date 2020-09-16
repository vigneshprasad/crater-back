from django.db import models
from django.utils.translation import ugettext_lazy as _

from locations.models import City
from base import models as base_models
from users import choices


class Tag(models.Model):
    name = models.CharField(
        max_length=100,
        verbose_name=_('Name')
    )
    order = models.PositiveIntegerField(default=0, blank=False, null=False)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = _('User Tag')
        verbose_name_plural = _('03. User Tags')
        ordering = ['order', 'name']

    def __str__(self):
        return self.name


class Interests(base_models.BaseModel):
    """
    Interest for a users on the platform.
    """
    name = models.CharField(max_length=255)
    icon = models.FileField(blank=True, null=True)

    class Meta:
        verbose_name = _('User Interests')
        verbose_name_plural = _('11. User Interests')
        ordering = ['name']

    def __str__(self):
        return self.name


class Objective(base_models.BaseModel):
    name = models.CharField(max_length=255)
    icon = models.FileField(blank=True, null=True)
    intent = models.CharField(
        verbose_name=_('Intent'), 
        max_length=100,
        null=True, 
        blank=True,
        choices=choices.INTENT_CHOICES,
        default=choices.INTENT_NETWORK
    )
    redirect_url = models.URLField(
        verbose_name=_('Redirect URL'),
        null=True,
        blank=True,
    )

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = _('User Objective')
        verbose_name_plural = _('User Objectives')
        ordering = ['name']


class MasterClassTag(models.Model):
    """
    Tag for Master Class created by admin
    """
    name = models.CharField(_('Name'), max_length=255)
    order = models.PositiveIntegerField(default=0, blank=False, null=False)

    class Meta:
        verbose_name = _('Master Class Tag')
        verbose_name_plural = _('07. Master Class Tags')
        db_table = 'tags_masterclass_tag'
        ordering = ['order', 'name']

    def __str__(self):
        return self.name


class ArticleTag(models.Model):
    """
    Tag for Article created by admin
    """
    name = models.CharField(_('Name'), max_length=255)
    order = models.PositiveIntegerField(default=0, blank=False, null=False)

    class Meta:
        verbose_name = _('Curated Article Tag')
        verbose_name_plural = _('08. Curated Article Tags')
        db_table = 'tags_article_tags'
        ordering = ['order', 'name']

    def __str__(self):
        return self.name


class EventTag(models.Model):
    """
    Tag for Event created by admin
    """
    name = models.CharField(_('Name'), max_length=255)
    order = models.PositiveIntegerField(default=0, blank=False, null=False)

    class Meta:
        verbose_name = _('Curated Article Tag')
        verbose_name_plural = _('09. Event Tags')
        db_table = 'tags_events'
        ordering = ['order', 'name']

    def __str__(self):
        return self.name


class Industry(models.Model):
    name = models.CharField(
        max_length=255,
        verbose_name=_('Name')
    )
    order = models.PositiveIntegerField(default=0, blank=False, null=False)

    class Meta:
        verbose_name = _('Industry')
        verbose_name_plural = _('04. Industries')
        ordering = ['order', 'name']

    def __str__(self):
        return self.name


class Funding(models.Model):
    name = models.CharField(
        max_length=255,
        verbose_name=_('Name')
    )
    order = models.PositiveIntegerField(default=0, blank=False, null=False)

    class Meta:
        verbose_name = _('Funding')
        verbose_name_plural = _('05. Fundings')
        ordering = ['order', 'name']

    def __str__(self):
        return self.name


class Company(models.Model):
    name = models.CharField(
        max_length=255,
        verbose_name=_('Name')
    )
    order = models.PositiveIntegerField(default=0, blank=False, null=False)

    class Meta:
        verbose_name = _('Company')
        verbose_name_plural = _('06. Companies')
        ordering = ['order', 'name']

    def __str__(self):
        return self.name


class SourceWebsite(models.Model):
    """
    Source Website for Article created by admin
    """
    name = models.CharField(_('Name'), max_length=255)
    url = models.URLField(_('Url'), max_length=255, blank=True, null=True)
    order = models.PositiveIntegerField(default=0, blank=False, null=False)

    class Meta:
        verbose_name = _('Source Website')
        verbose_name_plural = _('10. Source Websites')
        db_table = 'tags_websites'
        ordering = ['order', 'name']

    def __str__(self):
        return self.name


class CityProxy(City):
    """
    City proxy model with relation to City, which is_work value is False
    """
    proxy = True

    class Meta:
        verbose_name = _('City')
        verbose_name_plural = _('01. Cities')
        ordering = ['order', 'name']


class WorkCityProxy(City):
    """
    City proxy model with relation to City, which is_work value is True
    """
    proxy = True

    class Meta:
        verbose_name = _('Work City')
        verbose_name_plural = _('02. Work Cities')
        ordering = ['order', 'name']

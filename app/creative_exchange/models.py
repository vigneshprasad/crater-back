from django.db import models
from django.utils.translation import ugettext_lazy as _


class ExchangeCategory(models.Model):
    name = models.CharField(
        max_length=255,
        verbose_name=_('Name')
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name=_('Active')
    )

    class Meta:
        verbose_name_plural = _('Exchange Categories')
        verbose_name = _('Exchange Category')
        ordering = ['is_active', 'name']


class ExchangeRequest(models.Model):
    category = models.ForeignKey(
        'creative_exchange.ExchangeCategory',
        on_delete=models.CASCADE,
        verbose_name=_('Exchange'),
        related_name='exchange_requests'
    )
    title = models.CharField(
        max_length=100,
        verbose_name=_('Title')
    )
    city = models.ForeignKey(
        'tags.CityProxy',
        on_delete=models.CASCADE,
        verbose_name=_('City'),
        null=True,
        related_name='exchange_requests'
    )
    days = models.PositiveIntegerField(
        verbose_name=_('Days'),
        null=True
    )
    require = models.BooleanField(
        default=False,
        verbose_name=_('Project Completion')
    )
    cover_image = models.ImageField(
        upload_to='exchange_request/cover/%Y/%m/%d/',
        verbose_name=_('Cover')
    )
    description = models.TextField(
        max_length=800,
        verbose_name=_('Description')
    )
    special_requirement = models.TextField(
        max_length=800,
        verbose_name=_('Special Requirements')
    )
    additional_information = models.TextField(
        max_length=800,
        verbose_name=_('Additional Information')
    )
    extended_price = models.PositiveIntegerField(
        verbose_name=_('Extended Price')
    )


class RequestImage(models.Model):
    request = models.ForeignKey(
        'creative_exchange.ExchangeRequest',
        related_name='files',
        verbose_name=_('Request'),
        on_delete=models.CASCADE
    )
    image = models.ImageField(
        upload_to='exchange_request/files/%Y/%m/%d/',
        verbose_name=_('Image')
    )

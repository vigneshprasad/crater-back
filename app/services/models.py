from django.contrib.postgres.fields import ArrayField
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils.translation import ugettext_lazy as _
from model_utils.models import TimeStampedModel

from services.choices import SERVICE_STATUS


class Category(TimeStampedModel):
    name = models.CharField(
        max_length=255,
        verbose_name=_('Category')
    )

    class Meta:
        verbose_name = _('Category')
        verbose_name_plural = _('Categories')


class ServiceType(TimeStampedModel):
    category = models.ForeignKey(
        'services.Category',
        on_delete=models.CASCADE,
        verbose_name=_('Category'),
        related_name='service_types'
    )
    name = models.CharField(
        max_length=255,
        verbose_name=_('Name')
    )
    description = models.TextField(
        max_length=400,
        verbose_name=_('Description')
    )
    group = models.CharField(
        max_length=100,
        choices=(
            ('service', _('Service')),
            ('call_request', _('Call request'))
        ),
        default='service'
    )

    class Meta:
        verbose_name = _('Service Type')
        verbose_name_plural = _('Service Types')


class Service(TimeStampedModel):
    user = models.ForeignKey(
        'users.User',
        on_delete=models.CASCADE,
        verbose_name=_('User'),
        related_name='services'
    )
    status = models.CharField(
        _('Status'),
        choices=SERVICE_STATUS,
        max_length=16,
        default='unknown'
    )
    service_type = models.ForeignKey(
        'services.ServiceType',
        on_delete=models.CASCADE,
        verbose_name=_('Service type'),
        related_name='services'
    )
    price_type = models.CharField(
        max_length=100,
        choices=(
            ('price', _('Price')),
            ('upon', _('Upon request'))
        ),
        default='price',
        verbose_name=_('Price type')
    )
    price = models.PositiveIntegerField(
        null=True,
        verbose_name=_('Price'),
        validators=[MaxValueValidator(999999)]
    )
    timeline = models.PositiveIntegerField(
        null=True,
        verbose_name=_('Timeline'),
        validators=[MaxValueValidator(99), MinValueValidator(1)]
    )
    revision = models.PositiveIntegerField(
        null=True,
        verbose_name=_('Revision'),
        validators=[MaxValueValidator(10), MinValueValidator(1)]
    )
    includes = models.TextField(
        max_length=800,
        verbose_name=_('Includes'),
        blank=True
    )
    attachments = ArrayField(
        models.CharField(max_length=255),
        size=3,
    )
    questions = ArrayField(
        models.CharField(max_length=255),
        size=3,
    )

    class Meta:
        verbose_name_plural = _('Services')
        verbose_name = _('Service')

    @property
    def service_type_group(self):
        return self.service_type.group

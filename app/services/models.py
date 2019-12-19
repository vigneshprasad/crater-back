from django.contrib.postgres.fields import ArrayField
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils.translation import ugettext_lazy as _
from model_utils.models import TimeStampedModel

from services.choices import SERVICE_STATUS, YEAR_OF_EXPERIENCE_CHOICES


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


class UserServiceInfo(models.Model):
    user = models.OneToOneField(
        'users.User',
        related_name='user_services_info',
        on_delete=models.CASCADE
    )
    years_of_experience = models.CharField(
        max_length=100,
        choices=YEAR_OF_EXPERIENCE_CHOICES,
        null=True,
        blank=True, verbose_name=_('Years of Experience')
    )
    bar_council = models.CharField(
        max_length=100,
        verbose_name=_('Bar council / CA identification'),
        null=True
    )
    followers = models.PositiveIntegerField(
        null=True,
        verbose_name=_('Combined followers on social networks')
    )
    industries = models.ManyToManyField(
        'tags.Industry',
        related_name='user_infos'
    )
    services = models.ManyToManyField(
        'services.Service',
        related_name='user_infos'
    )

    class Meta:
        verbose_name = _('User Service Info')
        verbose_name_plural = _('User Service Infos')


class InvestorServiceInfo(models.Model):
    user = models.OneToOneField(
        'users.User',
        related_name='investor_services_info',
        on_delete=models.CASCADE
    )
    years_of_experience = models.CharField(
        max_length=100,
        choices=YEAR_OF_EXPERIENCE_CHOICES,
        null=True,
        blank=True, verbose_name=_('Years of Experience')
    )
    number_of_startups = models.PositiveIntegerField(
        null=True,
        verbose_name=_('Number of Startups')
    )
    kind_of_funding = models.ManyToManyField(
        'tags.Funding',
        verbose_name=_('Kind of Funding')
    )
    companies = models.ManyToManyField(
        'tags.Company',
        verbose_name=_('Companies can connect to')
    )
    connect_with_us = models.BooleanField(
        default=False,
        verbose_name=_('Connect with us')
    )
    process = models.TextField(
        max_length=800,
        verbose_name=_('Process')
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
        verbose_name = _('User Investor Info')
        verbose_name_plural = _('User Investor Infos')




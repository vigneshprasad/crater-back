from django.db import models
from django.utils.translation import ugettext_lazy as _
from model_utils.models import TimeStampedModel


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

    def __str__(self):
        return self.name


class ExchangeRequest(TimeStampedModel):
    category = models.ForeignKey(
        'creative_exchange.ExchangeCategory',
        on_delete=models.CASCADE,
        verbose_name=_('Exchange'),
        related_name='exchange_requests'
    )
    user = models.ForeignKey(
        'users.User',
        on_delete=models.CASCADE,
        verbose_name=_('User'),
        related_name='exchange_requests',
        null=True
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
    is_deleted = models.BooleanField(
        verbose_name=_('Is Deleted'),
        default=False
    )

    class Meta:
        verbose_name = _('Exchange Request')
        verbose_name_plural = _('Exchange Requests')

    def __str__(self):
        return self.category.name


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

#
# class ExchangeResponse(TimeStampedModel):
#     request = models.ForeignKey(
#         'creative_exchange.ExchangeRequest',
#         on_delete=models.CASCADE,
#         verbose_name=_('Request'),
#         related_name='responses'
#     )
#     user = models.ForeignKey(
#         'users.User',
#         related_name='exchange_responses',
#         on_delete=models.CASCADE,
#         verbose_name=_('User')
#     )
#     price = models.PositiveIntegerField(
#         verbose_name=_('Price'),
#         validators=[MaxValueValidator(999999), MinValueValidator(1)]
#     )
#     timeline = models.PositiveIntegerField(
#         verbose_name=_('Timeline'),
#         validators=[MaxValueValidator(99), MinValueValidator(1)]
#     )
#     revisions = models.PositiveIntegerField(
#         verbose_name=_('Revisions'),
#         validators=[MaxValueValidator(10), MinValueValidator(1)]
#     )
#     year_of_experience = models.PositiveIntegerField(
#         verbose_name=_('Years of experience'),
#         validators=[MaxValueValidator(50), MinValueValidator(1)]
#     )
#     followers = models.PositiveIntegerField(
#         verbose_name=_('Followers'),
#         null=True
#     )
#     includes = models.TextField(
#         max_length=800,
#         verbose_name=_('Includes and Process')
#     )
#     additional_text = models.TextField(
#         max_length=800,
#         verbose_name=_('Additional text')
#     )
#     require = models.TextField(
#         max_length=800,
#         verbose_name=_('I require')
#     )
#     status = models.CharField(
#         max_length=100,
#         choices=(
#             ('approved', _('Approved')),
#             ('pending', _('Pending')),
#             ('declined', _('Declined'))
#         ),
#         default='pending'
#     )
#
#     class Meta:
#         verbose_name = _('Exchange Response')
#         verbose_name_plural = _('Exchange Responses')

import uuid

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils.translation import ugettext_lazy as _
from model_utils.models import TimeStampedModel

from .choices import ORDER_STATUS_CHOICES, FUNDING_REQUEST_CHOICES, QUOTE_STATUS_CHOICES


class Order(TimeStampedModel):
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4)
    buyer = models.ForeignKey(
        'users.User',
        related_name='buyer_orders',
        verbose_name=_('Buyer'),
        on_delete=models.CASCADE
    )
    seller = models.ForeignKey(
        'users.User',
        related_name='seller_orders',
        verbose_name=_('Seller'),
        on_delete=models.CASCADE
    )
    status = models.CharField(
        max_length=100,
        choices=ORDER_STATUS_CHOICES,
        default='created'
    )
    creative_exchange_response = models.OneToOneField(
        'creative_exchange.ExchangeResponse',
        on_delete=models.CASCADE,
        verbose_name=_('Creative exchange response'),
        null=True,
        related_name='order'
    )
    quote = models.OneToOneField(
        'order.Quote',
        on_delete=models.CASCADE,
        verbose_name=_('Quote'),
        null=True,
        related_name='order'
    )
    service = models.ForeignKey(
        'services.Service',
        on_delete=models.SET_NULL,
        null=True,
        related_name='orders',
        verbose_name=_('User Service')
    )
    note = models.TextField(
        max_length=800,
        verbose_name=_('Note from Provider'),
        blank='True'
    )

    class Meta:
        verbose_name_plural = _('Orders')
        verbose_name = _('Order')
        ordering = ['-created']


class Quote(TimeStampedModel):
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4)
    buyer = models.ForeignKey(
        'users.User',
        related_name='buyer_quotes',
        verbose_name=_('Buyer'),
        on_delete=models.CASCADE
    )
    seller = models.ForeignKey(
        'users.User',
        related_name='seller_quotes',
        verbose_name=_('Seller'),
        on_delete=models.CASCADE
    )
    status = models.CharField(
        max_length=100,
        choices=QUOTE_STATUS_CHOICES,
        default='quote_pending'
    )
    comment = models.TextField(
        max_length=800,
        verbose_name=_('Comment'),
        blank=True,
        null=True
    )
    price = models.PositiveIntegerField(
        verbose_name=_('Price'),
        null=True,
        validators=[MaxValueValidator(999999), MinValueValidator(1)]
    )
    timeline = models.PositiveIntegerField(
        verbose_name=_('Timeline'),
        null=True,
        validators=[MaxValueValidator(99), MinValueValidator(1)]
    )
    revisions = models.PositiveIntegerField(
        verbose_name=_('Revisions'),
        validators=[MaxValueValidator(10), MinValueValidator(1)],
        null=True
    )
    service = models.ForeignKey(
        'services.Service',
        related_name='quotes',
        verbose_name=_('Service'),
        on_delete=models.CASCADE
    )
    note = models.TextField(
        max_length=800,
        verbose_name=_('Note from Provider'),
        blank=True
    )

    class Meta:
        verbose_name = _('Quote')
        verbose_name_plural = _('Quotes')
        ordering = ['-created']


class Answer(models.Model):
    order = models.ForeignKey(
        'order.Order',
        on_delete=models.CASCADE,
        verbose_name=_(''),
        related_name='answers',
        null=True
    )
    quote = models.ForeignKey(
        'order.Quote',
        on_delete=models.CASCADE,
        verbose_name=_(''),
        related_name='answers',
        null=True
    )
    funding_request = models.ForeignKey(
        'order.FundingRequest',
        on_delete=models.CASCADE,
        verbose_name=_('Answers'),
        related_name='answers',
        null=True
    )
    question = models.CharField(
        verbose_name=_('Question'),
        max_length=400
    )
    text = models.TextField(
        verbose_name=_('Text'),
        max_length=800
    )

    class Meta:
        verbose_name = _('Answer')
        verbose_name_plural = _('Answers')
        ordering = ['id']


class Attachment(models.Model):
    name = models.CharField(
        max_length=255,
        verbose_name=_('Name')
    )
    order = models.ForeignKey(
        'order.Order',
        on_delete=models.CASCADE,
        verbose_name=_('Order'),
        related_name='attachments',
        null=True
    )
    funding_request = models.ForeignKey(
        'order.FundingRequest',
        on_delete=models.CASCADE,
        verbose_name=_('Funding Request'),
        related_name='attachments',
        null=True
    )
    quote = models.ForeignKey(
        'order.Quote',
        on_delete=models.CASCADE,
        verbose_name=_(''),
        related_name='attachments',
        null=True
    )

    class Meta:
        verbose_name = _('Attachment')
        verbose_name_plural = _('Attachments')
        ordering = ['id']


class AttachmentFile(models.Model):
    attachment = models.ForeignKey(
        'order.Attachment',
        verbose_name=_('Attachment'),
        related_name='files',
        on_delete=models.CASCADE
    )
    file = models.FileField(
        verbose_name=_('File')
    )

    class Meta:
        verbose_name = _('Attachment File')
        verbose_name_plural = _('Attachment Files')
        ordering = ['id']


class QuotePreference(models.Model):
    quote = models.ForeignKey(
        'order.Quote',
        on_delete=models.CASCADE,
        verbose_name=_('Quote'),
        related_name='date_preferences'
    )
    date = models.DateField(
        verbose_name=_('Date')
    )
    time_start = models.TimeField(
        verbose_name=_('Time start')
    )
    time_end = models.TimeField(
        verbose_name=_('Time end')
    )


class FundingRequest(TimeStampedModel):
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4)
    investor = models.ForeignKey(
        'users.User',
        related_name='funding_requests',
        verbose_name=_('Investor'),
        on_delete=models.CASCADE
    )
    buyer = models.ForeignKey(
        'users.User',
        related_name='buyer_funding_requests',
        verbose_name=_('Buyer'),
        on_delete=models.CASCADE
    )
    status = models.CharField(
        max_length=100,
        choices=FUNDING_REQUEST_CHOICES,
        default='pending'
    )

    class Meta:
        verbose_name = _('Funding Request')
        verbose_name_plural = _('Funding Requests')
        ordering = ['-created']

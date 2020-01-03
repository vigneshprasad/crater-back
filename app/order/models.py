import uuid

from django.db import models
from django.utils.translation import ugettext_lazy as _
from model_utils.models import TimeStampedModel

from .choices import ORDER_STATUS_CHOICES, FUNDING_REQUEST_CHOICES


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

    class Meta:
        verbose_name = _('Order')
        verbose_name_plural = _('Orders')
        ordering = ['-created']


class OrderService(models.Model):
    order = models.ForeignKey(
        'order.Order',
        on_delete=models.CASCADE,
        verbose_name=_('Order'),
        related_name='services'
    )
    service = models.ForeignKey(
        'services.Service',
        on_delete=models.CASCADE,
        verbose_name=_('Service'),
        related_name='orders'
    )

    class Meta:
        verbose_name = _('Order Service')
        verbose_name_plural = _('Order Services')
        ordering = ['id']


class Answer(models.Model):
    order_service = models.ForeignKey(
        'order.OrderService',
        on_delete=models.CASCADE,
        verbose_name=_('Order service'),
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
    order_service = models.ForeignKey(
        'order.OrderService',
        on_delete=models.CASCADE,
        verbose_name=_('Order service'),
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

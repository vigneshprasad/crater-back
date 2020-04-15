import uuid

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from django.utils.translation import ugettext_lazy as _
from model_utils.models import TimeStampedModel

from payment.models import Transaction
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
    order_field = models.IntegerField(
        default=1
    )
    completed_file = models.FileField(
        upload_to='order/completed_file/%Y/%m/%d',
        verbose_name=_('Completed File'),
        null=True
    )
    rate = models.PositiveIntegerField(
        default=5,
        verbose_name=_('Rate'),
        null=True,
        validators=[MaxValueValidator(5), MinValueValidator(1)]
    )
    review_text = models.TextField(
        max_length=800,
        verbose_name=_('Text'),
        null=True,
        blank=True
    )
    review_datetime = models.DateTimeField(
        null=True,
    )
    is_paid = models.BooleanField(
        default=False
    )

    class Meta:
        verbose_name_plural = _('Orders')
        verbose_name = _('Order')
        ordering = ['order_field', '-created']

    @property
    def price(self):
        price = 0
        if self.quote:
            if self.quote.price:
                price = self.quote.price
            elif self.quote.service:
                price = self.quote.service.price
            elif self.quote.exchange_request:
                price = self.quote.exchange_request.extended_price
        else:
            price = self.service.price
        return price

    @property
    def title(self):
        title = "Non Titled Order"
        if self.quote:
            if self.quote.service:
                title = self.quote.service.service_type.name
            elif self.quote.exchange_request:
                title = self.quote.exchange_request.title
        else:
            title = self.service.service_type.name
        return title


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
        default='pending'
    )
    comment = models.TextField(
        max_length=2000,
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
        validators=[MaxValueValidator(10), MinValueValidator(0)],
        null=True
    )
    service = models.ForeignKey(
        'services.Service',
        related_name='quotes',
        verbose_name=_('Service'),
        on_delete=models.CASCADE,
        null=True
    )
    exchange_request = models.ForeignKey(
        'creative_exchange.ExchangeRequest',
        related_name='quotes',
        verbose_name=_('Exchange Request'),
        on_delete=models.CASCADE,
        null=True
    )
    year_of_experience = models.PositiveIntegerField(
        verbose_name=_('Years of experience'),
        validators=[MaxValueValidator(50), MinValueValidator(1)],
        null=True
    )
    followers = models.PositiveIntegerField(
        verbose_name=_('Followers'),
        null=True
    )
    includes = models.TextField(
        max_length=2000,
        verbose_name=_('Includes and Process'),
        blank=True
    )
    additional_text = models.TextField(
        max_length=2000,
        verbose_name=_('Additional text'),
        blank=True
    )
    require = models.TextField(
        max_length=2000,
        verbose_name=_('I require'),
        blank=True
    )
    note = models.TextField(
        max_length=2000,
        verbose_name=_('Note from Provider'),
        blank=True
    )
    order_field = models.IntegerField(
        default=1
    )

    class Meta:
        verbose_name = _('Quote')
        verbose_name_plural = _('Quotes')
        ordering = ['order_field', '-created']


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


class OrderPreference(models.Model):
    order = models.ForeignKey(
        'order.Order',
        on_delete=models.CASCADE,
        verbose_name=_('Order'),
        related_name='order_preferences'
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
    order_field = models.IntegerField(
        default=1
    )
    comments = models.TextField(
        max_length=800,
        blank=True,
        null=True
    )

    class Meta:
        verbose_name = _('Funding Request')
        verbose_name_plural = _('Funding Requests')
        ordering = ['order_field', '-created']


@receiver(pre_save, sender=FundingRequest)
def funding_request_pre_save(sender, instance,  *args, **kwargs):
    order_dict = {
        'pending': 1,
        'accepted': 2,
        'canceled': 3
    }
    instance.order_field = order_dict.get(instance.status)
    return instance


@receiver(pre_save, sender=Order)
def order_pre_save(sender, instance,  *args, **kwargs):
    order_dict = {
        'pending': 1,
        'accepted': 1,
        'complete': 3,
        'done': 3,
        'canceled': 4,
        'created': 1
    }
    instance.order_field = order_dict.get(instance.status)
    return instance


@receiver(pre_save, sender=Quote)
def quote_pre_save(sender, instance,  *args, **kwargs):
    order_dict = {
        'pending': 1,
        'provided': 2,
        'accepted': 3,
        'canceled': 4
    }
    instance.order_field = order_dict.get(instance.status)
    return instance


@receiver(post_save, sender=Order)
def order_create_transaction(sender, instance,  created, *args, **kwargs):
    if instance.status == 'complete':
        out_transaction = instance.transactions.filter(direction='out').first()
        if instance.is_paid:
            if out_transaction:
                if out_transaction.status != 'transferred':
                    out_transaction.status = 'transferred'
                    out_transaction.save()
            else:
                Transaction.objects.create(
                    user=instance.buyer,
                    amount=instance.price,
                    order=instance,
                    direction='out',
                    status='transferred'
                )
        else:
            Transaction.objects.create(
                user=instance.seller,
                amount=instance.price,
                order=instance,
                direction='out',
                status='pending'
            )
    elif instance.status == 'canceled' and instance.is_paid and hasattr(instance, 'transaction'):
        t = instance.transaction.filter(direction='in', status='transferred')
        t.update(status='refund')


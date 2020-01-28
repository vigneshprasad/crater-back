from django.contrib.postgres.fields import JSONField
from django.db import models
from django.utils.translation import ugettext_lazy as _
from model_utils.models import TimeStampedModel


class BankDetails(TimeStampedModel):
    user = models.OneToOneField(
        'users.User',
        related_name='bank_details',
        on_delete=models.CASCADE
    )
    membership = models.CharField(
        max_length=255,
        verbose_name=_('Membership'),
        choices=(
            ('basic', _('Basic')),
            ('premium', _('Premium'))
        )
    )
    terms_and_condition = models.BooleanField(
        default=True,
        verbose_name=_('Terms and condition')
    )
    stripe_customer_id = models.CharField(
        max_length=400,
        verbose_name=_('Stripe Customer ID'),
        null=True
    )
    card_data = JSONField(
        verbose_name=_('Stripe card data'),
        null=True
    )


class Transaction(TimeStampedModel):
    user = models.ForeignKey(
        'users.User',
        related_name='transactions',
        verbose_name=_('User'),
        on_delete=models.CASCADE
    )
    amount = models.PositiveIntegerField(
        verbose_name=_('Amount')
    )
    order = models.ForeignKey(
        'order.Order',
        verbose_name=_('Order'),
        null=True,
        related_name='transactions',
        on_delete=models.CASCADE
    )
    # Direction of transaction for system
    # IN - charge money from user
    # OUT - send money to user
    direction = models.CharField(
        max_length=100,
        choices=(
            ('in', _('Income')),
            ('out', _('Outcome'))
        ),
        default='in'
    )
    # If charge id does not exists - this transaction create from admin panel
    charge_stripe_id = models.CharField(
        max_length=400,
        verbose_name=_('Charge Stripe Id'),
        null=True
    )
    status = models.CharField(
        max_length=100,
        choices=(
            ('pending', _('Pending')),
            ('refund', _('Refund')),
            ('transferred', _('Transferred'))
        )
    )

    class Meta:
        verbose_name_plural = _('Transactions')
        verbose_name = _('Transaction')
        ordering = ['-created']

    @property
    def kind(self):
        kind_data = {
            'in': 'paid',
            'out': 'received'
        }
        return kind_data.get(self.direction, 'paid')

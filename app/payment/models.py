from django.contrib.postgres.fields import JSONField
from django.db import models
from django.utils.translation import ugettext_lazy as _
from model_utils.models import TimeStampedModel

from users import choices


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
    funds_recipient = models.CharField(
        verbose_name=_('Funds Recipient'),
        choices=(
            ('individual', _('Individual')),
            ('organization', _('Organization'))
        ),
        default='individual',
        max_length=255
    )
    pan_card_number = models.CharField(
        null=True,
        blank=True,
        verbose_name=_('Pan card number'),
        max_length=255
    )
    bank_account_number = models.CharField(
        null=True,
        blank=True,
        verbose_name=_('Bank account number'),
        max_length=255
    )
    bank_account_name = models.CharField(
        null=True,
        blank=True,
        verbose_name=_('Bank account name'),
        max_length=255
    )
    bank_ifsc_code = models.CharField(
        null=True,
        blank=True,
        verbose_name=_('Bank ifsc code'),
        max_length=255
    )
    bank_name = models.CharField(
        null=True,
        blank=True,
        verbose_name=_('Bank name'),
        max_length=255
    )
    branch_name = models.CharField(
        null=True,
        blank=True,
        verbose_name=_('Branch name'),
        max_length=255
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


class Subscription(TimeStampedModel):
    user = models.ForeignKey(
        'users.User',
        related_name='subscriptions',
        verbose_name=_('User'),
        on_delete=models.CASCADE
    )
    date_start = models.DateField(
        verbose_name=_('Date start')
    )
    date_end = models.DateField(
        verbose_name=_('Date end')
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name=_('Is active')
    )
    google_receipt = JSONField(
        verbose_name=_('Google market identify'),
        null=True
    )
    apple_receipt = JSONField(
        verbose_name=_('Apple market identify'),
        null=True
    )
    is_trial = models.BooleanField(
        default=False
    )
    membership = models.CharField(
        max_length=255,
        verbose_name=_('Membership'),
        choices=(
            ('basic', _('Basic')),
            ('premium', _('Premium'))
        ),
        default='basic'
    )

    class Meta:
        verbose_name = _('Subscription')
        verbose_name_plural = _('Subscriptions')

    def send_month_warning(self):
        data = {
            self.user.email: {
                'name': self.user.name
            }
        }
        self.user.send_email(
            'One month subscription warning',
            to=[self.user.email],
            template_name=choices.template_names.get('one_month_subs_warning'),
            content={},
            merge_vars=data
        )

    def send_two_weeks_warning(self):
        data = {
            self.user.email: {
                'name': self.user.name
            }
        }
        self.user.send_email(
            'Two weeks subscription warning',
            to=[self.user.email],
            template_name=choices.template_names.get('two_weeks_subs_warning'),
            content={},
            merge_vars=data
        )

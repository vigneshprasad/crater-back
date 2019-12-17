from django.db import models
from model_utils.models import TimeStampedModel
from django.utils.translation import ugettext_lazy as _
from django.contrib.postgres.fields import JSONField


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
        verbose_name=_('Stripe Customer ID')
    )
    card_data = JSONField(
        verbose_name=_('Stripe card data')
    )

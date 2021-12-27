from django.contrib.auth import get_user_model
from django.db import models

# Create your models here.

from base import models as base_models
from crater.payments import constants


class Payment(base_models.BaseModel):

    STATUS_CHOICES = (
        (constants.PAYMENT_STATUS_PENDING, constants.PAYMENT_STATUS_PENDING.title()),
        (constants.PAYMENT_STATUS_SUCCESS, constants.PAYMENT_STATUS_SUCCESS.title()),
        (constants.PAYMENT_STATUS_FAILED, constants.PAYMENT_STATUS_FAILED.title())
    )

    user = models.ForeignKey(
        get_user_model(),
        on_delete=models.CASCADE
    )
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )
    status = models.CharField(
        max_length=16,
        choices=STATUS_CHOICES,
        default=constants.PAYMENT_STATUS_PENDING
    )
    gateway = models.CharField(max_length=16, null=True, blank=True)

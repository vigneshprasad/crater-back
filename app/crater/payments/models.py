from django.contrib.auth import get_user_model
from django.db import models

# Create your models here.

from base import models as base_models
from crater.payments import constants


class Payment(base_models.BaseModel):

    STATUS_CHOICES = (
        (constants.PAYMENT_STATUS_PENDING_ENUM, constants.PAYMENT_STATUS_PENDING),
        (constants.PAYMENT_STATUS_SUCCESS_ENUM, constants.PAYMENT_STATUS_SUCCESS),
        (constants.PAYMENT_STATUS_FAILED_ENUM, constants.PAYMENT_STATUS_FAILED)
    )

    GATEWAY_CHOICES = (
        (constants.PAYMENT_GATEWAY_STRIPE_ENUM, constants.PAYMENT_GATEWAY_STRIPE),
        (constants.PAYMENT_GATEWAY_CREATOR_UPI_ENUM, constants.PAYMENT_GATEWAY_CREATOR_UPI)
    )

    user = models.ForeignKey(
        get_user_model(),
        on_delete=models.CASCADE
    )
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )
    status = models.PositiveIntegerField(
        choices=STATUS_CHOICES,
        default=constants.PAYMENT_STATUS_PENDING_ENUM
    )
    gateway = models.PositiveIntegerField(
        choices=GATEWAY_CHOICES,
        default=constants.PAYMENT_GATEWAY_STRIPE_ENUM
    )

    def __str__(self):
        return "{} - {} - {}".format(self.id, self.user, self.amount)

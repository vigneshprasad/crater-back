from django.contrib.auth import get_user_model
from django.db import models

# Create your models here.

from base import models as base_models


class Customer(base_models.BaseModel):

    user = models.ForeignKey(
        get_user_model(),
        related_name="stripe_customer",
        on_delete=models.CASCADE
    )
    customer_id = models.CharField(
        max_length=128
    )


class PaymentIntent(base_models.BaseModel):

    customer = models.ForeignKey(
        "stripe_payments.Customer",
        related_name="payment_intents",
        on_delete=models.CASCADE
    )
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
    )
    product_id = models.IntegerField()

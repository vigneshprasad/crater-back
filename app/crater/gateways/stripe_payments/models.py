from django.contrib.auth import get_user_model
from django.contrib.postgres.fields import JSONField
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
    payment = models.ForeignKey(
        "crater_payments.Payment",
        related_name="stripe_payment_intent",
        on_delete=models.CASCADE,
        null=True,
    )
    customer = models.ForeignKey(
        "stripe_payments.Customer",
        related_name="payment_intents",
        on_delete=models.CASCADE
    )
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
    )
    intent_id = models.CharField(max_length=128, null=True,)
    client_secret = models.CharField(max_length=255, null=True,)
    product_id = models.IntegerField()
    data = JSONField(default=dict)


class PaymentCharge(base_models.BaseModel):
    payment_intent = models.ForeignKey(
        PaymentIntent,
        related_name="charges",
        on_delete=models.CASCADE
    )
    charge_id = models.CharField(max_length=128)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    amount_captured = models.DecimalField(max_digits=10, decimal_places=2)
    amount_refunded = models.DecimalField(max_digits=10, decimal_places=2)
    captured = models.BooleanField()
    data = JSONField()

from django.contrib import admin

from crater.gateways.stripe_payments import models


@admin.register(models.PaymentIntent)
class PaymentIntentAdmin(admin.ModelAdmin):
    list_display = (
        "payment",
        "customer",
        "amount",
        "intent_id",
        "product_id",
    )
    raw_id_fields = ("payment", "customer", )
    exclude = ("created_at", "deleted_at", "updated_at", "is_deleted")


@admin.register(models.PaymentCharge)
class PaymentChargeAdmin(admin.ModelAdmin):
    list_display = (
        "payment_intent",
        "charge_id",
        "amount",
        "amount_captured",
        "amount_refunded",
        "captured",
    )
    raw_id_fields = ("payment_intent", )
    exclude = ("created_at", "deleted_at", "updated_at", "is_deleted")

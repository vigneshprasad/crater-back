from django.contrib import admin
from admin_auto_filters.filters import AutocompleteFilterFactory

from crater.gateways.stripe_payments import models


@admin.register(models.PaymentIntent)
class PaymentIntentAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "payment",
        "customer",
        "amount",
        "intent_id",
        "product_id",
    )
    search_fields = (
        "customer__user__name",
        "customer__user__username",
        "id"
    )
    list_filter = (
        AutocompleteFilterFactory("Customer", "customer__user"),
    )
    raw_id_fields = ("payment", "customer", )
    exclude = ("created_at", "deleted_at", "updated_at", "is_deleted")


@admin.register(models.PaymentCharge)
class PaymentChargeAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "payment_intent",
        "charge_id",
        "amount",
        "amount_captured",
        "amount_refunded",
        "captured",
    )
    list_filter = (
        "captured",
        AutocompleteFilterFactory("Payment Intent", "payment_intent")
    )
    raw_id_fields = ("payment_intent", )
    exclude = ("created_at", "deleted_at", "updated_at", "is_deleted")

from django.contrib import admin

from crater.sales import models
from crater.sales import constants

# Register your models here.


@admin.register(models.RewardSale)
class RewardSalesAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "reward",
        "payment_type",
        "price",
        "quantity",
        "quantity_sold",
        "is_active",
        "is_closed"
    )
    list_editable = ("is_active", "is_closed")
    exclude = (
        "created_at",
        "deleted_at",
        "updated_at",
        "is_deleted"
    )


@admin.register(models.RewardSaleLog)
class RewardSaleLogAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "reward_sale",
        "price",
        "quantity",
        "status",
        "payment_type"
    )
    exclude = (
        "created_at",
        "deleted_at",
        "updated_at",
        "is_deleted"
    )

    def save_model(self, request, obj, form, change):
        if not change:
            return super(RewardSaleLogAdmin, self).save_model(request, obj, form, change)

        fields_changed = form.changed_data
        cleaned_data = form.cleaned_data

        if "status" in fields_changed:
            if cleaned_data["status"] == constants.SALE_PAYMENT_CONFIRMED_ENUM:
                obj.mark_sale_confirmed()

        return super(RewardSaleLogAdmin, self).save_model(request, obj, form, change)

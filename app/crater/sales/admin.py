from django.contrib import admin

from crater.sales import constants, models


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
    raw_id_fields = ("reward", )
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
        "payment_type",
        "is_processed"
    )
    raw_id_fields = ("user", "reward_sale")
    exclude = (
        "created_at",
        "deleted_at",
        "updated_at",
        "is_deleted"
    )
    readonly_fields = ("is_processed", "processed_at")

    def save_model(self, request, obj, form, change):
        if not change:
            return super(RewardSaleLogAdmin, self).save_model(request, obj, form, change)

        fields_changed = form.changed_data
        cleaned_data = form.cleaned_data

        if "status" in fields_changed:
            if cleaned_data["status"] == constants.SALE_PAYMENT_CONFIRMED_ENUM:
                obj.mark_sale_confirmed()

        if "status" in fields_changed:
            if cleaned_data["status"] ==  constants.SALE_PAYMENT_DECLINED_ENUM:
                obj.mark_sale_declined()

        return super(RewardSaleLogAdmin, self).save_model(request, obj, form, change)

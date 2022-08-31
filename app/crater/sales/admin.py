from django.contrib import admin

from crater.sales import models

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
    )
    list_editable = ("is_active", )
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
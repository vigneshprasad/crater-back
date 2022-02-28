from django.contrib import admin

from crater.exchange import models


@admin.register(models.Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ("coin", "number_of_coins", "buyer", "seller", "payment", "type")
    exclude = ("created_at", "deleted_at", "updated_at", "is_deleted")


@admin.register(models.UserCoinHolding)
class UserCoinHoldingAdmin(admin.ModelAdmin):
    list_display = ("coin", "user", "number_of_coins")
    exclude = ("created_at", "deleted_at", "updated_at", "is_deleted")


@admin.register(models.UserReward)
class UserRewardAdmin(admin.ModelAdmin):
    list_display = ("user", "reward", "quantity", "redeemed_quantity", "is_redeemed")
    exclude = ("created_at", "deleted_at", "updated_at", "is_deleted")
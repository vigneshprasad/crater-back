from django.contrib import admin

from crater.rewards import models


@admin.register(models.RewardType)
class RewardTypeAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "name",
        "is_active"
    )
    exclude = ("created_at", "deleted_at", "updated_at", "is_deleted")


@admin.register(models.Reward)
class RewardAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "creator",
        "name",
        "quantity",
        "number_of_coins",
        "type",
        "is_active"
    )
    exclude = ("created_at", "deleted_at", "updated_at", "is_deleted")


@admin.register(models.Redemption)
class RedemptionAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "reward",
        "object_id",
        "expires_at"
    )
    exclude = ("created_at", "deleted_at", "updated_at", "is_deleted")

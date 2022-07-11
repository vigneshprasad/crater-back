from django.contrib import admin

# Register your models here.
from tokens import models


@admin.register(models.TokenDataPerDay)
class TokenDataPerDayAdmin(admin.ModelAdmin):
    list_display = ("id", "time_spent", "engagement", "amount", "date")
    exclude = ("created_at", "deleted_at", "updated_at", "is_deleted")


@admin.register(models.TokenTransaction)
class TokenTransactionAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "creator", "time_spent", "engagement", "amount", "date", "type")
    raw_id_fields = ("user", "creator", "stream")
    exclude = ("created_at", "deleted_at", "updated_at", "is_deleted")


@admin.register(models.UserTokenLog)
class UserTokenLogAdmin(admin.ModelAdmin):
    list_display = ("user", "transaction", "amount", "type")
    raw_id_fields = ("user", "transaction")
    exclude = ("created_at", "deleted_at", "updated_at", "is_deleted")

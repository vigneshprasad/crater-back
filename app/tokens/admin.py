from django.contrib import admin

# Register your models here.
from tokens import models


@admin.register(models.TokenDataPerDay)
class TokenDataPerDayAdmin(admin.ModelAdmin):
    exclude = ("created_at", "deleted_at", "updated_at", "is_deleted")


@admin.register(models.TokenTransaction)
class TokenTransactionAdmin(admin.ModelAdmin):
    exclude = ("created_at", "deleted_at", "updated_at", "is_deleted")


@admin.register(models.UserTokenLog)
class UserTokenLogAdmin(admin.ModelAdmin):
    exclude = ("created_at", "deleted_at", "updated_at", "is_deleted")

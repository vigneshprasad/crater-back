from admin_auto_filters.filters import AutocompleteFilterFactory
from django.contrib import admin

from base import admin as base_admin
# Register your models here.
from tokens import models


@admin.register(models.TokenDataPerDay)
class TokenDataPerDayAdmin(admin.ModelAdmin):
    list_display = ("id", "time_spent", "engagement", "amount", "date")
    exclude = ("created_at", "deleted_at", "updated_at", "is_deleted")


@admin.register(models.TokenTransaction)
class TokenTransactionAdmin(admin.ModelAdmin, base_admin.ExportCsvMixin):
    list_display = ("id", "user", "creator", "time_spent", "engagement", "amount", "date", "type")
    raw_id_fields = ("user", "stream")
    list_filter = (
        AutocompleteFilterFactory("Group", "stream", use_pk_exact=True),
        AutocompleteFilterFactory("User", "user"),
    )
    exclude = ("created_at", "deleted_at", "updated_at", "is_deleted")
    actions = ["export_as_csv"]


@admin.register(models.UserTokenLog)
class UserTokenLogAdmin(admin.ModelAdmin, base_admin.ExportCsvMixin):
    list_display = ("id", "user", "transaction", "amount", "type", "date")
    raw_id_fields = ("user", "transaction")
    list_filter = (
        AutocompleteFilterFactory("Group", "transaction__stream", use_pk_exact=True),
        AutocompleteFilterFactory("User", "user"),
    )
    exclude = ("created_at", "deleted_at", "updated_at", "is_deleted")
    actions = ["export_as_csv"]

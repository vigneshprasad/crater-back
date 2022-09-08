from admin_auto_filters.filters import AutocompleteFilterFactory
from django.contrib import admin
from rangefilter import filter

from base import admin as base_admin
# Register your models here.
from tokens import models


@admin.register(models.TokenDataPerDay)
class TokenDataPerDayAdmin(admin.ModelAdmin):
    list_display = ("id", "time_spent", "engagement", "amount", "date")
    list_filter = ("date", filter.DateRangeFilter),
    exclude = ("created_at", "deleted_at", "updated_at", "is_deleted")

    @staticmethod
    def get_rangefilter_date_title(request, field_path="start"):
        """Returns the title for the start date filter."""
        return "Filter by Date"


@admin.register(models.TokenTransaction)
class TokenTransactionAdmin(admin.ModelAdmin, base_admin.ExportCsvMixin):
    list_display = ("id", "user", "stream", "time_spent", "engagement", "amount", "date", "type")
    raw_id_fields = ("user", "stream")
    list_filter = (
        AutocompleteFilterFactory("Group", "stream", use_pk_exact=True),
        AutocompleteFilterFactory("User", "user"),
        ("date",  filter.DateRangeFilter),
    )
    exclude = ("created_at", "deleted_at", "updated_at", "is_deleted")
    actions = ["export_as_csv"]

    @staticmethod
    def get_rangefilter_date_title(request, field_path="start"):
        """Returns the title for the start date filter."""
        return "Filter by Date"


@admin.register(models.UserTokenLog)
class UserTokenLogAdmin(admin.ModelAdmin, base_admin.ExportCsvMixin):
    list_display = ("id", "user", "transaction", "amount", "type", "date")
    raw_id_fields = ("user", "transaction")
    list_filter = (
        AutocompleteFilterFactory("Group", "transaction__stream", use_pk_exact=True),
        AutocompleteFilterFactory("User", "user"),
        ("date", filter.DateRangeFilter),
    )
    exclude = ("created_at", "deleted_at", "updated_at", "is_deleted")
    actions = ["export_as_csv"]

    @staticmethod
    def get_rangefilter_date_title(request, field_path="start"):
        """Returns the title for the start date filter."""
        return "Filter by Date"


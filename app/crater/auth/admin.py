from django.contrib import admin
from rangefilter import filter

from crater.auth import models


@admin.register(models.PhoneOtp)
class PhoneOtpAdmin(admin.ModelAdmin):

    list_display = ("id", "is_signup", "user", "phone_number", "otp", "successful", "used", "successful_at")
    raw_id_fields = ("user", )
    list_filter = (
        ("created_at", filter.DateRangeFilter),
        "used",
        "is_signup"
    )
    readonly_fields = ("successful", "successful_at")
    search_fields = ("user__username", "user__name", "user__email", "phone_number")
    exclude = ("created_at", "deleted_at", "updated_at", "is_deleted")

    @staticmethod
    def get_rangefilter_created_at_title(request, field_path="start"):
        """Returns the title for the start date filter."""
        return "Sent at"


@admin.register(models.PhoneOtpMetric)
class PhoneOtpMetric(admin.ModelAdmin):

    list_display = (
        "id",
        "last_successful",
        "generated_since",
        "last_successful_at",
        "notify_at"
    )
    exclude = ("created_at", "deleted_at", "updated_at", "is_deleted")

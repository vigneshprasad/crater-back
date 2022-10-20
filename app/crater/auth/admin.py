from django.contrib import admin
from rangefilter import filter

from crater.auth import models


@admin.register(models.PhoneOtp)
class PhoneOtpAdmin(admin.ModelAdmin):

    list_display = ("id", "user", "phone_number", "otp", "used", "is_expired", "created_at")
    raw_id_fields = ("user", )
    list_filter = (
        ("created_at", filter.DateRangeFilter),
        "used",
    )
    search_fields = ("user__username", "user__name", "user__email", "phone_number")
    exclude = ("deleted_at", "updated_at", "is_deleted")

    @staticmethod
    def get_rangefilter_created_at_title(request, field_path="start"):
        """Returns the title for the start date filter."""
        return "Sent at"

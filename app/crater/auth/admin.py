from django.contrib import admin

from crater.auth import models


@admin.register(models.PhoneOtp)
class PhoneOtpAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "phone_number", "otp", "used", "is_expired")
    raw_id_fields = ("user", )
    search_fields = ("user__username", "user__name", "user__email")
    exclude = ("created_at", "deleted_at", "updated_at", "is_deleted")

from django.contrib import admin

from crater.auth import models


@admin.register(models.PhoneOtp)
class PhoneOtpAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "phone_number", "otp", "used", "is_expired")
    exclude = ("created_at", "deleted_at", "updated_at", "is_deleted")

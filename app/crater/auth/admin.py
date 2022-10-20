from django.contrib import admin

from crater.auth import models


@admin.register(models.PhoneOtp)
class PhoneOtpAdmin(admin.ModelAdmin):

    list_display = ("id", "user", "phone_number", "otp", "used", "is_expired", "created_at")
    raw_id_fields = ("user", )
    search_fields = ("user__username", "user__name", "user__email", "phone_number")
    exclude = ("deleted_at", "updated_at", "is_deleted")

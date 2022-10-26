from django.contrib import admin

from integrations.twiliologs import models


@admin.register(models.SMSLog)
class SMSLogAdmin(admin.ModelAdmin):

    list_display = ("id", "phone_otp", "status", "sid", "error_code", "error_message", "updated_at")
    list_filter = ("status", )
    exclude = ("deleted_at", "created_at", "is_deleted")

from django.contrib import admin

from integrations.onesignal import models


@admin.register(models.OneSignalDevice)
class OneSignalDeviceAdmin(admin.ModelAdmin):
    exclude = ("created_at", "deleted_at", "updated_at", "is_deleted")



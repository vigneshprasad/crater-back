from django.contrib import admin

from integrations.onesignal import models


@admin.register(models.OneSignalDevice)
class OneSignalDeviceAdmin(admin.ModelAdmin):

    list_display = ("id", "user", "os_id", "created_at")
    raw_id_fields = ("user", )
    exclude = ("deleted_at", "updated_at", "is_deleted")

    def delete_queryset(self, request, queryset):
        # Hard deleting follower objects.
        queryset.delete(soft=False)

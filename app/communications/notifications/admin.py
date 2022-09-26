from django.contrib.admin import ModelAdmin, register

from communications.notifications import models


@register(models.Notification)
class NotificationAdmin(ModelAdmin):
    list_display = ("id", "name", "headings", "contents", "obj_type", "is_active")
    list_editable = ("is_active", )
    exclude = ("created_at", "deleted_at", "updated_at", "is_deleted")


@register(models.NotificationLog)
class NotificationLogsAdmin(ModelAdmin):
    list_display = ("user", "notification")
    raw_id_fields = ("user", )
    exclude = ("created_at", "deleted_at", "updated_at", "is_deleted")

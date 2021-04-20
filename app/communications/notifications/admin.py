from django.contrib.admin import ModelAdmin, register

from communications.notifications import models


@register(models.Notification)
class NotificationAdmin(ModelAdmin):
    list_display = ("id", "name", "is_active")
    exclude = ("created_at", "deleted_at", "updated_at", "is_deleted")

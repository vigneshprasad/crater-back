from django.contrib.admin import ModelAdmin, register

from communications.notifications import models


@register(models.Notification)
class MeetingInterestAdmin(ModelAdmin):
    list_display = ("id", "name")
    exclude = ("created_at", "deleted_at", "updated_at", "is_deleted")

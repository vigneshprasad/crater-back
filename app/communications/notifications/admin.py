from django.contrib.admin import ModelAdmin, register
from rangefilter import filter

from communications.notifications import models


@register(models.Notification)
class NotificationAdmin(ModelAdmin):
    list_display = ("id", "name", "headings", "contents", "obj_type", "is_active")
    list_editable = ("is_active", )
    exclude = ("created_at", "deleted_at", "updated_at", "is_deleted")


@register(models.NotificationLog)
class NotificationLogAdmin(ModelAdmin):
    list_display = ("user", "notification", "notification_json", "data", "created_at")
    raw_id_fields = ("user", )
    list_filter = (
        ("created_at", filter.DateRangeFilter),
    )
    exclude = ("created_at", "deleted_at", "updated_at", "is_deleted")

    @staticmethod
    def get_rangefilter_created_at_title(request, field_path="start"):
        """Returns the title for the start date filter."""
        return "Filter by Sent at"

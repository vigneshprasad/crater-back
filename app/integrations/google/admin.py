from django.contrib import admin

from integrations.google import models
from admin_auto_filters.filters import AutocompleteFilterFactory


@admin.register(models.GoogleCalendarEvent)
class GoogleCalendarAdminView(admin.ModelAdmin):
    list_display = (
        "user",
        "group_id",
        "meeting_id",
        "event_id",
        "status",
        "meeting_link",
        "starts_at"
    )
    search_fields = ("group_id", )
    list_filter = (AutocompleteFilterFactory("User", "user"), "status")
    exclude = ("created_at", "deleted_at", "updated_at", "is_deleted")

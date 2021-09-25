from django.contrib import admin

from integrations.google import models


@admin.register(models.GoogleCalendarEvent)
class GoogleCalendarAdminView(admin.ModelAdmin):
    list_display = ("user", "group_id", "meeting_id", "event_id", "meeting_link", "starts_at")
    exclude = ("created_at", "deleted_at", "updated_at", "is_deleted")

from django.contrib import admin
from rangefilter import filter

from conversations import models


@admin.register(models.Topic)
class TopicAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "parent", "image", "is_active")
    exclude = ("created_at", "deleted_at", "updated_at", "is_deleted")


@admin.register(models.Group)
class GroupAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "score",
        "topic",
        "group_speakers",
        "group_interests",
        "start",
        "end",
        "closed",
    )
    exclude = ("created_at", "deleted_at", "updated_at", "is_deleted")
    search_fields = ("speakers__email", )
    list_filter = (
        ("start", filter.DateRangeFilter),
        "topic"
    )

    @staticmethod
    def group_speakers(obj):
        if not obj.speakers.all():
            return ""
        return ", ".join((speaker.email or "") for speaker in obj.speakers.all())

    @staticmethod
    def group_interests(obj):
        if not obj.interests.all():
            return ""
        return ", ".join((interest.name or "") for interest in obj.interests.all())

    @staticmethod
    def get_rangefilter_start_title(request, field_path="start"):
        """Returns the title for the start date filter."""
        return "Filter by Start Date"


@admin.register(models.Invite)
class InviteAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "group",
        "invitee",
        "inviter",
        "status"
    )
    exclude = ("created_at", "deleted_at", "updated_at", "is_deleted")


@admin.register(models.Request)
class RequestAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "group",
        "requester",
        "status",
        "is_recommended"
    )
    exclude = ("created_at", "deleted_at", "updated_at", "is_deleted")

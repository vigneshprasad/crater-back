import datetime

from django.contrib import admin
from rangefilter import filter
from django_admin_row_actions import AdminRowActionsMixin

from conversations import models
from conversations import signals


@admin.register(models.SuggestedTopic)
class SuggestedTopicAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "suggested_by", "is_approved")
    exclude = ("created_at", "deleted_at", "updated_at", "is_deleted")


@admin.register(models.Topic)
class TopicAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "parent", "image", "is_active")
    exclude = ("created_at", "deleted_at", "updated_at", "is_deleted")


@admin.register(models.Group)
class GroupAdmin(AdminRowActionsMixin, admin.ModelAdmin):
    list_display = (
        "id",
        "topic",
        "type",
        "group_speakers",
        "group_attendees",
        "start",
        "end",
        "calculate_score",
        "score",
        "is_approved",
        "is_featured",
        "is_live"
    )
    readonly_fields = (
        "is_approved",
        "approved_at"
    )
    exclude = ("created_at", "deleted_at", "updated_at", "is_deleted")
    search_fields = ("speakers__email", )
    list_filter = (
        ("start", filter.DateRangeFilter),
        "topic"
    )

    def get_row_actions(self, obj):
        row_actions = [
            {
                "divided": True,
                "label": "Approve",
                "action": "approve_group",
                "enabled": obj.is_approved is False,
            },
        ]
        row_actions += super(GroupAdmin, self).get_row_actions(obj)
        return row_actions

    @staticmethod
    def approve_group(request, obj):
        if obj.is_approved:
            return
        obj.approve()

        # Sending signal for approval of a group.
        signals.conversation_approved.send(sender=obj.__class__, group=obj)

    @staticmethod
    def group_speakers(obj):
        if not obj.speakers.all():
            return ""
        return ", ".join((speaker.__str__() or "") for speaker in obj.speakers.all())

    @staticmethod
    def group_attendees(obj):
        if not obj.attendees.all():
            return ""
        return ", ".join((attendee.__str__() or "") for attendee in obj.attendees.all())

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

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


@admin.register(models.Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "is_active", "color", "color_example")
    exclude = ("created_at", "deleted_at", "updated_at", "is_deleted")


@admin.register(models.Group)
class GroupAdmin(AdminRowActionsMixin, admin.ModelAdmin):
    list_display = (
        "id",
        "topic",
        "type",
        "all_speakers",
        "attendees_count",
        "start",
        "is_featured",
        "is_live",
        "closed"
    )
    readonly_fields = (
        "closed_at",
        "approved_at",
        "last_live_at"
    )
    exclude = ("created_at", "deleted_at", "updated_at", "is_deleted")
    search_fields = ("speakers__email", "speaker__name", "speaker__username")
    list_editable = ("is_featured", "is_live", "closed")
    list_filter = (
        ("start", filter.DateRangeFilter),
        "topic"
    )

    def save_model(self, request, obj, form, change):
        if not change:
            return super(GroupAdmin, self).save_model(request, obj, form, change)

        fields_changed = form.changed_data
        cleaned_data = form.cleaned_data
        if "closed" in fields_changed:
            if cleaned_data["closed"]:
                obj.mark_closed()

        if "is_approved" in fields_changed:
            if cleaned_data["is_approved"]:
                obj.approve()

        if "is_live" in fields_changed:
            if cleaned_data["is_live"]:
                obj.mark_live()

        return super(GroupAdmin, self).save_model(request, obj, form, change)

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.select_related(
            "host",
            "topic"
        ).prefetch_related(
            "speakers",
            "attendees",
            "interests",
            "categories"
        ).all()

    @staticmethod
    def all_speakers(obj):
        return [speaker.username for speaker in obj.speakers.all()]

    @staticmethod
    def speaker_count(obj):
        return obj.speakers.count()

    @staticmethod
    def attendees_count(obj):
        return obj.attendees.count()

    @staticmethod
    def get_rangefilter_start_title(request, field_path="start"):
        """Returns the title for the start date filter."""
        return "Start Date"


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

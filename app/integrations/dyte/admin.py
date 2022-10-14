from admin_auto_filters.filters import AutocompleteFilterFactory
from rangefilter import filter
from django.contrib import admin, messages

from integrations.dyte import models, tasks


@admin.register(models.DyteMeeting)
class DyteMeetingAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "dyte_meeting_id",
        "room_name",
        "group",
        "meeting",
    )
    raw_id_fields = ("group", "meeting", )
    exclude = ("created_at", "deleted_at", "updated_at", "is_deleted")
    list_filter = (
        AutocompleteFilterFactory("Group", "group"),
        ("group__start",  filter.DateRangeFilter),
    )
    search_fields = (
        "group__id",
        "group__host__name",
        "group__host__username"
    )

    @staticmethod
    def get_rangefilter_group__start_title(request, field_path="start"):
        """Returns the title for the start date filter."""
        return "Filter by Group Start"


@admin.register(models.DyteMeetingParticipant)
class DyteMeetingParticipantAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "is_online",
        "participant",
        "joined_stream",
        "last_online_at",
        "minutes_spent",
        "total_minutes_watched",
        "dyte_meeting"
    )
    raw_id_fields = ("participant", "dyte_meeting")
    list_select_related = (
        "participant",
        "dyte_meeting__group__topic",
        "dyte_meeting__group__host",
        "dyte_meeting__meeting"
    )
    exclude = ("auth_token", "created_at", "deleted_at", "updated_at", "is_deleted")
    list_filter = (
        "is_online",
        AutocompleteFilterFactory("Group", "dyte_meeting__group"),
        ("dyte_meeting__group__start", filter.DateRangeFilter)
    )
    search_fields = (
        "participant__name",
        "participant__username"
    )

    def joined_stream(self, obj):
        return obj.joined_group

    joined_stream.boolean = True

    @staticmethod
    def get_rangefilter_dyte_meeting__group__start_title(request, field_path="start"):
        """Returns the title for the start date filter."""
        return "Filter by Group Start"


@admin.register(models.DyteParticipantOnlineLog)
class DyteParticipantOnlineLogAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "dyte_meeting_participant",
        "is_online",
        "online_at",
        "offline_at",
        "online_time"
    )
    raw_id_fields = ("dyte_meeting_participant", )
    list_filter = (
        "is_offline",
        AutocompleteFilterFactory("By Participant", "dyte_meeting_participant__participant"),
        AutocompleteFilterFactory("By Group", "dyte_meeting_participant__dyte_meeting__group"),
    )
    exclude = ("created_at", "deleted_at", "updated_at", "is_deleted")

    def is_online(self, obj):
        return not obj.is_offline

    is_online.boolean = True


@admin.register(models.DyteMeetingRecording)
class DyteMeetingRecordingAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "dyte_meeting",
        "status",
        "recording_id",
        "object_url",
        "file_size",
        "started_at",
        "stopped_at"
    )
    raw_id_fields = ("dyte_meeting", )
    exclude = ("created_at", "deleted_at", "updated_at", "is_deleted")
    actions = ("update_recording_status", )
    list_filter = (
        AutocompleteFilterFactory("Group", "dyte_meeting__group"),
        "status",
        "created_at"
    )
    search_fields = (
        "recording_id",
        "dyte_meeting__group__host__name"
    )

    def update_recording_status(self, request, queryset):
        """Adds previous webinar attendees to the provided webinar.

        Args:
            request(Request): Request build by admin.
            queryset(Queryset): Query set of recording we are
                update the status for.

        """
        recording_ids = list(queryset.values_list("id", flat=True))
        tasks.update_meeting_recording_status_for_recording_ids.delay(recording_ids)

        # Create a log entry.
        for obj in queryset:
            self.log_change(
                request,
                obj,
                message=[{"changed": {"actions": ["update_recording_status"]}}]
            )

        self.message_user(
            request,
            "Recording status updated for: {}".format(
                ", ".join([str(recording.id) for recording in queryset])
            ),
            messages.SUCCESS
        )

    update_recording_status.short_description = "Update Recording Status"


@admin.register(models.LiveStream)
class LiveStreamAdmin(admin.ModelAdmin):

    list_display = ("id", "dyte_meeting", "livestream_id", "status")
    raw_id_fields = ("dyte_meeting", )
    list_filter = (
        AutocompleteFilterFactory("Group", "dyte_meeting__group"),
        "status"
    )
    exclude = ("created_at", "deleted_at", "updated_at", "is_deleted")

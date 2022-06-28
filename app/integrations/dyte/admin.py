from admin_auto_filters.filters import AutocompleteFilterFactory
from django.contrib import admin

from integrations.dyte import models


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
        "group__start"
    )
    search_fields = (
        "group__id",
        "group__host__name",
        "group__host__username"
    )


@admin.register(models.DyteMeetingParticipant)
class DyteMeetingParticipantAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "is_online",
        "participant",
        "joined_stream",
        "last_online_at",
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
        "dyte_meeting__group__start"
    )
    search_fields = (
        "participant__name",
        "participant__username"
    )

    def joined_stream(self, obj):
        return obj.joined_group

    joined_stream.boolean = True


@admin.register(models.DyteParticipantOnlineLog)
class DyteParticipantOnlineLogAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "dyte_meeting_participant",
        "online_at",
        "offline_at",
        "is_offline",
        "online_time"
    )
    raw_id_fields = ("dyte_meeting_participant", )
    list_filter = (
        "is_offline",
        AutocompleteFilterFactory("Dyte Meeting Participant", "dyte_meeting_participant"),
    )


@admin.register(models.DyteMeetingRecording)
class DyteMeetingRecordingAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "dyte_meeting",
        "status",
        "recording_id",
        "object_url",
        "started_at",
        "stopped_at"
    )
    raw_id_fields = ("dyte_meeting", )
    exclude = ("created_at", "deleted_at", "updated_at", "is_deleted")
    list_filter = (
        AutocompleteFilterFactory("Group", "dyte_meeting__group"),
        "status"
    )
    search_fields = (
        "recording_id",
        "dyte_meeting__group__host__name"
    )

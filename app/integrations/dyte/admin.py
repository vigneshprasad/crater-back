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
    exclude = ("created_at", "deleted_at", "updated_at", "is_deleted")
    list_filter = (
        "group",
        "group__start"
    )
    search_fields = (
        "meeting_id",
        "group_id",
        "meeting__participants__name",
        "meeting__participants__username",
        "group__host__name",
        "group__host__username",
        "group__speakers__name",
        "group__speakers__username",
        "group__attendees__name",
        "group__attendees__username",
    )


@admin.register(models.DyteMeetingParticipant)
class DyteMeetingParticipantAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "is_online",
        "participant",
        "dyte_meeting"
    )
    exclude = ("created_at", "deleted_at", "updated_at", "is_deleted")
    list_filter = (
        "is_online",
        "dyte_meeting__group",
        "dyte_meeting__group__start"
    )
    search_fields = (
        "participant__name",
        "participant__username"
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
    exclude = ("created_at", "deleted_at", "updated_at", "is_deleted")
    list_filter = (
        "dyte_meeting__group",
        "dyte_meeting__group__start",
        "status"
    )
    search_fields = (
        "recording_id",
        "dyte_meeting__group__host__name"
    )

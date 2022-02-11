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
        "group",
        "group__start"
    )
    search_fields = (
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
        "joined_stream",
        "last_online_at",
        "dyte_meeting"
    )
    raw_id_fields = ("participant", "dyte_meeting")
    exclude = ("auth_token", "created_at", "deleted_at", "updated_at", "is_deleted")
    list_filter = (
        "is_online",
        "dyte_meeting__group",
        "dyte_meeting__group__start"
    )
    search_fields = (
        "participant__name",
        "participant__username"
    )

    def joined_stream(self, obj):
        return obj.joined_group

    joined_stream.boolean = True


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
        "dyte_meeting__group",
        "status"
    )
    search_fields = (
        "recording_id",
        "dyte_meeting__group__host__name"
    )

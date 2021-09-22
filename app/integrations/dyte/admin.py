from django.contrib import admin

from integrations.dyte import models


@admin.register(models.DyteMeeting)
class DyteMeetingAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "dyte_meeting_id",
        "room_name",
        "meeting",
        "group"
    )
    exclude = ("created_at", "deleted_at", "updated_at", "is_deleted")
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
        "participant",
        "dyte_meeting",
        # "dyte_group",
        # "dyte_meeting",
        "is_online"
    )
    exclude = ("created_at", "deleted_at", "updated_at", "is_deleted")
    search_fields = (
        "participant__name",
        "participant__username"
    )

    @staticmethod
    def get_dyte_group(obj):
        return obj.dyte.group

    @staticmethod
    def get_dyte_meeting(obj):
        return obj.dyte.meeting

from django.contrib.admin import ModelAdmin, register

from resources.meetings import models


@register(models.Interest)
class MeetingInterestAdmin(ModelAdmin):
    list_display = ("id", "name", "is_active")
    exclude = ("created_at", "deleted_at", "updated_at", "is_deleted")


@register(models.Objective)
class MeetingObjectiveAdmin(ModelAdmin):
    list_display = ("id", "name", "type", "is_active")
    exclude = ("created_at", "deleted_at", "updated_at", "is_deleted")


@register(models.TimeSlot)
class TimeSlotAdmin(ModelAdmin):
    exclude = ("created_at", "deleted_at", "updated_at", "is_deleted")


@register(models.Config)
class MeetingConfigAdmin(ModelAdmin):
    list_display = (
        "id",
        "is_active",
        "is_registration_open",
        "registration_start_date",
        "registration_end_date",
        "week_start_date",
        "week_end_date",
        "type"
    )
    exclude = ("created_at", "deleted_at", "updated_at", "is_deleted")


@register(models.MeetingPreference)
class MeetingPreferenceAdmin(ModelAdmin):
    list_display = (
        "id",
        "user",
        "meeting_id",
        "topic",
        "user_objectives",
        "user_interests",
        "user_time_slots"
    )
    search_fields = ("user__email", )
    list_filter = ("meeting", )
    exclude = ("deleted_at", "updated_at", "is_deleted", "created_at")

    @staticmethod
    def monthly_meetings(obj):
        return obj.number_of_meetings_per_month

    @staticmethod
    def user_interests(obj):
        interests = obj.interests.all()
        if not interests:
            return "No Interest Selected"
        return [interest.name for interest in interests]

    @staticmethod
    def user_objectives(obj):
        objectives = obj.objectives.all()
        if not objectives:
            return "No objectives Selected"
        return [objective.name for objective in objectives]

    @staticmethod
    def user_time_slots(obj):
        time_slots = obj.time_slots.all()
        if not time_slots:
            return "No Time Slots Selected."
        return [
            "{} {}".format(time_slot.get_display_day(), time_slot.get_display_start_time())
            for time_slot in time_slots
        ]


@register(models.Meeting)
class MeetingAdmin(ModelAdmin):
    list_display = ("id", "meeting_participants", "start", "status")
    search_fields = ("participants__email", "start", "participants__phone_number")
    date_hierarchy = "start"
    list_filter = ("status", "config", "start")
    exclude = ("created_at", "deleted_at", "updated_at", "is_deleted", "is_canceled")

    @staticmethod
    def meeting_participants(obj):
        users = obj.participants.all()
        if not users:
            return "No users added"
        return ", ".join([user.email for user in users])


@register(models.MeetingRSVP)
class MeetingRSVPAdmin(ModelAdmin):
    list_display = ("id", "meeting", "participant", "status")
    exclude = ("created_at", "deleted_at", "updated_at", "is_deleted")
    search_fields = ["participant__email"]
    list_filter = ("status", "created_at")


@register(models.RescheduleRequest)
class RescheduleRequestAdmin(ModelAdmin):
    list_display = (
        "id",
        "requested_by",
        "approver",
        "old_meeting",
        "status",
        "new_meeting"
    )
    exclude = ("created_at", "deleted_at", "updated_at", "is_deleted")


@register(models.MeetingRequest)
class MeetingRequestAdmin(ModelAdmin):
    list_display = (
        "id",
        "requested_by",
        "requested_to",
        "time_slots",
        "selected_time_slot",
        "status",
        "created_at"
    )
    raw_id_fields = ("requested_by", "requested_to", )
    exclude = ("deleted_at", "updated_at", "is_deleted")

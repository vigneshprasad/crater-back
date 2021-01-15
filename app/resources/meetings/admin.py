from django.contrib.admin import ModelAdmin, register

from resources.meetings import models


@register(models.Interest)
class MeetingInterestAdmin(ModelAdmin):
    list_display = ('id', 'name', 'is_active')
    exclude = ('created_at', 'deleted_at', 'updated_at', 'is_deleted')


@register(models.Objective)
class MeetingObjectiveAdmin(ModelAdmin):
    list_display = ('id', 'name', 'type', 'is_active')
    exclude = ('created_at', 'deleted_at', 'updated_at', 'is_deleted')


@register(models.TimeSlot)
class TimeSlotAdmin(ModelAdmin):
    exclude = ('created_at', 'deleted_at', 'updated_at', 'is_deleted')


@register(models.Config)
class MeetingConfigAdmin(ModelAdmin):
    list_display = (
        'id',
        'is_active',
        'is_registration_open',
        'registration_start_date',
        'registration_end_date',
        'week_start_date',
        'week_end_date',
        'type'
    )
    exclude = ('created_at', 'deleted_at', 'updated_at', 'is_deleted')


@register(models.MeetingPreference)
class MeetingPreference(ModelAdmin):
    list_display = (
        'id',
        'user',
        'number_of_meetings',
        'monthly_meetings',
        'meeting_id',
        'user_objectives',
        'user_interests',
        'user_time_slots',
        'user_campaign',
    )
    search_fields = ('user__email', )
    list_filter = ('meeting', )
    exclude = ('deleted_at', 'updated_at', 'is_deleted', 'created_at')

    @staticmethod
    def user_campaign(obj):
        return obj.user.source

    @staticmethod
    def monthly_meetings(obj):
        return obj.number_of_meetings_per_month

    @staticmethod
    def user_interests(obj):
        interests = obj.interests.all()
        if not interests:
            return 'No Interest Selected'
        return [interest.name for interest in interests]

    @staticmethod
    def user_objectives(obj):
        objectives = obj.objectives.all()
        if not objectives:
            return 'No objectives Selected'
        return [objective.name for objective in objectives]

    @staticmethod
    def user_time_slots(obj):
        time_slots = obj.time_slots.all()
        if not time_slots:
            return "No Time Slots Selected."
        return [time_slot.get_display_time() for time_slot in time_slots]


@register(models.Meeting)
class Meeting(ModelAdmin):
    list_display = ('id', 'meeting_participants', 'start', 'status')
    search_fields = ('participants__email', 'start', 'participants__phone_number')
    list_filter = ('status', 'start')
    exclude = ('created_at', 'deleted_at', 'updated_at', 'is_deleted', 'is_canceled')

    @staticmethod
    def meeting_participants(obj):
        users = obj.participants.all()
        if not users:
            return 'No users added'
        return ', '.join([user.email for user in users])


@register(models.MeetingRSVP)
class MeetingRsvp(ModelAdmin):
    list_display = ('id', 'meeting', 'participant', 'status')
    exclude = ('created_at', 'deleted_at', 'updated_at', 'is_deleted')
    search_fields = ['participant__email']
    list_filter = ('status', 'created_at')


@register(models.RescheduleRequest)
class RescheduleRequests(ModelAdmin):
    list_display = (
        'id',
        'requested_by',
        'approver',
        'old_meeting',
        'status',
        'new_meeting'
    )
    exclude = ('created_at', 'deleted_at', 'updated_at', 'is_deleted')

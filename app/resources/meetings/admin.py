from django.contrib.admin import ModelAdmin, register

from resources.meetings import models


@register(models.Interest)
class MeetingInterestAdmin(ModelAdmin):
    exclude = ('created_at', 'deleted_at', 'updated_at', 'is_deleted')


@register(models.Objective)
class MeetingObjectiveAdmin(ModelAdmin):
    exclude = ('created_at', 'deleted_at', 'updated_at', 'is_deleted')


@register(models.TimeSlot)
class TimeSlotAdmin(ModelAdmin):
    exclude = ('created_at', 'deleted_at', 'updated_at', 'is_deleted')


@register(models.MeetingTimeSlot)
class MeetingTimeSlotAdmin(ModelAdmin):
    exclude = ('created_at', 'deleted_at', 'updated_at', 'is_deleted')


@register(models.MeetingConfig)
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


@register(models.UserMeetingPreference)
class UserMeetingPreference(ModelAdmin):
    list_display = ('id', 'user', 'number_of_meetings', 'meeting', 'user_interests', 'user_time_slots')
    exclude = ('created_at', 'deleted_at', 'updated_at', 'is_deleted')

    @staticmethod
    def user_interests(obj):
        interests = obj.interests.all()
        if not interests:
            return 'No Interest Selected'
        return [interest.name for interest in interests]

    @staticmethod
    def user_time_slots(obj):
        time_slots = obj.time_slots.all()
        if not time_slots:
            return "No Time Slots Selected."
        return [time_slot.get_display_time() for time_slot in time_slots]


@register(models.Meeting)
class Meeting(ModelAdmin):
    list_display = ('id', 'meeting_participants', 'time_slot', 'is_canceled')
    search_fields = ('participants__email', )
    list_filter = ('is_canceled', 'time_slot__start_time')
    exclude = ('created_at', 'deleted_at', 'updated_at', 'is_deleted')

    @staticmethod
    def meeting_participants(obj):
        users = obj.participants.all()
        if not users:
            return 'No users added'
        return ', '.join([user.email for user in users])

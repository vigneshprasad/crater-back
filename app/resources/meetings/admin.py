from django.contrib.admin import ModelAdmin, register, TabularInline, DateFieldListFilter

from resources.meetings import models
from base import admin as base_admin


@register(models.TimeSlot)
class TimeSlotAdmin(ModelAdmin):
    exclude = ('created_at', 'deleted_at', 'updated_at', 'is_deleted')


@register(models.Meeting)
class MeetingAdmin(ModelAdmin):
    exclude = ('created_at', 'deleted_at', 'updated_at', 'is_deleted')


@register(models.UserMeetingPreference)
class UserMeetingPreference(ModelAdmin):
    exclude = ('created_at', 'deleted_at', 'updated_at', 'is_deleted')

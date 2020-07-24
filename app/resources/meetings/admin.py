from django.contrib.admin import ModelAdmin, register, TabularInline, DateFieldListFilter

from resources.meetings import models
from resources.meetings import forms


@register(models.TimeSlot)
class TimeSlotAdmin(ModelAdmin):
    exclude = ('created_at', 'deleted_at', 'updated_at', 'is_deleted')
    pass


@register(models.Meeting)
class MeetingAdmin(ModelAdmin):
    exclude = ('created_at', 'deleted_at', 'updated_at', 'is_deleted')
    pass

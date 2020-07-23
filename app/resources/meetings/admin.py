from django.contrib.admin import ModelAdmin, register, TabularInline, DateFieldListFilter

from resources.meetings import models
from resources.meetings import forms


@register(models.TimeSlot)
class TimeSlotAdmin(ModelAdmin):
    pass


@register(models.Meeting)
class MeetingAdmin(ModelAdmin):
    pass

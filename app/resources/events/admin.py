from django.contrib.admin import ModelAdmin, register

from resources.events.models import Event


@register(Event)
class EventAdmin(ModelAdmin):
    icon_name = 'event'
    list_display = ('title', 'date', 'start', 'end', 'state')
    list_editable = ('date', 'start', 'end')
    readonly_fields = ('state',)

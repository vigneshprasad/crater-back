from django.contrib.admin import ModelAdmin, register, TabularInline, DateFieldListFilter
from django.utils.translation import ugettext_lazy as _

from resources.events.forms import EventForm
from resources.events.models import Event, RSVPD
from utils.mixins import ViewActionMixin


class RSVPDAdmin(TabularInline):
    model = RSVPD
    extra = 0
    readonly_fields = ('name', 'email')
    fields = ('name', 'email')

    def name(self, rsvpd):
        return rsvpd.user.name

    def email(self, rsvpd):
        return rsvpd.user.email

    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@register(Event)
class EventAdmin(ViewActionMixin, ModelAdmin):
    icon_name = 'event'
    form = EventForm
    list_display = ('title', 'date', 'start_time', 'end_time', 'state', 'action')
    list_filter = ('state', ('date', DateFieldListFilter))
    search_fields = ('title',)
    readonly_fields = ('state',)
    inlines = [RSVPDAdmin]

    def start_time(self, event):
        return event.start.strftime('%H:%M:%S')
    start_time.short_description = _('Start Time')

    def end_time(self, event):
        return event.end.strftime('%H:%M:%S')
    end_time.short_description = _('End Time')

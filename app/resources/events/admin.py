from django.contrib.admin import ModelAdmin, register, TabularInline, DateFieldListFilter
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
    list_display = ('title', 'date', 'start', 'end', 'state', 'action')
    list_filter = ('state', ('date', DateFieldListFilter))
    search_fields = ('title',)
    readonly_fields = ('state',)
    inlines = [RSVPDAdmin]

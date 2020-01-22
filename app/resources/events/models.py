from datetime import datetime

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import ugettext_lazy as _
from timezone_field import TimeZoneField

from locations.models import City
from resources.events.choices import EVENT_STATE
from tags.models import EventTag


class Event(models.Model):
    """
    Resources events created by admins
    """
    title = models.CharField(_('Title'), max_length=255)
    text = models.TextField(_('Text'))
    picture = models.ImageField(_('Cover photo'), upload_to='events/%Y/%m/%d', null=True)
    date = models.DateField(_('Date'))
    start = models.TimeField(_('Start Time'))
    end = models.TimeField(_('End Time'))
    is_free = models.BooleanField(_('Free'))
    is_rsvp = models.BooleanField(_('RSVP Required'))
    location = models.ForeignKey(City, on_delete=models.CASCADE, related_name='events')
    capacity = models.PositiveIntegerField(_('Venue capacity'), null=True)
    state = models.CharField(_('State'), choices=EVENT_STATE, default='upcoming', max_length=16)
    timezone = TimeZoneField(default='Asia/Kolkata')
    tag = models.ForeignKey(
        EventTag,
        verbose_name=_('Event Tag'),
        on_delete=models.CASCADE,
        related_name='events',
        null=True
    )

    def clean(self):
        if self.start and self.end and self.start >= self.end:
            raise ValidationError({'end': _('Should be later than the "Start Time"')})
        start_datetime = datetime.combine(self.date, self.start)
        if start_datetime < datetime.now():
            raise ValidationError({'start': _('Event can\'t be in past')})

    class Meta:
        verbose_name = _('Event')
        verbose_name_plural = _('Events')
        db_table = 'resources_events'
        ordering = ('-date', '-start')

    def __str__(self):
        return self.title


class RSVPD(models.Model):
    """
    Reply for invitation, subscription for an event
    """
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='participants')
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, related_name='user_participants')

    class Meta:
        verbose_name = _('Participant')
        verbose_name_plural = _('Participants')
        db_table = 'resources_participants'
        unique_together = ['event', 'user']

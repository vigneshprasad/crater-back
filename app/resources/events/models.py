from datetime import datetime

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.translation import ugettext_lazy as _
from model_utils.models import TimeStampedModel

from locations.models import City
from notifications.models import Notification, UserNotification
from resources.events.choices import EVENT_STATE
from tags.models import EventTag
from users.models import User


class Event(TimeStampedModel):
    """
    Resources events created by admins
    """
    title = models.CharField(_('Title'), max_length=255)
    address = models.CharField(_('Event Address'), max_length=255)
    text = models.TextField(_('Text'))
    picture = models.ImageField(_('Cover photo'), upload_to='events/%Y/%m/%d', null=True)
    date = models.DateField(_('Date'))
    start = models.TimeField(_('Start Time'))
    end = models.TimeField(_('End Time'))
    is_free = models.BooleanField(_('Free'))
    is_rsvp_required = models.BooleanField(_('RSVP Required'))
    location = models.ForeignKey(City, on_delete=models.CASCADE, related_name='events')
    capacity = models.PositiveIntegerField(_('Venue capacity'), null=True)
    state = models.CharField(_('State'), choices=EVENT_STATE, default='upcoming', max_length=16)
    tag = models.ForeignKey(
        EventTag,
        verbose_name=_('Event Tag'),
        on_delete=models.CASCADE,
        related_name='events',
        null=True
    )

    def clean(self):
        error_message_past_event = _('Event can\'t be in past')
        if self.start and self.end and self.start >= self.end:
            raise ValidationError({'end': _('Should be later than the "Start Time"')})
        if self.date and self.start:
            start_datetime = datetime.combine(self.date, self.start)
            if start_datetime < datetime.now():
                if start_datetime.date() == datetime.now().date():
                    raise ValidationError({'start': error_message_past_event})
                raise ValidationError({'date': error_message_past_event})

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


@receiver(post_save, sender=Event)
def event_post_save(sender, instance,  created, *args, **kwargs):
    if created:
        notification = Notification.objects.create(event=instance)
        users = User.objects.filter(profile__isnull=False)
        for user in users:
            UserNotification.objects.create(user=user, notification=notification)

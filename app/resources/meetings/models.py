from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import ugettext_lazy as _

from base import models as base_model
from resources.meetings import choices


class TimeSlot(base_model.BaseModel):
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()

    def clean(self):
        if self.start_time >= self.end_time:
            raise ValidationError({'end': _('Start time should be lesser than End time.')})

    def __str__(self):
        return '{}-{}'.format(self.start_time, self.end_time)


class Meeting(base_model.BaseModel):
    """
    Resources meetings created by admins

    """
    title = models.CharField(_('Title'), max_length=255)
    # Week the meeting is for.
    week_start_date = models.DateField(_('Week Start Date'), null=True, blank=False)
    week_end_date = models.DateField(_('Week End Date'), null=True, blank=False)
    # Registration details for the meeting. Only during this time period can a
    # user register for the meeting.
    registration_start_date = models.DateField(_('Registration Start Date'), null=True, blank=False)
    registration_end_date = models.DateField(_('Registration End Date'), null=True, blank=False)
    is_registration_open = models.BooleanField(_('Registration Open'), default=True)

    is_active = models.BooleanField(_('Active Meeting'), default=True)
    available_time_slots = models.ManyToManyField(
        TimeSlot,
        verbose_name=_('Available Slots'),
        related_name='meetings',
    )

    def clean(self):
        # Check is end date is greater than start date.
        if self.week_start_date >= self.week_end_date:
            raise ValidationError('Week start should be lesser than Week end.')

        # TODO: Add a validation for meeting in the same duration.

    def close_meeting(self):
        self.is_registration_open = False
        self.is_active = False
        self.save()

    def close_registration(self):
        self.is_registration_open = False
        self.save()


class UserMeetingPreference(base_model.BaseModel):
    """
    Resources meetings created by admins

    """
    user = models.ForeignKey(
        'users.User',
        verbose_name=_('User'),
        on_delete=models.CASCADE,
        related_name='meeting_preferences'
    )
    meeting = models.ForeignKey(
        Meeting,
        verbose_name=_('Meetings'),
        on_delete=models.CASCADE,
        related_name='user_preferences'
    )
    number_of_meetings = models.PositiveIntegerField(default=1)
    objective = models.CharField(max_length=255, choices=choices.OBJECTIVE_CHOICES)
    interests = models.ManyToManyField(
        'tags.Interests',
        verbose_name=_('Interests'),
    )
    time_slots = models.ManyToManyField(
        TimeSlot,
        verbose_name=_('Time Slots'),
    )

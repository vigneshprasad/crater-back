import datetime

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

    def get_display(self):
        """
        This is the display state for a time slot.

        Args:
            self(TimeSlot)

        return:
            str: String display for the time slot.
                ex. "Friday, 31 July - 08:00 PM - 08:30 PM"

        """
        display_time = self.get_display_time()
        display_date = self.get_display_day()

        return '{} - {}'.format(display_date, display_time)

    def get_display_day(self):
        return '{}, {} {}'.format(
            self.date.strftime('%A'),
            str(self.date.day),
            self.date.strftime('%B')
        )

    def get_display_time(self, join="to"):
        return '{} {} {}'.format(self.get_display_start_time(), join ,self.get_display_end_time())

    def get_display_start_time(self):
        start_time = datetime.datetime.strptime(str(self.start_time), "%H:%M:%S")
        return start_time.strftime("%I:%M %p")

    def get_display_end_time(self):
        end_time = datetime.datetime.strptime(str(self.end_time), "%H:%M:%S")
        return end_time.strftime("%I:%M %p")

    def __str__(self):
        return self.get_display()


class MeetingTimeSlot(base_model.BaseModel):
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()

    def clean(self):
        if self.start_time >= self.end_time:
            raise ValidationError({'end': _('Start time should be lesser than End time.')})

    def get_display(self):
        """
        This is the display state for a time slot.

        Args:
            self(TimeSlot)

        return:
            str: String display for the time slot.
                ex. "Friday, 31 July - 08:00 PM - 08:30 PM"

        """
        display_time = self.get_display_time()
        display_date = self.get_display_day()

        return '{} - {}'.format(display_date, display_time)

    def get_display_day(self):
        return '{}, {} {}'.format(
            self.date.strftime('%A'),
            str(self.date.day),
            self.date.strftime('%B')
        )

    def get_display_time(self):
        start_time = datetime.datetime.strptime(str(self.start_time), "%H:%M:%S")
        end_time = datetime.datetime.strptime(str(self.end_time), "%H:%M:%S")

        display_start_time = start_time.strftime("%I:%M %p")
        display_end_time = end_time.strftime("%I:%M %p")

        return '{} to {}'.format(display_start_time, display_end_time)

    def __str__(self):
        return self.get_display()


class MeetingConfig(base_model.BaseModel):
    """
    Resources meeting config created by admins

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
        related_name='meeting_configs',
    )
    type = models.CharField(
        max_length=64,
        default=choices.MEETING_CHOICE_1_ON_1,
        choices=choices.MEETING_TYPE_CHOICES
    )

    def __str__(self):
        return 'Meeting Config {} ({} - {})'.format(
            self.pk,
            self.get_display_week_start_date(),
            self.get_display_week_end_date()
        )

    def get_display_week_start_date(self):
        return '{}, {} {}, {}'.format(
            self.week_start_date.strftime('%A'),
            str(self.week_start_date.day),
            self.week_end_date.strftime('%B'),
            self.week_start_date.year
        )

    def get_display_week_end_date(self):
        return '{}, {} {}, {}'.format(
            self.week_end_date.strftime('%A'),
            str(self.week_end_date.day),
            self.week_end_date.strftime('%B'),
            self.week_end_date.year
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
    User meeting preference as selected by user
    for a meeting config.

    """
    user = models.ForeignKey(
        'users.User',
        verbose_name=_('User'),
        on_delete=models.CASCADE,
        related_name='meeting_preferences'
    )
    meeting = models.ForeignKey(
        MeetingConfig,
        verbose_name=_('Meeting Config'),
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


class Meeting(base_model.BaseModel):
    meeting_config = models.ForeignKey(
        MeetingConfig,
        verbose_name=_('Meeting Config'),
        on_delete=models.CASCADE,
        related_name='meetings'
    )
    organiser = models.ForeignKey(
        'users.User',
        verbose_name=_('Organiser'),
        on_delete=models.CASCADE,
        related_name='meetings',
        null=True,
        blank=True
    )
    participants = models.ManyToManyField(
        'users.User',
        verbose_name=_('Participants'),
    )
    link = models.URLField(null=True, blank=True)
    time_slot = models.ForeignKey(
        'meetings.MeetingTimeSlot',
        verbose_name=_('Meeting Time Slot'),
        on_delete=models.CASCADE,
        related_name='meetings'
    )
    is_canceled = models.BooleanField(
        default=False,
        verbose_name=_('Canceled')
    )

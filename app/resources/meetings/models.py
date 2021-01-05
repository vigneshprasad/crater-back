import datetime

import pytz
from django.conf import settings
from django.contrib.postgres.fields import ArrayField
from django.core import exceptions
from django.db import models
from django.contrib.auth import get_user_model
from django.utils.translation import ugettext_lazy as _

from base import models as base_model
from resources.meetings import choices


class Interest(base_model.BaseModel):
    """
    Interest for a user who opt in for a meeting.

    Note:
        These interests are used for matching user's
        within themselves.

    """
    name = models.CharField(max_length=255)
    icon = models.FileField(blank=True, null=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        # TODO(Nishant): Rename it to Meeting Interest
        verbose_name = _('User Meeting Interest')
        verbose_name_plural = _('User Meeting Interests')
        ordering = ['name']

    def __str__(self):
        return self.name


class Objective(base_model.BaseModel):
    """
    Objective for a user who wants to do meetings
    on the platform.


    Note:
        This is different from platform wide objectives.

    """
    name = models.CharField(max_length=255)
    icon = models.FileField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    type = models.CharField(
        max_length=255,
        choices=choices.OBJECTIVE_TYPES,
        default=choices.OBJECTIVE_TYPES[0][0],
    )

    def __str__(self):
        return self.name

    class Meta:
        # TODO(Nishant): Rename it to Meeting Objective
        verbose_name = _('User Meeting Objective')
        verbose_name_plural = _('User Meeting Objectives')
        ordering = ['name']


class TimeSlot(base_model.BaseModel):
    """
    Time Slots are only used for display. They define
    the range of Meeting Time Slots available for selection.

    TODO(Nishant): Create task for deleting old objects.

    """
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    # Will use DateTimeFields going forward instead of
    # date, start_time and end_time.
    start = models.DateTimeField(
        null=True,
        blank=True
    )
    end = models.DateTimeField(
        null=True,
        blank=True
    )

    def clean(self):
        if self.start_time >= self.end_time:
            raise exceptions.ValidationError({'end': _('Start time should be lesser than End time.')})

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
        return '{} {} {}'.format(self.get_display_start_time(), join, self.get_display_end_time())

    def get_display_start_time(self):
        start_time = datetime.datetime.strptime(str(self.start_time), "%H:%M:%S")
        return start_time.strftime("%I:%M %p")

    def get_display_end_time(self):
        end_time = datetime.datetime.strptime(str(self.end_time), "%H:%M:%S")
        return end_time.strftime("%I:%M %p")

    def __str__(self):
        return self.get_display()


class MeetingTimeSlot(base_model.BaseModel):
    """
    Meeting Time Slots are one time use time slots
    for meetings only.

    Note:
        These objects are created while creating
        meeting for users and are deleted after that.

    """
    # TODO(Nishant): Deprecate this model.

    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()

    def clean(self):
        if self.start_time >= self.end_time:
            raise exceptions.ValidationError({'end': _('Start time should be lesser than End time.')})

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
        """Give the date in a display format.

        Example:
            Thursday, 3 September.

        """
        return '{}, {} {}'.format(
            self.date.strftime('%A'),
            str(self.date.day),
            self.date.strftime('%B')
        )

    def get_display_time(self, join="to"):
        return '{} {} {}'.format(self.get_display_start_time(), join, self.get_display_end_time())

    def get_display_start_time(self):
        start_time = datetime.datetime.strptime(str(self.start_time), "%H:%M:%S")
        return start_time.strftime("%I:%M %p")

    def get_display_end_time(self):
        end_time = datetime.datetime.strptime(str(self.end_time), "%H:%M:%S")
        return end_time.strftime("%I:%M %p")

    def __str__(self):
        return self.get_display()


class Config(base_model.BaseModel):
    """
    Resources meeting config created by admins.

    Note:
        This consists of all details for a meeting
        user's can opt in for at a given time.

    """
    # Title is not being used right now. But can be used in
    # any way in the future.
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
    # Only used for display purposes. The actual time slots being
    # assigned to a meeting are different.
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
        return '{} - {} to {}'.format(
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
        if not self.week_start_date:
            raise exceptions.ValidationError('Week start date is required.')
        if not self.week_end_date:
            raise exceptions.ValidationError('Week end date is required.')

        if self.week_start_date >= self.week_end_date:
            raise exceptions.ValidationError('Week start should be lesser than week end.')

    def close_meeting(self):
        self.is_registration_open = False
        self.is_active = False
        self.save()

    def close_registration(self):
        self.is_registration_open = False
        self.save()


class MeetingPreference(base_model.BaseModel):
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
    # Should denote the latest meeting_config the user
    # has opted in for.
    # TODO(Abhishek): Rename to config after users on old app upgrade to new version
    meeting = models.ForeignKey(
        Config,
        verbose_name=_('Meeting Config'),
        on_delete=models.CASCADE,
        related_name='user_preferences'
    )
    number_of_meetings_per_month = models.PositiveIntegerField(default=2)
    number_of_meetings = models.PositiveIntegerField(default=1)
    # Only one objective can be selected for a each weeks meeting.
    objective = models.CharField(
        max_length=255,
        choices=choices.OBJECTIVE_CHOICES,
        null=True,
        blank=True
    )
    objectives = models.ManyToManyField(
        Objective,
        verbose_name=_('Meeting Objective'),
        blank=True
    )
    interests = models.ManyToManyField(
        Interest,
        verbose_name=_('Meeting Interests'),
    )
    time_slots = models.ManyToManyField(
        TimeSlot,
        verbose_name=_('Time Slots'),
    )

    class Meta:
        ordering = ['-created_at']


class Meeting(base_model.BaseModel):
    config = models.ForeignKey(
        Config,
        verbose_name=_('Meeting Config'),
        on_delete=models.CASCADE,
        related_name='meetings'
    )
    participants = models.ManyToManyField(
        'users.User',
        verbose_name=_('Participants'),
    )
    link = models.URLField(null=True, blank=True)
    # TODO(Nishant): Remove once we completely start using start and end.
    time_slot = models.ForeignKey(
        'meetings.MeetingTimeSlot',
        verbose_name=_('Meeting Time Slot'),
        on_delete=models.CASCADE,
        related_name='meetings'
    )
    start = models.DateTimeField(
        verbose_name=_('Meeting Start Time'),
        null=True,
        blank=True
    )
    end = models.DateTimeField(
        verbose_name=_('Meeting End Time'),
        null=True,
        blank=True
    )
    is_canceled = models.BooleanField(
        default=False,
        verbose_name=_('Canceled')
    )
    status = models.CharField(
        verbose_name=_('Meeting Status'),
        choices=choices.MEETING_STATUS_CHOICES,
        default=choices.MEETING_STATUS_PENDING,
        max_length=32,
    )

    def __init__(self, *args, **kwargs):
        super(Meeting, self).__init__(*args, **kwargs)
        self.__previous_status = self.status

    def __str__(self):
        member_str = " - ".join((self.participants.all().values_list("email", flat=True)))
        # Getting the time_str from start or time_slot.
        if self.start:
            time_str = self.start.strftime("%A %d, %b %I:%M %p")
        else:
            time_str = self.time_slot.get_display()
        return "{} @ {}".format(member_str, time_str)




    @property
    def local_start(self):
        """Return start in the local timezone."""
        return self.start.astimezone(pytz.timezone(settings.TIME_ZONE))

    @property
    def local_end(self):
        """Return start in the local timezone."""
        return self.end.astimezone(pytz.timezone(settings.TIME_ZONE))

    def get_display(self):
        """This is the display date time for a Meeting.
            ex. "Friday, 31 July - 08:00 PM - 08:30 PM"

        """
        display_time = self.get_display_time()
        display_date = self.get_display_day()
        return '{} @ {}'.format(display_date, display_time)

    def get_display_day(self):
        """Give a displayable date for a Meeting.

        Note:
            This is generally used for communication.

        """
        return self.start.strftime("%A, %d %B")

    def get_display_time(self,):
        """Give a displayable time (start plus end) for a Meeting.

        Note:
            This is generally used for communication.

        """
        return '{} - {}'.format(self.get_display_start_time(), self.get_display_end_time())

    def get_display_start_time(self):
        """Give a displayable start time for a Meeting.

        Note:
            This is generally used for communication.

        """
        return self.local_start.strftime("%I:%M %p")

    def get_display_end_time(self):
        """Give a displayable end time for a Meeting.

        Note:
            This is generally used for communication.

        """
        return self.local_end.strftime("%I:%M %p")


class MeetingRSVP(base_model.BaseModel):
    """
    Meeting RSVP for a user for a specific meeting

    """
    meeting = models.ForeignKey(
        'meetings.Meeting',
        verbose_name=_('Meeting'),
        related_name='rsvps',
        on_delete=models.CASCADE,
    )
    participant = models.ForeignKey(
        get_user_model(),
        verbose_name=_('Meeting Participant'),
        related_name='meeting_rsvps',
        on_delete=models.CASCADE,
    )
    status = models.CharField(
        max_length=255,
        verbose_name=_("Status"),
        choices=choices.MEETING_RSVP_STATUS_CHOICES,
        default=choices.MEETING_RSVP_STATUS_CHOICES[1][0],
    )

    class Meta:
        unique_together = ['meeting', 'participant']


class RescheduleRequest(base_model.BaseModel):
    old_meeting = models.ForeignKey(
        Meeting,
        verbose_name=_('Old Meeting'),
        related_name='reschedule_requests',
        on_delete=models.CASCADE,
    )
    new_meeting = models.ForeignKey(
        Meeting,
        null=True,
        blank=True,
        verbose_name=_('New Meeting'),
        related_name='rescheduled_from',
        on_delete=models.CASCADE
    )
    requested_by = models.ForeignKey(
        get_user_model(),
        verbose_name=_('Request By'),
        related_name='reschedule_requests',
        on_delete=models.CASCADE
    )
    approver = models.ForeignKey(
        get_user_model(),
        verbose_name=_('Approver'),
        related_name='reschedule_approvals',
        on_delete=models.CASCADE
    )
    time_slots = ArrayField(
        models.DateTimeField(null=True, blank=True),
        size=3
    )
    status = models.CharField(
        max_length=32,
        default=choices.RESCHEDULE_REQUEST_PENDING_APPROVAL,
        choices=choices.RESCHEDULE_REQUEST_STATUSES
    )

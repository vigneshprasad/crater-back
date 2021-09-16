import datetime

import pytz

from datetime import timedelta

from django.db import models
from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils.translation import ugettext_lazy as _

from base import models as base_model
from conversations import constants
from resources.meetings import models as meeting_models


class SuggestedTopic(base_model.BaseModel):

    GROUP_TYPE_CHOICES = (
        (constants.GROUP_TYPE_GENERIC_ENUM, constants.GROUP_TYPE_GENERIC),
        (constants.GROUP_TYPE_AMA_ENUM, constants.GROUP_TYPE_AMA),
        (constants.GROUP_TYPE_WEBINAR_ENUM, constants.GROUP_TYPE_WEBINAR_ENUM),
    )

    type = models.PositiveIntegerField(
        default=constants.GROUP_TYPE_GENERIC_ENUM,
        choices=GROUP_TYPE_CHOICES,
    )
    name = models.CharField(max_length=255)
    suggested_by = models.ForeignKey(
        get_user_model(),
        related_name="suggested_topics",
        on_delete=models.CASCADE
    )
    is_approved = models.BooleanField(default=False)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = _("Suggested Topic")
        verbose_name_plural = _("Suggested Topics")

    def __str__(self):
        return "{}-{}".format(self.suggested_by, self.name)


class Topic(base_model.BaseModel):
    """Topic of discussion for a conversation.

    It has self-reference of the {parent} topic to create nesting.

    Example:
        (Topic) How to build a brand?, a topic (Topic)  Marketing can be parent
        to create nesting

    """

    GROUP_TYPE_CHOICES = (
        (constants.GROUP_TYPE_GENERIC_ENUM, constants.GROUP_TYPE_GENERIC),
        (constants.GROUP_TYPE_AMA_ENUM, constants.GROUP_TYPE_AMA),
        (constants.GROUP_TYPE_WEBINAR_ENUM, constants.GROUP_TYPE_WEBINAR)
    )

    type = models.PositiveIntegerField(
        default=constants.GROUP_TYPE_GENERIC_ENUM,
        choices=GROUP_TYPE_CHOICES,
    )
    name = models.CharField(max_length=255)
    image = models.ImageField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    parent = models.ForeignKey(
        "conversations.Topic",
        blank=True,
        null=True,
        on_delete=models.CASCADE
    )
    article = models.ForeignKey(
        "curated_articles.CuratedArticle",
        null=True,
        blank=True,
        on_delete=models.CASCADE
    )
    is_approved = models.BooleanField(default=True)
    description = models.TextField(max_length=255, null=True, blank=True)
    creator = models.ForeignKey(
        get_user_model(),
        on_delete=models.CASCADE,
        blank=True,
        null=True,
    )
    is_suggested = models.BooleanField(default=False)

    class Meta:
        ordering = ["name"]
        verbose_name = _("Topic")
        verbose_name_plural = _("Topics")

    def __str__(self):
        return "{}".format(self.name)


class Group(base_model.BaseModel):

    GROUP_PRIVACY_CHOICES = (
        (constants.GROUP_PRIVACY_PUBLIC_ENUM, constants.GROUP_PRIVACY_PUBLIC),
        (constants.GROUP_PRIVACY_PRIVATE_ENUM, constants.GROUP_PRIVACY_PRIVATE)
    )

    GROUP_MEDIUM_CHOICES = (
        (constants.GROUP_MEDIUM_AUDIO_ENUM, constants.GROUP_MEDIUM_AUDIO),
        (constants.GROUP_MEDIUM_AUDIO_VIDEO_ENUM, constants.GROUP_MEDIUM_AUDIO_VIDEO)
    )

    GROUP_TYPE_CHOICES = (
        (constants.GROUP_TYPE_GENERIC_ENUM, constants.GROUP_TYPE_GENERIC),
        (constants.GROUP_TYPE_AMA_ENUM, constants.GROUP_TYPE_AMA),
        (constants.GROUP_TYPE_WEBINAR_ENUM, constants.GROUP_TYPE_WEBINAR)
    )

    type = models.PositiveIntegerField(
        default=constants.GROUP_TYPE_GENERIC_ENUM,
        choices=GROUP_TYPE_CHOICES,
    )

    # The user who has setup the group.
    host = models.ForeignKey(
        get_user_model(),
        on_delete=models.CASCADE,
        related_name="groups_hosted",
        null=True,
        blank=True
    )
    # Who all can speak on the call.
    speakers = models.ManyToManyField(
        get_user_model(),
        verbose_name=_("Speakers"),
        related_name="groups_speaker"
    )
    # Attendees are users who can join the call but are not the
    # speakers on it i.e just listen/chat.
    attendees = models.ManyToManyField(
        get_user_model(),
        verbose_name=_("Attendees"),
        related_name="groups_attended",
        blank=True,
    )

    topic = models.ForeignKey("conversations.Topic", on_delete=models.CASCADE, related_name="group")
    # Description is populated from Topic.
    description = models.TextField(max_length=1024, null=True, blank=True)

    interests = models.ManyToManyField(meeting_models.Interest, verbose_name=_("Interests"))

    # Duration or start of the Group.
    start = models.DateTimeField()
    end = models.DateTimeField(null=True, blank=True)

    max_speakers = models.PositiveIntegerField(default=constants.DEFAULT_MAX_SPEAKERS)
    max_attendees = models.PositiveIntegerField(null=True, blank=True)

    privacy = models.IntegerField(choices=GROUP_PRIVACY_CHOICES, default=constants.GROUP_PRIVACY_PUBLIC_ENUM)
    medium = models.IntegerField(choices=GROUP_MEDIUM_CHOICES, default=constants.GROUP_MEDIUM_AUDIO_ENUM)

    is_full = models.BooleanField(default=False)
    is_live = models.BooleanField(default=False)

    # Group closed status and datetime of closure.
    # TODO(Nishant): Can change this into statuses as well.
    closed = models.BooleanField(default=False)
    closed_at = models.DateTimeField(null=True, blank=True)

    # Group score.
    calculate_score = models.BooleanField(default=True)
    score = models.FloatField(null=True, blank=True)

    # Approval status for groups. This controls if notifications go out,
    # group is visible in all conversations etc.
    is_approved = models.BooleanField(default=True)
    approved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = _("Group")
        verbose_name_plural = _("Groups")

    def __str__(self):
        return "{} - {} - {} - {}".format(self.pk, self.topic, self.host, self.type)

    def save(
            self,
            force_insert=False,
            force_update=False,
            using=None,
            update_fields=None
    ):
        if not self.end and not self.type == constants.GROUP_TYPE_WEBINAR_ENUM:
            self.end = self.start + timedelta(hours=1)

        return super(Group, self).save(force_insert, force_update, using, update_fields)

    def approve(self):
        self.is_approved = True
        self.approved_at = datetime.datetime.now()
        self.save()

    @property
    def local_start(self):
        """Return start in the local timezone."""
        return self.start.astimezone(pytz.timezone(settings.TIME_ZONE))

    @property
    def local_end(self):
        """Return start in the local timezone."""
        return self.end.astimezone(pytz.timezone(settings.TIME_ZONE)) if self.end else None

    def can_add_speakers(self):
        """Return True if speakers can be added to the group."""
        if self.speakers.count() > self.max_speakers:
            return False
        return True

    def get_display(self):
        """This is the display date time for a Group.
            ex. "Friday, 31 July - 08:00 PM - 08:30 PM"

        """
        display_time = self.get_display_time()
        display_date = self.get_display_day()
        return "{} @ {}".format(display_date, display_time)

    def get_display_day(self):
        """Give a displayable date for a Group.

        Note:
            This is generally used for communication.

        """
        return self.start.strftime("%A, %d %B")

    def get_display_time(self):
        """Give a displayable time (start plus end) for a Group.

        Note:
            This is generally used for communication.

        """
        display_end_time = self.get_display_end_time()
        display_start_time = self.get_display_start_time()

        if not display_end_time:
            return "{}".format(display_start_time)

        return "{} - {}".format(display_start_time, display_end_time)

    def get_display_start_time(self):
        """Give a displayable start time for a Group.

        Note:
            This is generally used for communication.

        """
        return self.local_start.strftime("%I:%M %p")

    def get_display_end_time(self):
        """Give a displayable end time for a Group.

        Note:
            This is generally used for communication.

        """
        return self.local_end.strftime("%I:%M %p") if self.local_end else None


class Invite(base_model.BaseModel):

    INVITE_STATUS_CHOICES = (
        (constants.INVITE_STATUS_PENDING_ENUM, constants.INVITE_STATUS_PENDING),
        (constants.INVITE_STATUS_ACCEPTED_ENUM, constants.INVITE_STATUS_ACCEPTED),
        (constants.INVITE_STATUS_DECLINED_ENUM, constants.INVITE_STATUS_DECLINED)
    )

    INVITE_TYPE_CHOICES = (
        (constants.INVITE_TYPE_SPEAKER, constants.INVITE_TYPE_SPEAKER),
        (constants.INVITE_TYPE_ATTENDEE_ENUM, constants.INVITE_TYPE_ATTENDEE)
    )

    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name="invites")
    inviter = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, related_name="group_invites_created")
    invitee = models.ForeignKey(
        get_user_model(),
        on_delete=models.CASCADE,
        related_name="groups_invites_received",
        null=True,
        blank=True
    )
    invitee_email = models.EmailField(max_length=128, null=True, blank=True)
    status = models.IntegerField(choices=INVITE_STATUS_CHOICES, default=constants.INVITE_STATUS_PENDING_ENUM)
    type = models.IntegerField(choices=INVITE_TYPE_CHOICES, default=constants.INVITE_TYPE_SPEAKER_ENUM)

    class Meta:
        verbose_name = _("Invite")
        verbose_name_plural = _("Invites")

    def __str__(self):
        return "{}-{}-{}".format(self.pk, self.group_id, self.invitee)

    def mark_status_as_accepted(self):
        self.status = constants.INVITE_STATUS_ACCEPTED
        self.save()

    def mark_status_as_declined(self):
        self.status = constants.INVITE_STATUS_DECLINED
        self.save()


class Request(base_model.BaseModel):

    REQUEST_STATUS_CHOICES = (
        (constants.REQUEST_STATUS_PENDING_ENUM, constants.REQUEST_STATUS_PENDING),
        (constants.REQUEST_STATUS_ACCEPTED_ENUM, constants.REQUEST_STATUS_ACCEPTED),
        (constants.REQUEST_STATUS_DECLINED_ENUM, constants.REQUEST_STATUS_DECLINED)
    )

    REQUEST_PARTICIPANT_TYPE = (
        (constants.REQUEST_PARTICIPANT_SPEAKER_ENUM, constants.REQUEST_PARTICIPANT_SPEAKER),
        (constants.REQUEST_PARTICIPANT_ATTENDEE_ENUM, constants.REQUEST_PARTICIPANT_ATTENDEE)
    )

    requester = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, related_name="group_requests")
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name="requests")
    status = models.IntegerField(choices=REQUEST_STATUS_CHOICES, default=constants.REQUEST_STATUS_PENDING_ENUM)

    # Will be True for users recommended by WorkNetwork.
    # TODO(Nishant): Remove this later once it is deprecated.
    is_recommended = models.BooleanField(default=False)
    participant_type = models.PositiveIntegerField(
        choices=REQUEST_PARTICIPANT_TYPE,
        default=constants.REQUEST_PARTICIPANT_SPEAKER_ENUM
    )

    class Meta:
        verbose_name = _("Request")
        verbose_name_plural = _("Requests")

    def __str__(self):
        return "{}-{}-{}".format(self.pk, self.group_id, self.requester)

    def mark_status_as_accepted(self):
        self.status = constants.REQUEST_STATUS_ACCEPTED
        self.save()

    def mark_status_as_declined(self):
        self.status = constants.REQUEST_STATUS_DECLINED
        self.save()

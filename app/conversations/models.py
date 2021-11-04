import datetime
import pytz

from django.db import models
from django.core import exceptions
from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils.html import format_html
from django.utils.translation import ugettext_lazy as _

from base import models as base_model
from conversations import constants
from conversations import signals
from model_utils.models import TimeStampedModel
from resources.meetings import models as meeting_models
from utils import validators as validator_utils


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
    description = models.TextField(
        null=True,
        blank=True
    )
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


class Category(base_model.BaseModel):
    name = models.CharField(max_length=64)
    # Denotes a specific color for a category.
    color = models.CharField(
        max_length=16,
        null=True,
        blank=True,
        help_text=_("Enter color code for the color here.")
    )
    photo = models.ImageField(
        upload_to="groups/category/%Y/%m/%d/",
        verbose_name=_("Category Photo"),
        null=True,
        blank=True
    )
    order = models.PositiveSmallIntegerField(
        null=True,
        blank=True
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["order"]
        verbose_name = _("Category")
        verbose_name_plural = _("Categories")

    def __str__(self):
        return self.name

    def color_example(self):
        """Return an html which display the color added
            to the category.

        """
        if not self.color:
            return None

        return format_html(
            "<span style='color: {};'>{}</span>",
            self.color,
            "COLOR EXAMPLE"
        )


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
    # TODO(Nishant): Have to get options for this.
    categories = models.ManyToManyField(
        Category,
        verbose_name=_("Categories"),
        blank=True
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

    interests = models.ManyToManyField(
        meeting_models.Interest,
        verbose_name=_("Interests"),
        blank=True
    )

    # Duration or start of the Group.
    start = models.DateTimeField()
    end = models.DateTimeField(null=True, blank=True)

    max_speakers = models.PositiveIntegerField(default=constants.DEFAULT_MAX_SPEAKERS)
    max_attendees = models.PositiveIntegerField(null=True, blank=True)

    privacy = models.IntegerField(choices=GROUP_PRIVACY_CHOICES, default=constants.GROUP_PRIVACY_PUBLIC_ENUM)
    medium = models.IntegerField(choices=GROUP_MEDIUM_CHOICES, default=constants.GROUP_MEDIUM_AUDIO_ENUM)

    is_featured = models.BooleanField(default=False)
    is_full = models.BooleanField(default=False)

    is_live = models.BooleanField(default=False)
    # Denotes the datetime at which the group was marked live or
    # inactive.
    last_live_at = models.DateTimeField(null=True, blank=True)

    # Group closed status and datetime of closure.
    # TODO(Nishant): Can change this into statuses as well.
    closed = models.BooleanField(default=False)
    closed_at = models.DateTimeField(null=True, blank=True)

    # Group score.
    calculate_score = models.BooleanField(default=False)
    score = models.FloatField(null=True, blank=True)

    # Approval status for groups. This controls if notifications go out,
    # group is visible in all conversations etc.
    is_approved = models.BooleanField(default=True)
    approved_at = models.DateTimeField(null=True, blank=True)
    is_published = models.BooleanField(default=False)

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
            self.end = self.start + datetime.timedelta(hours=1)
        else:
            # Adding end date for webinars as +30 from start.
            self.end = self.start + datetime.timedelta(minutes=30)

        return super(Group, self).save(force_insert, force_update, using, update_fields)

    def approve(self):
        self.is_approved = True
        self.approved_at = datetime.datetime.now()
        self.save()

    def mark_live(self, user=None):
        """Mark group as live."""
        self.is_live = True
        self.last_live_at = datetime.datetime.now()
        self.save()

        # Create log for change on the is_live key.
        self._log_is_live_change(user=user)

        # Send group marked live signal.
        signals.group_marked_live.send(
            sender=self.__class__,
            group=self
        )

    def mark_inactive(self, user=None):
        """Mark group as not live."""
        self.is_live = False
        self.last_live_at = datetime.datetime.now()
        self.save()

        # Create log for change on the is_live key.
        self._log_is_live_change(user=user)

        # Send group marked live signal.
        signals.group_marked_inactive.send(
            sender=self.__class__,
            group=self
        )

    def mark_closed(self, user=None):
        """Marks group as closed.

        Note:
            This marks as group as inactive and
                then closes the group.

        """

        # Mark the meeting as inactive first.
        self.mark_inactive(user=user)
        self.closed = True
        self.closed_at = datetime.datetime.now()
        self.save()
        # Send group marked live signal.
        signals.group_marked_closed.send(
            sender=self.__class__,
            group=self
        )

    def can_start_recording(self):
        """Returns True if the recording can start."""
        recording_min_time = self.start - datetime.timedelta(minutes=5)
        return datetime.datetime.now() > recording_min_time

    def _log_is_live_change(self, user=None):
        """Creates a log if is_live on group changes."""
        if not user:
            return

        # Check if the current status and last
        latest_group_live_log = GroupLiveLog.objects.filter(
            group=self
        ).last()

        # If there is latest log and the status has not changed
        # don't create another log.
        # TODO(Nishant): Can remove this, but it's good condition
        # in case we want precise data.
        if (
                latest_group_live_log and
                latest_group_live_log.live_status == self.is_live
        ):
            return

        return GroupLiveLog.objects.create(
            user=user,
            group=self,
            live_status=self.is_live,
        )

    @property
    def local_start(self):
        """Return start in the local timezone."""
        return self.start.astimezone(pytz.timezone(settings.TIME_ZONE))

    @property
    def local_end(self):
        """Return start in the local timezone."""
        return self.end.astimezone(pytz.timezone(settings.TIME_ZONE)) if self.end else None

    def get_all_users(self):
        """Returns all users that are part of the group."""
        users = [self.host]
        speakers_and_attendees = self.speakers.all() | self.attendees.all()
        for user in speakers_and_attendees:
            if user in users:
                continue
            users.append(user)

        return users

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

    def get_display_start(self):
        """This is the display start date time for a Group.
            ex. "Friday, 31 July - 08:00 PM"

        """
        display_time = self.get_display_start_time()
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

    def get_host_and_speakers(self):
        """Return a list of hosts and speakers."""
        users = [self.host]
        speakers = self.speakers.all()
        for speaker in speakers:
            if speaker in users:
                continue
            users.append(speaker)
        return users


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


class GroupLiveLog(base_model.BaseModel):
    """Keeps logs of is_live change on the Group model."""

    user = models.ForeignKey(
        get_user_model(),
        on_delete=models.CASCADE
    )
    group = models.ForeignKey(
        Group,
        on_delete=models.CASCADE
    )
    live_status = models.BooleanField()


def recording_storage_path(instance, filename):
    """File storage path for group recordings.

    Note:
        Example: "live_stream_recordings/nishant(+9132763723723)/413/filename.mp4

    """
    group = instance.group
    return f"live_stream_recordings/{group.host.__str__()}/{group.id}/{filename}"


class GroupRecording(base_model.BaseModel):
    """Recording for the group.

    Note:
        This is specific to live streams for now.

    """

    group = models.OneToOneField(
        Group,
        related_name="recording",
        on_delete=models.CASCADE
    )
    recording = models.FileField(
        upload_to=recording_storage_path,
        null=True,
        validators=[validator_utils.SizeValidator(size=512)]
    )

    # All dyte recordings for this GroupRecording.
    # Generally there will be only
    dyte_recordings = models.ManyToManyField(
        "dyte.DyteMeetingRecording",
        blank=True
    )
    order = models.PositiveIntegerField(null=True, blank=True)

    is_published = models.BooleanField(default=False)
    published_at = models.DateTimeField(null=True, blank=True)

    def publish(self):
        """Publish the group recording.

        Note:
            Publishing the recording is only allowed if the
                recording is present.

        """
        if not self.recording:
            raise exceptions.ValidationError("Recording must be present to publish.")

        self.is_published = True
        self.published_at = datetime.datetime.now()
        self.save()


class GroupRtmp(base_model.BaseModel):
    """RTMP for the group."""
    group = models.OneToOneField(
        Group,
        related_name="rtmp",
        on_delete=models.CASCADE
    )
    link = models.TextField()


class GroupMessage(base_model.BaseModel):
    """
    Message for the group.
    """
    message = models.TextField()
    group = models.ForeignKey(
        Group,
        related_name='group_questions',
        on_delete=models.CASCADE
    )
    sender = models.ForeignKey(
        get_user_model(),
        related_name='sender_questions',
        on_delete=models.CASCADE
    )
    display_name = models.CharField(
        max_length=128,
        null=True,
        blank=True
    )

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.pk}-{self.sender}"

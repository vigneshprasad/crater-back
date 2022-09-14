import logging
from decimal import Decimal

from dateutil import parser
from django.conf import settings
from django.db import models
from django.utils import timezone
from django.utils.html import format_html

from base import models as base_model
from integrations.dyte import constants

LOGGER = logging.getLogger(__name__)


class DyteMeeting(base_model.BaseModel):

    meeting = models.ForeignKey(
        "meetings.Meeting",
        related_name="dyte_meeting",
        null=True,
        blank=True,
        on_delete=models.CASCADE
    )
    group = models.ForeignKey(
        "conversations.Group",
        related_name="dyte_webinar",
        null=True,
        blank=True,
        on_delete=models.CASCADE
    )
    dyte_meeting_id = models.CharField(max_length=128)
    room_name = models.CharField(max_length=128)

    def __str__(self):
        return "{} - {}".format(self.room_name, (self.meeting_id or self.group_id))


class DyteMeetingParticipant(base_model.BaseModel):

    dyte_meeting = models.ForeignKey(
        "dyte.DyteMeeting",
        related_name="meeting_participants",
        on_delete=models.CASCADE
    )
    participant = models.ForeignKey(
        "users.User",
        on_delete=models.CASCADE,
        related_name="dyte_participant"
    )

    # Auth token for joining the dyte call.
    auth_token = models.TextField()

    last_online_at = models.DateTimeField(null=True, blank=True)
    is_online = models.BooleanField(default=False)

    # Minutes spent on the livestream according to Dyte.
    minutes_spent = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00")
    )

    class Meta:
        unique_together = ["dyte_meeting", "participant"]

    def __str__(self):
        return "{} - {}".format(
            self.dyte_meeting,
            self.participant
        )

    @property
    def latest_join_time(self):
        """Returns datetime after which we are calculating minutes
            spent on a stream for a user.

        """
        return self.dyte_meeting.group.start - timezone.timedelta(minutes=5)

    @property
    def joined_group(self):
        """Returns if the user joined the stream."""
        if self.total_minutes_watched:
            return True

        return False

    @property
    def total_minutes_watched(self):
        """Total minutes spent on the stream."""
        minutes_spent = 0
        online_logs = self.online_logs.all()
        # If there is no last_online_at return 0.
        if not self.last_online_at:
            return minutes_spent

        # If not online logs are there and last_online_at is present,
        # calculate minutes the old way.
        if not online_logs:
            group = self.dyte_meeting.group
            if group and group.closed:
                last_live_time_for_group = min(
                    self.last_online_at, group.last_live_at
                ) if (group and group.last_live_at) else self.last_online_at
            else:
                last_live_time_for_group = self.last_online_at

            # Calculate time spent based on the last live at for group.
            time_spent = max(
                (last_live_time_for_group - self.latest_join_time),
                timezone.timedelta()
            )
            minutes_spent = round(time_spent.seconds / 60)
        else:
            # If logs are present calculate minutes from logs.
            for log in online_logs:
                minutes_spent += log.online_time

        return round(minutes_spent)

    def mark_online(self):
        """Mark a dyte participant online."""
        online_at = max(timezone.now(), self.latest_join_time)
        self.is_online = True
        self.last_online_at = online_at

        # Create online logs.
        online_log, _ = DyteParticipantOnlineLog.objects.get_or_create(
            dyte_meeting_participant=self,
            is_offline=False,
            defaults={
                "online_at": online_at
            }
        )

        self.save()

    def mark_offline(self):
        """Mark a dyte participant offline."""
        if self.is_offline():
            return

        offline_at = max(timezone.now(), self.latest_join_time)
        self.is_online = False
        self.last_online_at = offline_at

        # Update the online log to offline.
        online_log = self.online_logs.filter(is_offline=False).last()
        if online_log:
            online_log.mark_offline()
        else:
            LOGGER.error("Went offline without online log. {} - {}".format(self.id, online_log))

        self.save()

    def is_offline(self):
        """Checks if the participant is already offline."""
        return self.last_online_at and not self.is_online


class DyteParticipantOnlineLog(base_model.BaseModel):

    dyte_meeting_participant = models.ForeignKey(
        "dyte.DyteMeetingParticipant",
        related_name="online_logs",
        on_delete=models.CASCADE
    )
    online_at = models.DateTimeField(null=True, blank=True)
    offline_at = models.DateTimeField(null=True, blank=True)
    is_offline = models.BooleanField(default=False)

    @property
    def online_time(self):
        """Get online time for a log."""
        if not self.online_at:
            return 0

        offline_at = self.offline_at if self.offline_at else timezone.now()
        group = self.dyte_meeting_participant.dyte_meeting.group
        # Update the last_live_at only if the group is closed.
        if group and group.closed:
            last_live_at = group.last_live_at if group.last_live_at else timezone.now()
        else:
            last_live_at = timezone.now()

        offline_at = min(offline_at, last_live_at)
        time_spent = max((offline_at - self.online_at), timezone.timedelta())
        minutes = time_spent.seconds / 60
        return round(minutes)

    def mark_offline(self):
        """Mark the online log offline when the user leaves."""
        offline_at = max(timezone.now(), self.dyte_meeting_participant.latest_join_time)
        # Removing this code block so that we have actual data when the
        # user went offline, we will calculate the online time based on
        # the groups last live at.
        # # Check the group.last_live_at and assign the min value to a log.
        # group = self.dyte_meeting_participant.dyte_meeting.group
        # last_live_at = group.last_live_at if group.last_live_at else timezone.now()
        # offline_at = min(offline_at, last_live_at)

        self.offline_at = offline_at
        self.is_offline = True
        self.save()


class DyteMeetingRecording(base_model.BaseModel):

    RECORDING_STATUS = (
        (constants.DYTE_RECORDING_STATUS_INVOKED, constants.DYTE_RECORDING_STATUS_INVOKED),
        (constants.DYTE_RECORDING_STATUS_RECORDING, constants.DYTE_RECORDING_STATUS_RECORDING),
        (constants.DYTE_RECORDING_STATUS_UPLOADING, constants.DYTE_RECORDING_STATUS_UPLOADING),
        (constants.DYTE_RECORDING_STATUS_UPLOADED, constants.DYTE_RECORDING_STATUS_UPLOADED),
        (constants.DYTE_RECORDING_STATUS_ERRORED, constants.DYTE_RECORDING_STATUS_ERRORED)
    )

    dyte_meeting = models.ForeignKey(
        "dyte.DyteMeeting",
        related_name="meeting_recording",
        on_delete=models.CASCADE
    )
    # Recording ID on Dyte's servers.
    recording_id = models.CharField(max_length=128)
    status = models.CharField(
        max_length=16,
        default=constants.DYTE_RECORDING_STATUS_INVOKED,
        choices=RECORDING_STATUS
    )
    # Path of the recording in S3 bucket.
    path = models.TextField()
    # File size of the recording as we receive from Dyte's end
    # converted in to Mega bytes.
    file_size = models.DecimalField(
        null=True,
        blank=True,
        max_digits=10,
        decimal_places=2,
        verbose_name="File Size(MB)"
    )
    # Recording start time..
    started_at = models.DateTimeField(null=True, blank=True)
    # Recording end time.
    stopped_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return "{}: {}".format(
            self.pk,
            self.recording_id
        )

    @property
    def file_name(self):
        if not self.path:
            return None
        return self.path.split("/")[3]

    @property
    def storage_key_name(self):
        if not self.path:
            return None
        return self.path[1:]

    @property
    def object_url(self):
        url = settings.AWS_DEFAULT_OBJECT_URL + self.path
        return format_html("<a target='_blank' href='{url}'>{url}</a>", url=url)

    def update_start_and_stop_times(self, started_time, stopped_time):
        """Update start and stop times of a recording from Dyte's end."""
        try:
            started_at = parser.parse(started_time)
        except (TypeError, parser.ParserError):
            started_at = None

        try:
            stopped_at = parser.parse(stopped_time)
        except (TypeError, parser.ParserError):
            stopped_at = None

        self.started_at = started_at
        self.stopped_at = stopped_at
        self.save()

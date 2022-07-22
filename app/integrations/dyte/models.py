import datetime
import logging

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
        return "{} - {}".format(self.dyte_meeting_id, (self.meeting or self.group))


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
        null=True,
        blank=True
    )

    class Meta:
        unique_together = ["dyte_meeting", "participant"]

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
        online_logs = DyteParticipantOnlineLog.objects.filter(
            dyte_meeting_participant_id=self.id
        )

        # If there are no online logs, calculate time based on
        # old approach.
        if not (online_logs or self.last_online_at):
            return minutes_spent

        # If not online logs are there and last_online_at is present,
        # calculate minutes the old way.
        if not online_logs:
            time_spent = max(
                (self.last_online_at - self.latest_join_time),
                timezone.timedelta()
            )
            minutes_spent = time_spent.seconds // 60 % 60

        # If logs are present calculate minutes from logs.
        for log in online_logs:
            minutes_spent += log.online_time

        return minutes_spent

    def __str__(self):
        return "{} - {} [{}]".format(
            self.dyte_meeting.id,
            self.dyte_meeting.dyte_meeting_id,
            self.participant.username
        )

    def mark_online(self):
        """Mark a dyte participant online."""
        online_at = max(timezone.now(), self.latest_join_time)
        self.is_online = True
        self.last_online_at = online_at
        self.save()

        # Create online logs.
        online_log = DyteParticipantOnlineLog.objects.create(
            dyte_meeting_participant_id=self.id,
            online_at=online_at
        )

    def mark_offline(self):
        """Mark a dyte participant offline."""
        offline_at = max(timezone.now(), self.latest_join_time)
        self.is_online = False
        self.last_online_at = offline_at
        self.save()

        # Update the online log to offline.
        online_log = DyteParticipantOnlineLog.objects.filter(
            dyte_meeting_participant=self,
            is_offline=False
        ).first()
        if not online_log:
            LOGGER.error("Went offline without online log. {}".format(self.id))
            return None

        online_log.mark_offline()


class DyteParticipantOnlineLog(base_model.BaseModel):

    dyte_meeting_participant = models.ForeignKey(
        "dyte.DyteMeetingParticipant",
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

        last_online_at = self.offline_at if self.offline_at else timezone.now()
        time_spent = max((last_online_at - self.online_at), timezone.timedelta())
        minutes = time_spent.seconds // 60 % 60
        return minutes

    def mark_offline(self):
        """Mark the online log offline when the user leaves."""
        offline_at = max(timezone.now(), self.dyte_meeting_participant.latest_join_time)
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
    path = models.TextField()
    started_at = models.DateTimeField(null=True, blank=True)
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

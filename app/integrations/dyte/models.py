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
    def joined_group(self):
        """Returns if the user joined the stream."""
        if not self.last_online_at:
            return False

        # The user can sit on the stream 5 minutes before the stream
        # TODO(Nishant): Check the front end logic here.
        latest_group_join_time = self.dyte_meeting.group.start - datetime.timedelta(minutes=5)
        return latest_group_join_time <= self.last_online_at
        # return DyteParticipantOnlineLog.objects.filter(dyte_meeting_participant_id=self.id).exists()

    @property
    def total_minutes_watched(self):
        """Total minutes spent on the stream."""
        minutes_spent = 0
        online_logs = DyteParticipantOnlineLog.objects.filter(
            dyte_meeting_participant_id=self.id
        )

        # If there are no online logs, calculate time based on
        # old approach.
        if not online_logs:
            time_spent = self.last_online_at - self.dyte_meeting.group.start
            minutes_spent = time_spent.seconds // 60 % 60

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
        self.is_online = True
        self.last_online_at = datetime.datetime.now()
        self.save()

        # Create online logs.
        DyteParticipantOnlineLog.objects.create(
            dyte_meeting_participant_id=self.id
        )

    def mark_offline(self):
        self.is_online = False
        self.last_online_at = datetime.datetime.now()
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
    online_at = models.DateTimeField(auto_now_add=True)
    offline_at = models.DateTimeField(null=True, blank=True)
    is_offline = models.BooleanField(default=False)

    @property
    def online_time(self):
        last_online_at = self.offline_at if self.offline_at else timezone.now()
        time_spent = last_online_at - self.online_at
        minutes = time_spent.seconds // 60 % 60
        return minutes

    def mark_offline(self):
        self.offline_at = timezone.now()
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

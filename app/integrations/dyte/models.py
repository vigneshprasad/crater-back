import datetime

from django.conf import settings
from django.db import models
from django.utils.html import format_html

from base import models as base_model
from integrations.dyte import constants


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
        return "{} - {}".format(self.room_name, (self.meeting or self.group))


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

    def mark_online(self):
        self.is_online = True
        self.last_online_at = datetime.datetime.now()
        self.save()

    def mark_offline(self):
        self.is_online = False
        self.last_online_at = datetime.datetime.now()
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
    def object_url(self):
        url = settings.AWS_DEFAULT_OBJECT_URL + self.path
        return format_html("<a target='_blank' href='{url}'>{url}</a>", url=url)

from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.utils.translation import ugettext_lazy as _

from base import models as base_model
from integrations.dyte import constants


class DyteWebhook(base_model.BaseModel):

    EVENT_CHOICES = (
        (constants.DYTE_EVENT_MEETING_STARTED, constants.DYTE_EVENT_MEETING_STARTED),
        (constants.DYTE_EVENT_MEETING_ENDED, constants.DYTE_EVENT_MEETING_ENDED),
        (constants.DYTE_EVENT_PARTICIPANT_JOINED, constants.DYTE_EVENT_PARTICIPANT_JOINED),
        (constants.DYTE_EVENT_PARTICIPANT_LEFT, constants.DYTE_EVENT_PARTICIPANT_LEFT),
        (constants.DYTE_EVENT_RECORDING_STATUS_UPDATE, constants.DYTE_EVENT_RECORDING_STATUS_UPDATE)
    )

    webhook_id = models.CharField(max_length=128)
    name = models.CharField(
        max_length=32,
        verbose_name=_("Webhook Name")
    )
    url = models.URLField(
        verbose_name=_("Webhook Url")
    )
    events = ArrayField(
        models.CharField(max_length=64, blank=True, choices=EVENT_CHOICES)
    )
    is_active = models.BooleanField(default=True)


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
    auth_token = models.TextField()
    is_online = models.BooleanField(default=False)

    def mark_online(self):
        self.is_online = True
        self.save()

    def mark_offline(self):
        self.is_online = False
        self.save()

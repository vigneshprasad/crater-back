from django.db import models

from base import models as base_model


class DyteMeeting(base_model.BaseModel):
    meeting = models.ForeignKey(
        "meetings.Meeting",
        related_name="dyte_meeting",
        null=True,
        blank=True,
        on_delete=models.CASCADE
    )
    dyte_meeting_id = models.CharField(max_length=128)
    room_name = models.CharField(max_length=128)

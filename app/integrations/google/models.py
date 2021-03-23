from django.db import models

from base import models as base_models
from integrations.google import constants
from users import models as user_models


class GoogleCalendarEvent(base_models.BaseModel):
    user = models.ForeignKey(
        user_models.User,
        related_name='calendar_events',
        on_delete=models.CASCADE
    )
    # TODO(Nishant): Add group id here.
    meeting_id = models.IntegerField(null=True, blank=True)
    # What was the last status of the event.
    status = models.CharField(
        max_length=64,
        choices=constants.CALENDAR_RESPONSE_STATUSES,
        default=constants.CALENDAR_RESPONSE_STATUSES[0][0]
    )
    event_id = models.CharField(max_length=128, null=True, blank=True)
    meeting_link = models.CharField(max_length=128, null=True, blank=True)
    starts_at = models.DateTimeField(null=True, blank=True)
    ends_at = models.DateTimeField(null=True, blank=True)

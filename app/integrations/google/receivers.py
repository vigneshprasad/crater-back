import datetime
import logging

from django.dispatch import receiver
from googleapiclient.errors import HttpError

from integrations.google import models
from integrations.google import calendar_services
from resources.meetings import signals as meeting_signals


@receiver(meeting_signals.meeting_marked_cancelled)
def delete_calendar_event_on_meeting_cancellation(sender, meeting, *args, **kwargs):
    """Remove google calendar event if the meeting is cancelled.

    Args:
        sender(Meeting class): Class representation of meeting.
        meeting(Meeting): Meeting object that was cancelled.

    """
    # Getting distinct event id's for calendar events.
    google_calendar_event_ids = models.GoogleCalendarEvent.objects.filter(
        meeting_id=meeting.id
    ).values_list('event_id', flat=True).distinct()

    for event_id in google_calendar_event_ids:
        try:
            calendar_services.google_calendar_service.delete_event(
                event_id=event_id
            )
            # Marking the google event as is deleted.
            models.GoogleCalendarEvent.objects.filter(event_id=event_id).delete()
        # Catching any sort of exception and sending it to sentry for now.
        except Exception as e:
            logging.error(
                "Google calendar delete failed with status {} for: {}".format(e, event_id)
            )
            continue

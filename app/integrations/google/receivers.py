from django.dispatch import receiver

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
    google_calendar_events = models.GoogleCalendarEvent.objects.filter(
        meeting_id=meeting.id
    )

    for calendar_event in google_calendar_events:
        calendar_services.google_calendar_service.delete_event(
            event_id=calendar_event.event_id
        )

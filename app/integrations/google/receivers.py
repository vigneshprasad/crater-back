from django.dispatch import receiver

from integrations.google import private
from resources.meetings import signals as meeting_signals


@receiver(meeting_signals.meeting_marked_cancelled)
def delete_calendar_event_on_meeting_cancellation(sender, meeting, *args, **kwargs):
    """Remove google calendar event if the meeting is cancelled.

    Args:
        sender(Meeting class): Class representation of meeting.
        meeting(Meeting): Meeting object that was cancelled.

    """
    # Getting distinct event id's for calendar events.
    private.delete_calendar_for_meeting(meeting=meeting)


@receiver(meeting_signals.reschedule_request_declined)
def delete_calendar_event_on_reschedule_request_decline(sender, reschedule_request, *args, **kwargs):
    """Remove google calendar event if the meeting is cancelled.

    Args:
        sender(Meeting class): Class representation of meeting.
        reschedule_request(RescheduleRequest): Meeting object that was cancelled.

    """
    # Getting distinct event id's for calendar events.
    private.delete_calendar_for_meeting(meeting=reschedule_request.old_meeting)

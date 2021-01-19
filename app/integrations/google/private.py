import logging

from integrations.google import calendar_services
from integrations.google import constants
from integrations.google import models


def get_and_update_event_status_for_event(google_calendar_event):

    # If the calendar status is already in accepted status, don't do anything.
    if google_calendar_event.status in constants.ACCEPTED_CALENDAR_STATUSES:
        return google_calendar_event.status

    event_id = google_calendar_event.event_id
    event_data = calendar_services.google_calendar_service.get_event(event_id)
    attendees = event_data.get('attendees')
    if not attendees:
        return

    # Default status.
    status = constants.CALENDAR_RESPONSE_STATUSES[0][0]

    for attendee in attendees:
        if attendee.get('email') == google_calendar_event.user.email:
            status = attendee.get('responseStatus')

    # Update status in the model with the latest status.
    google_calendar_event.status = status
    google_calendar_event.save()

    return status


def delete_calendar_for_meeting(meeting):
    """Deletes calendar event for a meeting.

    Args:
        meeting(Meeting): Meeting object calendar is to be
            deleted for.

    """
    if not meeting:
        return True

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

    return True

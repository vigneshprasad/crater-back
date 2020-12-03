from integrations.google import constants
from integrations.google.calendar_services import google_calendar_service


def get_and_update_event_status_for_event(google_calendar_event):

    # If the calendar status is already in accepted status, don't do anything.
    if google_calendar_event.status in constants.ACCEPTED_CALENDAR_STATUSES:
        return google_calendar_event.status

    event_id = google_calendar_event.event_id
    event_data = google_calendar_service.get_event(event_id)
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

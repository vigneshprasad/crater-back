from integrations.google import models
from integrations.google.calendar_services import google_calendar_service


def update_meetings_link_to_google_meet_links(meetings):
    """Update meeting with google meet links instead of superpro links."""

    for meeting in meetings:
        google_calendar_event = models.GoogleCalendarEvent.objects.filter(
            meeting_id=meeting.id
        ).first()

        if not google_calendar_event:
            print("No google calendar event for meeting: {}".format(meeting.id))
            continue

        try:
            meeting_link = google_calendar_service.update_event_to_google_meet(
                google_calendar_event.event_id
            )
            meeting.meeting_link = meeting_link
            meeting.save()
            print("Updated to google meet for meeting: {}".format(meeting.id))
        except Exception as e:
            print(e)

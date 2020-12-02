import datetime

from integrations.google import calendar_services
from integrations.google import constants
from integrations.google import models


def create_calendar_event_for_meeting(meeting):
    users = meeting.participants.all()
    start_datetime = datetime.datetime.combine(
        date=meeting.time_slot.date,
        time=meeting.time_slot.start_time
    )
    end_datetime = datetime.datetime.combine(
        date=meeting.time_slot.date,
        time=meeting.time_slot.end_time
    )
    event_id, hangout_link = calendar_services.google_calendar_service.create_event(
        start_datetime,
        end_datetime,
        users,
        meeting,
        summary=constants.DEFAULT_SUMMARY_FOR_MEETING_EVENTS,
        description=constants.DEFAULT_DESCRIPTION_FOR_MEETING_EVENTS,
    )

    # Creating model entries for each user.
    for user in users:
        models.GoogleCalendarEvent.objects.create(
            user=user,
            meeting_id=meeting.id,
            meeting_link=hangout_link,
            event_id=event_id,
            starts_at=start_datetime,
            ends_at=end_datetime
        )

    return hangout_link

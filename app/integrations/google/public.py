import datetime

from integrations.google import calendar_services
from integrations.google import constants


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
    hangout_link = calendar_services.google_calendar_service.create_event(
        start_datetime,
        end_datetime,
        users,
        summary=constants.DEFAULT_SUMMARY_FOR_MEETING_EVENTS,
        description=constants.DEFAULT_DESCRIPTION_FOR_MEETING_EVENTS
    )
    return hangout_link

from integrations.google import calendar_services
from integrations.google import models
from integrations.google import private
from integrations.google import constants


def create_calendar_event_for_meeting(meeting):
    """Creates google calendar event for a meeting.

    Args:
        meeting(Meeting): Meeting object for which we have to
            create the calendar event.

    """
    users = meeting.participants.all()
    start_datetime = meeting.local_start
    end_datetime = meeting.local_end
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


def get_and_update_rsvp_status(meeting_rsvp):
    """ Get Status and update status of meetings rsvp object via google api

    Args:
        meeting_rsvp(MeetingRsvp): The MeetingRsvp object whose status is updated

    """
    user = meeting_rsvp.participant
    google_calendar_event = models.GoogleCalendarEvent.objects.filter(
        user=user,
        meeting_id=meeting_rsvp.meeting.id,
    ).last()

    # If there is no calendar event in the future, return.
    if not google_calendar_event:
        return

    status = private.get_and_update_event_status_for_event(google_calendar_event)
    updated_status = constants.CALENDAR_RESPONSE_TO_MEETING_RSVP_STATUS_MAP[status]
    meeting_rsvp.status = updated_status
    meeting_rsvp.save()

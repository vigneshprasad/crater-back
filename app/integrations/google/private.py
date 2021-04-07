import logging

from django.conf import settings

from integrations.google import calendar_services
from integrations.google import constants
from integrations.google import models
from utils.deep_link_service import deep_link_service


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
        return False

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


def update_or_create_calendar_event_for_conversation(user, group):
    """Updates the google calendar event for a conversation.

    Args:
        user(User): User that was recently added to the group.
        group(Group): Group for which we have to update the event.

    """
    google_calendar_event = models.GoogleCalendarEvent.objects.filter(
        group_id=group.id,
    ).last()

    if not google_calendar_event:
        # Create the calendar event for the group.
        create_calendar_event_for_conversations(group)
        return True

    # Refreshing the group instance.
    group.refresh_from_db()
    event_id = google_calendar_event.event_id

    try:
        calendar_services.google_calendar_service.update_event_attendees(
            event_id,
            group.speakers.all()
        )
        # Creating calendar event entry.
        models.GoogleCalendarEvent.objects.create(
            user=user,
            group_id=group.id,
            event_id=event_id,
            starts_at=group.local_start,
            ends_at=group.local_end
        )
    except Exception as e:
        logging.error(
            "Google calendar update failed with status {} for: {}".format(e, group.id)
        )

    return True


def create_calendar_event_for_conversations(group):
    """Create calendar event for a group.

     Args:
        group(Group): Group object for which we have to
            create the calendar event.

    """
    users = group.speakers.all()
    start_datetime = group.local_start
    end_datetime = group.local_end

    group_link = "https://{}/group?id={}".format(settings.FRONT_URL, group.id)
    deeplink = deep_link_service.make_firebase_deep_link(group_link)

    summary = constants.DEFAULT_SUMMARY_FOR_CONVERSATIONS.format(topic_name=group.topic.name)
    description = constants.DEFAULT_DESCRIPTION_FOR_CONVERSATIONS.format(deeplink=deeplink)

    event_id, _ = calendar_services.google_calendar_service_without_conference_data.create_event(
        start_datetime,
        end_datetime,
        users,
        summary=summary,
        description=description
    )

    # Create rows for users.
    for user in users:
        models.GoogleCalendarEvent.objects.create(
            user=user,
            group_id=group.id,
            event_id=event_id,
            starts_at=start_datetime,
            ends_at=end_datetime
        )

    return event_id

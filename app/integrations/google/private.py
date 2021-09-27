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


def update_or_create_calendar_event_for_conversation(group):
    """Updates the google calendar event for a conversation.

    Args:
        group(Group): Group for which we have to update the event.

    """
    google_calendar_event = models.GoogleCalendarEvent.objects.filter(
        group_id=group.id,
    ).last()

    if not google_calendar_event:
        # Create the calendar event for the group.
        return create_calendar_event_for_conversations(group)

    # Refreshing the group instance.
    group.refresh_from_db()
    users = group.get_all_users()
    event_id = google_calendar_event.event_id

    try:
        calendar_services.google_calendar_service.update_event_attendees(
            event_id,
            users
        )
        # Creating calendar event entry.
        for user in users:
            models.GoogleCalendarEvent.objects.update_or_create(
                user=user,
                group_id=group.id,
                event_id=event_id,
                defaults={
                    "starts_at": group.local_start,
                    "ends_at": group.local_end
                }
            )
    except Exception as e:
        logging.error(
            "Google calendar update failed with status {} for: {}".format(e, group.id)
        )

    return event_id


def create_calendar_event_for_conversations(group):
    """Create calendar event for a group.

     Args:
        group(Group): Group object for which we have to
            create the calendar event.

    Note:
        This function is only eligible for AMA and Group
            conversation for now.

    """
    users = group.get_all_users()
    start_datetime = group.local_start
    end_datetime = group.local_end

    group_link = "https://{}/group?id={}".format(settings.FRONT_URL, group.id)
    deeplink = deep_link_service.make_firebase_deep_link(group_link)

    summary = constants.DEFAULT_SUMMARY_FOR_CONVERSATIONS.format(topic_name=group.topic.name)
    description = constants.DEFAULT_DESCRIPTION_FOR_CONVERSATIONS.format(deeplink=deeplink)

    event_id, _ = calendar_services.google_calendar_service_without_conference_data.create_event(
        start_datetime=start_datetime,
        end_datetime=end_datetime,
        users=users,
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


def create_calendar_event_for_webinar_host(group):
    """Create calendar event for a live stream an attendee.

    Args:
        group(Group): Group the user joined into.

    """
    host = group.host

    # TODO(Nishant): This has to change for each environment.
    stream_link = "https://crater.club/session/{group_id}".format(
        group_id=group.id
    )
    summary = constants.HOST_SUMMARY_FOR_WEBINARS
    description = constants.HOST_DESCRIPTION_FOR_WEBINARS.format(
        creator_name=host.name.title(),
        date=group.get_display_day(),
        time=group.get_display_start_time(),
        topic=group.topic.name,
        stream_link=stream_link,
        phone_number=host.username
    )

    event_id, meeting_link = calendar_services.google_calendar_service.create_event(
        start_datetime=group.local_start,
        end_datetime=group.local_end,
        users=[group.host],
        summary=summary,
        description=description,
        conference_name=constants.DEFAULT_CONFERENCE_NAME_FOR_WEBINAR,
        meeting_link=stream_link
    )

    models.GoogleCalendarEvent.objects.create(
        user=group.host,
        group_id=group.id,
        event_id=event_id,
        meeting_link=meeting_link,
        starts_at=group.local_start,
        ends_at=group.local_end
    )

    return event_id


def create_calendar_event_for_webinar_attendee(user, group):
    """Create calendar event for a live stream an attendee.

    Args:
        user(User): Attendee that joined the group.
        group(Group): Group the user joined into.

    """
    host = group.host

    # TODO(Nishant): This has to change for each environment.
    stream_link = "https://crater.club/session/{group_id}".format(
        group_id=group.id
    )

    summary = constants.ATTENDEE_SUMMARY_FOR_WEBINARS.format(
        creator_name=host.name.title(),
        topic=group.topic.name
    )
    description = constants.ATTENDEE_SUMMARY_FOR_WEBINARS.format(
        creator_name=host.name.title(),
        date=group.get_display_day(),
        time=group.get_display_start_time(),
        topic=group.topic.name,
        stream_link=stream_link,
        # TODO(Nishant): Get app link from Ram/Vivan and add it here.
        app_link=""
    )

    event_id, meeting_link = calendar_services.google_calendar_service.create_event(
        start_datetime=group.local_start,
        end_datetime=group.local_end,
        users=[user],
        summary=summary,
        description=description,
        conference_name=constants.DEFAULT_CONFERENCE_NAME_FOR_WEBINAR,
        meeting_link=stream_link
    )

    models.GoogleCalendarEvent.objects.update_or_create(
        user=group.host,
        group_id=group.id,
        event_id=event_id,
        meeting_link=meeting_link,
        defaults={
            "starts_at": group.local_start,
            "ends_at": group.local_end
        }
    )

    return event_id

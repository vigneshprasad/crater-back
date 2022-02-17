from conversations import models as conversations_models

from integrations.google import constants
from integrations.google import models
from integrations.google.calendar_services import google_calendar_service


def run(group_id, link, dry_run=True):

    group = conversations_models.Group.objects.get(id=group_id)
    series = group.series_groups.first()
    all_calendar_events = models.GoogleCalendarEvent.objects.filter(
        group_id=group_id
    )
    for calendar_event in all_calendar_events:
        print("-------")
        if calendar_event.user in group.get_host_and_speakers():
            continue

        if not series:
            description = constants.ATTENDEE_DESCRIPTION_FOR_WEBINARS.format(
                creator_name=group.host.display_name,
                date=group.get_display_day(),
                time=group.get_display_start_time(),
                topic=group.topic.name,
                stream_link=link,
                # TODO(Nishant): Get app link from Ram/Vivan and add it here.
                app_link=""
            )
        else:
            description = constants.ATTENDEE_DESCRIPTION_FOR_SERIES.format(
                creator_name=group.host.display_name,
                date=group.get_display_day(),
                time=group.get_display_start_time(),
                series_name=series.topic.name,
                topic=group.topic.name,
                stream_link=link,
                # TODO(Nishant): Get app link from Ram/Vivan and add it here.
                app_link=""
            )

        patch_body = {
            "description": description,
            "conferenceData": {
                "conferenceSolution": {
                    "name": constants.DEFAULT_CONFERENCE_NAME_FOR_WEBINAR,
                    "key": {
                        "type": constants.ADD_ON_LINK
                    },
                    "iconUri": constants.DEFAULT_ICON_URI_FOR_GOOGLE_EVENTS
                },
                "entryPoints": [
                    {
                        "entryPointType": "video",
                        "label": link,
                        "uri": link
                    }
                ]
            }
        }

        if not calendar_event.event_id:
            print("No event ID")
            print(calendar_event.user)
            print(calendar_event.user.email)
            print(calendar_event.group_id)
            continue

        print("Updating")
        print(calendar_event.user)
        print(calendar_event.user.email)
        print(calendar_event.group_id)

        if not dry_run:
            google_calendar_service.service.events().patch(
                calendarId=google_calendar_service.calendar_id,
                eventId=calendar_event.event_id,
                body=patch_body,
                conferenceDataVersion=google_calendar_service.conference_data_version
            ).execute()

        print("-------")

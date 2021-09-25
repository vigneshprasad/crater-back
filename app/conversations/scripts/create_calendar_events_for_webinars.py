from conversations import models
from conversations import constants
from integrations.google import private as google_private


def run(dry_run=False):
    webinars = models.Group.objects.filter(
        type=constants.GROUP_TYPE_WEBINAR_ENUM
    )

    for webinar in webinars:
        # Doing this to generate end time for webinars.
        webinar.save()
        print("----")

        print("Webinar ID: ", webinar.id)
        print("Webinar Host: ", webinar.host.__str__())
        print("Webinar run from: {} - {}".format(webinar.local_start, webinars.local_end))

        if not dry_run:
            print("Creating google event for Webinar.")
            event_id = google_private.update_or_create_calendar_event_for_conversation(
                webinar
            )
            print("Created google event: {}".format(event_id))

        print("----")

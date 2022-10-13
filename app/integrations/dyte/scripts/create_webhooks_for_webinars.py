from integrations.dyte import constants
from integrations.dyte.service import dyte_service

ALL_WEBHOOK_DATA = [
    {
        "name": "Participant Joined",
        "events": [constants.DYTE_EVENT_PARTICIPANT_JOINED],
        "url": "https://api.prod.worknetwork.in/v1/integrations/dyte/participant/joined/"
    },
    {
        "name": "Participant Left",
        "events": [constants.DYTE_EVENT_PARTICIPANT_LEFT],
        "url": "https://api.prod.worknetwork.in/v1/integrations/dyte/participant/left/"
    },
    {
        "name": "Meeting Ended",
        "events": [constants.DYTE_EVENT_MEETING_ENDED],
        "url": "https://api.prod.worknetwork.in/v1/integrations/dyte/meeting/ended/"
    },
    {
        "name": "Meeting Recording",
        "events": [constants.DYTE_EVENT_RECORDING_STATUS_UPDATE],
        "url": "https://api.prod.worknetwork.in/v1/integrations/dyte/recording/status/"
    },
]

ALL_WEBHOOK_DATA_PREPROD = [
    {
        "name": "Participant Joined Testing",
        "events": [constants.DYTE_EVENT_PARTICIPANT_JOINED],
        "url": "https://api.dev.worknetwork.in/v1/integrations/dyte/participant/joined/"
    },
    {
        "name": "Participant Left Testing",
        "events": [constants.DYTE_EVENT_PARTICIPANT_LEFT],
        "url": "https://api.dev.worknetwork.in/v1/integrations/dyte/participant/left/"
    },
    {
        "name": "Meeting Ended Testing",
        "events": [constants.DYTE_EVENT_MEETING_ENDED],
        "url": "https://api.dev.worknetwork.in/v1/integrations/dyte/meeting/ended/"
    },
    {
        "name": "Meeting Recording Testing",
        "events": [constants.DYTE_EVENT_RECORDING_STATUS_UPDATE],
        "url": "https://api.dev.worknetwork.in/v1/integrations/dyte/recording/status/"
    },
]


LIVE_STREAM_STATUS_WEBHOOK = [
    {
        "name": "Livestream Update Testing",
        "events": [constants.DYTE_EVENT_LIVESTREAM_STATUS_UPDATE],
        "url": "https://api.dev.worknetwork.in/v1/integrations/dyte/livestream/status/"
    },
    {
        "name": "Livestream Update",
        "events": [constants.DYTE_EVENT_PARTICIPANT_LEFT],
        "url": "https://api.prod.worknetwork.in/v1/integrations/dyte/livestream/status/"
    },
]


def run(dry_run=True, all_webhook_data=None):

    for webhook_data in all_webhook_data:
        print("Creating Webhook")
        print(webhook_data["name"], webhook_data["events"], webhook_data["url"])

        if not dry_run:
            response = dyte_service.create_webhook(
                name=webhook_data["name"],
                events=webhook_data["events"],
                webhook_endpoint=webhook_data["url"]
            )
            print("Created Webhook")
            print(response)

    print("----")

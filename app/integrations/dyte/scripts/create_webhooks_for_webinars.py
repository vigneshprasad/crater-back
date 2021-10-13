from integrations.dyte import constants
from integrations.dyte.service import dyte_service

ALL_WEBHOOK_DATA = [
    {
        "name": "Participant Joined",
        "events": [constants.DYTE_EVENT_PARTICIPANT_JOINED],
        "url": "https://back.worknetwork.in/v1/integrations/dyte/participant/joined/"
    },
    {
        "name": "Participant Left",
        "events": [constants.DYTE_EVENT_PARTICIPANT_LEFT],
        "url": "https://back.worknetwork.in/v1/integrations/dyte/participant/left/"
    },
    {
        "name": "Meeting Ended",
        "events": [constants.DYTE_EVENT_MEETING_ENDED],
        "url": "https://back.worknetwork.in/v1/integrations/dyte/meeting/ended/"
    },
    {
        "name": "Meeting Recording",
        "events": [constants.DYTE_EVENT_RECORDING_STATUS_UPDATE],
        "url": "https://back.worknetwork.in/v1/integrations/dyte/recording/status/"
    },
]

ALL_WEBHOOK_DATA_PREPROD = [
    {
        "name": "Participant Joined Testing",
        "events": [constants.DYTE_EVENT_PARTICIPANT_JOINED],
        "url": "https://back-pre.1worknetwork.com/v1/integrations/dyte/participant/joined/"
    },
    {
        "name": "Participant Left Testing",
        "events": [constants.DYTE_EVENT_PARTICIPANT_LEFT],
        "url": "https://back-pre.1worknetwork.com/v1/integrations/dyte/participant/left/"
    },
    {
        "name": "Meeting Ended Testing",
        "events": [constants.DYTE_EVENT_MEETING_ENDED],
        "url": "https://back-pre.1worknetwork.com/v1/integrations/dyte/meeting/ended/"
    },
    {
        "name": "Meeting Recording Testing",
        "events": [constants.DYTE_EVENT_RECORDING_STATUS_UPDATE],
        "url": "https://back-pre.1worknetwork.com/v1/integrations/dyte/recording/status/"
    },
]


def run(dry_run=True, pre_prod=True):

    all_webhook_data = ALL_WEBHOOK_DATA_PREPROD if pre_prod else ALL_WEBHOOK_DATA

    for webhook_data in all_webhook_data:

        print("Creating Webhook")
        print(webhook_data["name"], webhook_data["events"], webhook_data["url"])

        if not dry_run:
            webhook_data = dyte_service.create_webhook(
                name=webhook_data["name"],
                events=webhook_data["events"],
                webhook_endpoint=webhook_data["url"]
            )
            print("Created Webhook")
            print(webhook_data)

    print("----")

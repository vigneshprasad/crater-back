from integrations.dyte import constants
from integrations.dyte.service import dyte_service
from integrations.dyte.scripts import delete_old_dyte_webhooks

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
]


def run(dry_run=True):

    delete_old_dyte_webhooks.run(dry_run=dry_run)

    for webhook_data in ALL_WEBHOOK_DATA:

        print("Creating Webhook")
        print(webhook_data["name"], webhook_data["events"], webhook_data["url"])

        if not dry_run:
            webhook = dyte_service.create_webhook(
                name=webhook_data["name"],
                events=webhook_data["events"],
                webhook_endpoint=webhook_data["url"]
            )
            print("Created Webhook")
            print(webhook.id, webhook.webhook_id)

    print("----")

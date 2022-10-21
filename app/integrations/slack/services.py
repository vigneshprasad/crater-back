import logging

import requests
from django.conf import settings

from integrations.slack import constants


LOGGER = logging.getLogger(__name__)


class SlackService:

    SLACK_API_ENDPOINTS = {
        "send_message_to_channel": settings.SLACK_BASE_API_URL + "/chat.postMessage"
    }

    def __init__(self, auth_token):
        self.auth_token = auth_token

    def _get_authorization_headers(self):
        """Create authorization headers for Dyte service."""
        return {
            "Accept": "application/json",
            "Authorization": "Bearer {}".format(
                self.auth_token
            ),
            "Content-Type": "application/json"
        }

    def send_message(self, text, channel_id=constants.SLACK_DEFAULT_CHANNEL_ID):
        """Sends message to a Slack channel.

        Args:
            text(str): Text we have to send as a Slack message.
            channel_id(str): Channel ID of the Slack channel
                we are sending the message to.

        """
        send_message_endpoint = self.SLACK_API_ENDPOINTS["send_message_to_channel"]
        data = {
            "channel": channel_id,
            "text": text
        }
        response = requests.request(
            "POST",
            send_message_endpoint,
            headers=self._get_authorization_headers(),
            json=data
        )
        response_json = response.json()
        response_ok = response_json["ok"]
        response_metadata = response_json["response_metadata"]

        if not response_ok:
            LOGGER.error("Slack message didn't go: {} - {}".format(
                response_json.get("error"),
                response_metadata.get("messages")
            ))
            return False

        return response_json


slack_service = SlackService(
    auth_token=settings.SLACK_OATH_TOKEN
)

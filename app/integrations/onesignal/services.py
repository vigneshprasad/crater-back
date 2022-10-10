import logging

import requests
from django.conf import settings

from integrations.onesignal import constants

LOGGER = logging.getLogger(__name__)


class OneSignalService:
    """One signal service to send push notifications to users."""

    ONE_SIGNAL_API_ENDPOINTS = {
        "players": constants.ONE_SIGNAL_BASE_API_URL + "/api/v1/players/",
        "notifications": constants.ONE_SIGNAL_BASE_API_URL + "/api/v1/notifications/"
    }

    def __init__(self, app_id: str, apikey: str):
        self.app_id = app_id
        self.apikey = apikey

    def get_headers(self):
        return {
            "Authorization": "Basic {}".format(self.apikey),
            "Content-Type": "application/json; charset=utf-8"
        }

    def send_push(self, players_list, contents, data, content_available=False):
        """Sends push notifications to the player ids provided.

        Args:
            players_list(list): List of player ids (from one signal dashboard).
            contents(dict): Dictionary representation of the notification we are
                sending.
            data(dict): Extra data we are sending with the notification.
            content_available(bool): Sending true wakes your app from
                background to run custom native code

        """
        payload = {
            "app_id": self.app_id,
            "include_player_ids": players_list,
            "contents": contents,
            "data": data
        }

        if content_available:
            payload["content-available"] = True

        response = requests.post(
            self.ONE_SIGNAL_API_ENDPOINTS["notifications"],
            json=payload,
            headers=self.get_headers()
        ).json()

        return response

    def send_bulk_notification(self, player_ids, notification_json):
        """Sends notifications give notification json and player id.

        Args:
            player_ids(list): List of player ids (from one signal dashboard).
            notification_json(dict): Dictionary representation of the notification we are
                sending.

        Note:
            player_ids should always be less than 2000 per call.

        """
        notification_json["app_id"] = self.app_id
        notification_json["include_player_ids"] = player_ids

        try:
            response = requests.post(
                self.ONE_SIGNAL_API_ENDPOINTS["notifications"],
                json=notification_json,
                headers=self.get_headers()
            ).json()
        except Exception as e:
            LOGGER.exception(str(e))
            return None

        return response

    def send_notification(self, player_id, notification_json):
        """Sends notifications give notification json and player id.

        Args:
            player_id(uuid): Player id (from one signal dashboard).
            notification_json(dict): Dictionary representation of the notification we are
                sending.

        """
        notification_json["app_id"] = self.app_id
        notification_json["include_player_ids"] = [player_id]

        try:
            response = requests.post(
                self.ONE_SIGNAL_API_ENDPOINTS["notifications"],
                json=notification_json,
                headers=self.get_headers()
            ).json()
        except Exception as e:
            LOGGER.exception(str(e))
            return None

        return response


one_signal_service = OneSignalService(
    settings.ONESIGNAL_APP_ID,
    settings.ONESIGNAL_APIKEY,
)

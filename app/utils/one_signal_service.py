import requests
from django.conf import settings


class OneSignalService:
    API_BASE_URL = "https://onesignal.com"
    API_URL = {
        "players": "/api/v1/players/",
        "notifications": "/api/v1/notifications/"
    }

    def __init__(self, app_id: str, apikey: str):
        self.app_id = app_id
        self.apikey = apikey

    def get_headers(self):
        return {
            "Authorization": "Basic %s" % self.apikey
        }

    def get_api_endpoint(self, name: str):
        return "%s%s" % (self.API_BASE_URL, self.API_URL.get(name))

    def send_push(self, players_list: list, contents: dict, data: dict, content_available: bool = False):
        payload = {
            "app_id": self.app_id,
            "include_player_ids": players_list,
            "contents": contents,
            "data": data
        }

        if content_available:
            payload["content-available"] = True

        response = requests.post(
            self.get_api_endpoint("notifications"),
            json=payload,
            headers=self.get_headers()
        ).json()

        return response

    def send_notification(self, player_id, notification_json):
        """Sends notifications give notification json and player id."""
        notification_json["app_id"] = self.app_id
        notification_json["include_player_ids"] = [player_id]

        response = requests.post(
            self.get_api_endpoint("notifications"),
            json=notification_json,
            headers=self.get_headers()
        ).json()

        return response


os_service = OneSignalService(
    settings.ONESIGNAL_APP_ID,
    settings.ONESIGNAL_APIKEY,
)

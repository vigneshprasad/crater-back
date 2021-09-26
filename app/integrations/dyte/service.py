import logging
import json
import requests

from integrations.dyte import constants
from integrations.dyte import models


class DyteService:

    DYTE_API_ENDPOINTS = {
        "join_meeting": constants.DYTE_JOIN_MEETING_BASE_URL + "/meeting/join/{room_name}",
        # These are all API endpoints.
        "create_meeting": constants.DYTE_PROD_BASE_URL + "/v1/organizations/{org_id}/meeting",
        "add_participant": constants.DYTE_PROD_BASE_URL + "/v1/organizations/{org_id}/meetings/{meeting_id}/participant",
        "get_all_meetings": constants.DYTE_PROD_BASE_URL + "/v1/organizations/{org_id}/meetings",
        "get_meeting": constants.DYTE_PROD_BASE_URL + "/v1/organizations/{org_id}/meetings/{dyte_meeting_id}",
        "create_webhook": constants.DYTE_PROD_BASE_URL + "/v1/organizations/{org_id}/webhook",
        "delete_webhook": constants.DYTE_PROD_BASE_URL + "/v1/organizations/{org_id}/webhook/{webhook_id}",
        "get_all_webhooks": constants.DYTE_PROD_BASE_URL + "/v1/organizations/{org_id}/webhooks",
    }

    def __init__(self, org_id, app_id):
        self.org_id = org_id
        self.app_id = app_id

    def _get_authorization_headers(self):
        """Create authorization headers for Dyte service."""
        return {
            "Accept": "application/json",
            "Authorization": "APIKEY {}".format(
                self.app_id
            ),
            "Content-Type": "application/json"
        }

    def _create_meeting_url_for_room_name(self, room_name):
        """Returns a meeting url for a room name returned by Dyte
            meeting creation.

        Args:
            room_name(str): Room name created on dyte for a meeting.

        """
        return self.DYTE_API_ENDPOINTS["join_meeting"].format(room_name=room_name)

    def create_meeting(self, meeting, preset_name=constants.DEFAULT_PRESET_NAME):
        """Creates meeting on Dyte for a given meeting object.

        Args:
            meeting(Meeting): Meeting object from the server.
            preset_name(str): Name of the preset being used by Dyte. Can be setup
                on their Developer dashboard.

        """
        create_meeting_endpoint = self.DYTE_API_ENDPOINTS["create_meeting"].format(org_id=self.org_id)

        # Adding this check so we don't update meeting links.
        if meeting.link:
            logging.error("Meeting already has a meeting link:{}, {}".format(meeting.id, meeting.link))
            return None

        participants = meeting.participants.all()

        data = {
            "title": "1:1 Professional Networking | " + " & ".join(
                [user.get_display_first_name() for user in participants]
            ),
            "presetName": preset_name,
            "authorization": {
                "waitingRoom": False,
                "closed": False
            }
        }
        response = requests.request("POST", create_meeting_endpoint, headers=self._get_authorization_headers(), json=data)

        try:
            response_json = response.json()
        except json.JSONDecodeError:
            logging.error("Dyte meeting creation failed: {}".format(meeting.id))
            return None

        meeting_data = response_json["data"]["meeting"]
        room_name = meeting_data["roomName"]
        dyte_meeting_id = meeting_data["id"]

        # Creating the dyte meeting object for a meeting.
        models.DyteMeeting.objects.create(
            meeting=meeting,
            dyte_meeting_id=dyte_meeting_id,
            room_name=room_name
        )

        return self._create_meeting_url_for_room_name(room_name=room_name)

    def create_custom_meeting(self, title=None, preset_name=constants.DEFAULT_PRESET_NAME):
        """Create custom meetings with custom title and preset on Dyte.

        Args:
            title(str): Title of the Dyte meeting.
            preset_name(str): Name of the preset being used by Dyte. Can be setup
                on their Developer dashboard.

        Note:
            Used for creating test/internal meetings.

        """
        create_meeting_endpoint = self.DYTE_API_ENDPOINTS["create_meeting"].format(org_id=self.org_id)

        data = {
            "title": title,
            "presetName": preset_name,
            "authorization": {
                "waitingRoom": False,
                "closed": False
            }
        }
        response = requests.request(
            "POST",
            create_meeting_endpoint,
            headers=self._get_authorization_headers(),
            json=data
        )
        try:
            response_json = response.json()
        except json.JSONDecodeError:
            logging.error("Dyte custom meeting creation failed")
            return None

        meeting_data = response_json["data"]["meeting"]
        room_name = meeting_data["roomName"]

        return self._create_meeting_url_for_room_name(room_name=room_name)

    def create_webinar(self, group, preset_name=constants.DEFAULT_WEBINAR_PARTICIPANT_PRESET_NAME):
        """Create a webinar on Dyte with given group object and add host

        Args:
            group(Group): Group object from the server.
            preset_name(str): Name of the preset being used by Dyte. Can be setup
                on their Developer dashboard.

        """
        create_meeting_endpoint = self.DYTE_API_ENDPOINTS["create_meeting"].format(org_id=self.org_id)

        data = {
            "title": group.topic.name,
            "presetName": preset_name,
            "authorization": {
                "waitingRoom": False,
                "closed": False
            }
        }
        response = requests.request(
            "POST",
            create_meeting_endpoint,
            headers=self._get_authorization_headers(),
            json=data
        )
        try:
            response_json = response.json()
        except json.JSONDecodeError:
            logging.error("Dyte webinar creation failed")
            return None

        meeting_data = response_json["data"]["meeting"]
        room_name = meeting_data["roomName"]
        dyte_meeting_id = meeting_data["id"]

        # Creating the dyte meeting object for a webinar.
        dyte_meeting = models.DyteMeeting.objects.create(
            group=group,
            dyte_meeting_id=dyte_meeting_id,
            room_name=room_name
        )

        # Add host to webinar
        self.add_participant_to_meeting(
            dyte_meeting=dyte_meeting,
            preset_name=constants.DEFAULT_WEBINAR_HOST_PRESET_NAME,
            user=group.host
        )

    def add_participant_to_meeting(
            self,
            dyte_meeting,
            user,
            preset_name=constants.DEFAULT_WEBINAR_PARTICIPANT_PRESET_NAME
    ):
        """Add a host / participant to Dyte meeting with appropriate preset name

        Args:
            dyte_meeting(DyteMeeting): DyteMeeting object from server.
            user(User): User object from server.
            preset_name(str): Name of the preset being used by Dyte. Can be setup
                on their Developer dashboard.

        """
        add_participant_endpoint = self.DYTE_API_ENDPOINTS["add_participant"].format(
            org_id=self.org_id,
            meeting_id=dyte_meeting.dyte_meeting_id
        )

        data = {
            "clientSpecificId": str(user.uuid),
            "presetName": preset_name,
            "userDetails": {
                "name": user.name
            }
        }
        response = requests.request(
            "POST",
            add_participant_endpoint,
            headers=self._get_authorization_headers(),
            json=data
        )
        try:
            response_json = response.json()
        except json.JSONDecodeError:
            logging.error("Dyte add participant failed")
            return None

        participant_data = response_json["data"]["authResponse"]
        auth_token = participant_data["authToken"]

        dyte_participant, _ = models.DyteMeetingParticipant.objects.update_or_create(
            dyte_meeting=dyte_meeting,
            participant=user,
            defaults={
                "auth_token": auth_token
            }
        )
        return dyte_participant

    def get_all_meetings_data(self):
        """Returns all meetings created by organisation."""
        get_all_meetings_url = self.DYTE_API_ENDPOINTS["get_all_meetings"].format(org_id=self.org_id)
        response = requests.request("GET", get_all_meetings_url, headers=self._get_authorization_headers())

        try:
            response_json = response.json()
        except json.JSONDecodeError:
            logging.error("Dyte get all meetings failed")
            return None

        meetings_data = response_json["data"]["meetings"]
        return meetings_data

    def get_meeting_data(self, meeting):
        """Get a single meeting on Dyte for given meeting id.

        Args:
            meeting(Meeting): Meeting object from the server.

        """
        try:
            dyte_meeting = models.DyteMeeting.objects.get(meeting=meeting)
        except models.DyteMeeting.DoesNotExist:
            return None

        dyte_meeting_id = dyte_meeting.dyte_meeting_id
        url = self.DYTE_API_ENDPOINTS["get_meeting"].format(org_id=self.org_id, dyte_meeting_id=dyte_meeting_id)
        response = requests.request("GET", url, headers=self._get_authorization_headers())

        try:
            response_json = response.json()
        except json.JSONDecodeError:
            logging.error("Dyte get all meetings failed")
            return None

        meeting_data = response_json["data"]["meeting"]
        return meeting_data

    def get_custom_meeting_data(self, dyte_meeting_id):
        """Get a single meeting on Dyte for dyte meeting id.

        Args:
            dyte_meeting_id(str): Dyte Meeting ID from the server.

        Note:
            Used for testing and data visualisation.

        """
        url = self.DYTE_API_ENDPOINTS["get_meeting"].format(org_id=self.org_id, dyte_meeting_id=dyte_meeting_id)
        response = requests.request("GET", url, headers=self._get_authorization_headers())

        try:
            response_json = response.json()
        except json.JSONDecodeError:
            logging.error("Dyte get all meetings failed")
            return None

        meeting_data = response_json["data"]["meeting"]
        return meeting_data

    def create_webhook(self, name, events, webhook_endpoint):
        """Create webhook on Dyte's end for dyte meeting events.

        name(str): Reference name for the webhook created.
        events(list of Events): Events on Dyte's end for which we need a
            webhook response on the provided url.
        webhook_endpoint(url): Url on our end which need to be hit for
            a particular event.

        """
        url = self.DYTE_API_ENDPOINTS["create_webhook"].format(
            org_id=self.org_id
        )
        data = {
            "events": events,
            "name": name,
            "url": webhook_endpoint
        }
        response = requests.request(
            "POST",
            url,
            headers=self._get_authorization_headers(),
            json=data
        )

        try:
            response_json = response.json()
        except json.JSONDecodeError:
            logging.error("Dyte webhook creation failed.")
            return None

        webhook_id = response_json.get("id")
        # Create dyte webhook object.
        dyte_webhook = models.DyteWebhook.objects.create(
            webhook_id=webhook_id,
            name=name,
            events=events,
            url=webhook_endpoint,
            is_active=True
        )

        return dyte_webhook

    def delete_webhook(self, webhook_id):
        """Deletes a webhook on Dyte's end.

        Args:
            webhook_id(uuid): Id of the webhook on Dyte's end.

        """
        url = self.DYTE_API_ENDPOINTS["get_all_webhooks"].format(
            org_id=self.org_id,
            webhook_id=webhook_id
        )
        response = requests.request(
            "GET",
            url,
            headers=self._get_authorization_headers()
        )

        try:
            response_json = response.json()
        except json.JSONDecodeError:
            logging.error("Dyte webhooks get failed.")
            return None

        try:
            dyte_webhook = models.DyteWebhook.objects.get(
                webhook_id=webhook_id,
                is_active=False
            )
        except models.DyteWebhook.DoesNotExist:
            return None

        return dyte_webhook

    def get_all_webhooks(self):
        """Returns all webhooks on Dyte's end."""
        url = self.DYTE_API_ENDPOINTS["get_all_webhooks"].format(org_id=self.org_id)
        response = requests.request(
            "GET",
            url,
            headers=self._get_authorization_headers()
        )

        try:
            response_json = response.json()
        except json.JSONDecodeError:
            logging.error("Dyte webhooks get failed.")
            return None

        return response_json


dyte_service = DyteService(
    constants.DYTE_ORG_ID,
    constants.DYTE_APP_ID
)

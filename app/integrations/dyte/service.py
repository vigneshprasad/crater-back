import logging
import json
import requests

from integrations.dyte import constants
from integrations.dyte import models


class DyteService:

    DYTE_API_ENDPOINTS = {
        "create_meeting": constants.DYTE_PROD_BASE_URL + "/v1/organizations/{org_id}/meeting",
        "get_all_meetings": constants.DYTE_PROD_BASE_URL + "/v1/organizations/{org_id}/meetings",
        "get_meeting": constants.DYTE_PROD_BASE_URL + "/v1/organizations/{org_id}/meetings/{dyte_meeting_id}",
        "join_meeting": constants.DYTE_JOIN_MEETING_BASE_URL + "/meeting/join/{room_name}"
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

    def create_meeting(self, meeting):
        """Creates meeting on Dyte for a given meeting object.

        Args:
            meeting(Meeting): Meeting object from the server.

        """
        create_meeting_endpoint = self.DYTE_API_ENDPOINTS["create_meeting"].format(org_id=self.org_id)

        participants = meeting.participants.all()

        data = {
            "title": "1:1_Professional Networking_WorkNetwork | " + " &".join([user.get_display_first_name() for user in participants]),
            "presetName": constants.DEFAULT_PRESET_NAME,
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

        dyte_meeting, created = models.DyteMeeting.objects.update_or_create(
            meeting=meeting,
            dyte_meeting_id=dyte_meeting_id,
            room_name=room_name
        )
        if not created:
            logging.info("Dyte meeting updated for: {}".format(meeting.id))

        return self._create_meeting_url_for_room_name(room_name=room_name)

    def get_all_meetings(self):
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

    def get_meeting(self, meeting):
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


dyte_service = DyteService(
    constants.DYTE_ORG_ID,
    constants.DYTE_APP_ID
)

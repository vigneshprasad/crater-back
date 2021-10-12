import logging
import json
import requests

from integrations.dyte import constants
from integrations.dyte import models

from freelance import settings


class DyteService:
    DYTE_API_ENDPOINTS = {
        "join_meeting": constants.DYTE_JOIN_MEETING_BASE_URL + "/meeting/join/{room_name}",
        # Meeting endpoints.
        "create_meeting": constants.DYTE_PROD_BASE_URL + "/v1/organizations/{org_id}/meeting",
        "get_meeting": constants.DYTE_PROD_BASE_URL + "/v1/organizations/{org_id}/meetings/{dyte_meeting_id}",
        "get_all_meetings": constants.DYTE_PROD_BASE_URL + "/v1/organizations/{org_id}/meetings",
        # Participant addition enpoint.
        "add_participant": constants.DYTE_PROD_BASE_URL + "/v1/organizations/{org_id}/meetings/{meeting_id}/participant",
        # Webhook endpoints.
        "create_webhook": constants.DYTE_PROD_BASE_URL + "/v1/organizations/{org_id}/webhook",
        "get_webhook": constants.DYTE_PROD_BASE_URL + "/v1/organizations/{org_id}/webhooks/{webhook_id}",
        "delete_webhook": constants.DYTE_PROD_BASE_URL + "/v1/organizations/{org_id}/webhooks/{webhook_id}",
        "get_all_webhooks": constants.DYTE_PROD_BASE_URL + "/v1/organizations/{org_id}/webhooks",
        # Recording endpoints.
        "start_recording": constants.DYTE_PROD_BASE_URL + "/v1/organizations/{org_id}/rooms/{room_name}/recording",
        "stop_recording": constants.DYTE_PROD_BASE_URL + "/v1/organizations/{org_id}/rooms/{room_name}/recordings/{recording_id}",
        "get_recording": constants.DYTE_PROD_BASE_URL + "/v1/organizations/{org_id}/meetings/{meeting_id}/recordings/{recording_id}",
        "get_all_recordings": constants.DYTE_PROD_BASE_URL + "/v1/organizations/{org_id}/meetings/{meeting_id}/recordings",
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
        return self.DYTE_API_ENDPOINTS["join_meeting"].format(
            room_name=room_name
        )

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
        response = requests.request("POST", create_meeting_endpoint, headers=self._get_authorization_headers(),
                                    json=data)

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
            "presetName": constants.DEFAULT_WEBINAR_PRESET_NAME,
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

    def get_meeting(self, dyte_meeting_id):
        """Get a single meeting on Dyte for dyte meeting id.

        Args:
            dyte_meeting_id(str): Dyte Meeting ID from the server.

        Note:
            Used for testing and data visualisation.

        """
        url = self.DYTE_API_ENDPOINTS["get_meeting"].format(org_id=self.org_id, dyte_meeting_id=dyte_meeting_id)
        response = requests.request(
            "GET",
            url,
            headers=self._get_authorization_headers()
        )

        try:
            response_json = response.json()
        except json.JSONDecodeError:
            logging.error("Dyte get all meetings failed")
            return None

        meeting_data = None
        if response_json["success"]:
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

        url = self.DYTE_API_ENDPOINTS["create_webhook"].format(org_id=self.org_id)
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

        webhook_data = None
        if response_json["success"]:
            webhook_data = response_json["data"]["webhook"]

        return webhook_data

    def get_webhook(self, webhook_id):
        """Returns webhook data from Dyte's end.

        Args:
            webhook_id(uuid): Id of the webhook on Dyte's end.

        """

        url = self.DYTE_API_ENDPOINTS["get_webhook"].format(org_id=self.org_id, webhook_id=webhook_id)
        response = requests.request(
            "GET",
            url,
            headers=self._get_authorization_headers()
        )

        try:
            response_json = response.json()
        except json.JSONDecodeError:
            logging.error("Dyte webhooks delete failed.")
            return None

        webhook_data = None
        if response_json["success"]:
            webhook_data = response_json["data"]["webhook"]

        return webhook_data

    def delete_webhook(self, webhook_id):
        """Deletes a webhook on Dyte's end.

        Args:
            webhook_id(uuid): Id of the webhook on Dyte's end.

        """

        url = self.DYTE_API_ENDPOINTS["delete_webhook"].format(org_id=self.org_id, webhook_id=webhook_id)
        response = requests.request(
            "DELETE",
            url,
            headers=self._get_authorization_headers()
        )

        try:
            response_json = response.json()
        except json.JSONDecodeError:
            logging.error("Dyte webhooks delete failed.")
            return None

        return response_json["success"]

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

        webhooks_data = None
        if response_json["success"]:
            webhooks_data = response_json["data"]["webhooks"]

        return webhooks_data

    def start_recording(self, dyte_meeting):
        """Start a recording for a given meeting room

        Args:
            dyte_meeting(DyteMeeting): DyteMeeting object

        """
        url = self.DYTE_API_ENDPOINTS["start_recording"].format(
            org_id=self.org_id,
            room_name=dyte_meeting.room_name
        )

        group_id = dyte_meeting.group_id if dyte_meeting.group_id else dyte_meeting.meeting_id
        path = constants.DYTE_MEETING_RECORDING_AWS_PATH.format(
            group_id=group_id
        )

        data = {
            "storageConfig": {
                "type": "aws",
                "accessKey": settings.AWS_ACCESS_KEY_ID,
                "secret": settings.AWS_SECRET_ACCESS_KEY,
                "region": settings.AWS_S3_REGION_NAME,
                "bucket": settings.AWS_STORAGE_BUCKET_NAME,
                "path": path
            }
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
            logging.error("Dyte start recording failed.")
            return None

        dyte_meeting_recording = None
        if not response_json.get("success"):
            return dyte_meeting_recording

        recording_data = response_json["data"]["recording"]
        recording_id = recording_data.get("id")
        status = recording_data.get("status")

        if status and status == constants.DYTE_RECORDING_STATUS_ERRORED:
            error_message = recording_data.get("errMessage")
            logging.error(
                "Dyte recording {} for Group: {}".format(
                    error_message,
                    dyte_meeting.group.id
                )
            )
            return None

        dyte_meeting_recording, _ = models.DyteMeetingRecording.objects.update_or_create(
            dyte_meeting=dyte_meeting,
            recording_id=recording_id,
            defaults={
                "status": status,
                "path": f"/{path}{recording_data.get('outputFileName')}"
            }
        )

        return dyte_meeting_recording.recording_id

    def stop_recording(self, room_name, recording_id):
        """Get a recording for a given meeting

        Args:
            room_name(str): Dyte meeting room name
            recording_id(str): Dyte recording id

        """
        if not (room_name and recording_id):
            return None

        url = self.DYTE_API_ENDPOINTS["stop_recording"].format(
            org_id=self.org_id,
            room_name=room_name,
            recording_id=recording_id
        )
        data = {
            "recordingAction": "stop"
        }
        response = requests.request(
            "PUT",
            url,
            headers=self._get_authorization_headers(),
            json=data
        )

        try:
            response_json = response.json()
        except json.JSONDecodeError:
            logging.error("Dyte stop recording failed.")
            return None

        recording_data = None
        if response_json.get("success"):
            recording_data = response_json["data"]["recording"]

        return recording_data

    def get_recording(self, meeting_id, recording_id):
        """Get a recording for a given meeting

        Args:
            meeting_id(str): Dyte meeting id
            recording_id(str): Dyte recording id

        """
        if not (meeting_id and recording_id):
            return None

        url = self.DYTE_API_ENDPOINTS["get_recording"].format(
            org_id=self.org_id,
            meeting_id=meeting_id,
            recording_id=recording_id
        )

        response = requests.request(
            "GET",
            url,
            headers=self._get_authorization_headers()
        )

        try:
            response_json = response.json()
        except json.JSONDecodeError:
            logging.error("Dyte get recording failed.")
            return None

        recording_data = None
        if response_json.get("success"):
            recording_data = response_json["data"]["recording"]

        return recording_data

    def get_all_recordings(self, dyte_meeting):
        """Get a recording for a given meeting

        Args:
            dyte_meeting(DyteMeeting): DyteMeeting object

        """

        if not dyte_meeting.dyte_meeting_id:
            return False

        url = self.DYTE_API_ENDPOINTS["get_all_recordings"].format(
            org_id=self.org_id,
            meeting_id=dyte_meeting.dyte_meeting_id
        )

        response = requests.request(
            "GET",
            url,
            headers=self._get_authorization_headers()
        )

        try:
            response_json = response.json()
        except json.JSONDecodeError:
            logging.error("Dyte get recordings failed.")
            return None

        recording_data = None
        if response_json.get("success"):
            recording_data = response_json["data"]["recordings"]

        return recording_data


dyte_service = DyteService(
    constants.DYTE_ORG_ID,
    constants.DYTE_APP_ID
)

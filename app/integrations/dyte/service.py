import json
import logging
import base64

import requests
from django.conf import settings
from django.contrib.auth import get_user_model

from integrations.dyte import constants, models

LOGGER = logging.getLogger(__name__)


class DyteService:

    DYTE_API_ENDPOINTS = {
        "join_meeting": constants.DYTE_JOIN_MEETING_BASE_URL + "/meeting/join/{room_name}",

        # Meeting endpoints.
        "create_meeting": constants.DYTE_PROD_BASE_URL + "/v1/organizations/{org_id}/meeting",
        "get_meeting": constants.DYTE_PROD_BASE_URL + "/v1/organizations/{org_id}/meetings/{dyte_meeting_id}",
        "get_all_meetings": constants.DYTE_PROD_BASE_URL + "/v1/organizations/{org_id}/meetings",

        # Participant addition endpoint.
        "add_participant": constants.DYTE_PROD_BASE_URL + "/v1/organizations/{org_id}/meetings/{meeting_id}/participant",

        # Webhook endpoints.
        "create_webhook": constants.DYTE_PROD_BASE_URL + "/v1/organizations/{org_id}/webhook",
        "update_webhook": constants.DYTE_PROD_BASE_URL + "/v1/organizations/{org_id}/webhooks/{webhook_id}",
        "get_webhook": constants.DYTE_PROD_BASE_URL + "/v1/organizations/{org_id}/webhooks/{webhook_id}",
        "delete_webhook": constants.DYTE_PROD_BASE_URL + "/v1/organizations/{org_id}/webhooks/{webhook_id}",
        "get_all_webhooks": constants.DYTE_PROD_BASE_URL + "/v1/organizations/{org_id}/webhooks",

        # Recording endpoints.
        "start_recording": constants.DYTE_PROD_BASE_URL + "/v1/organizations/{org_id}/meetings/{meeting_id}/recording",
        "stop_recording": constants.DYTE_PROD_BASE_URL + "/v1/organizations/{org_id}/meetings/{meeting_id}/recordings/{recording_id}",
        "get_recording": constants.DYTE_PROD_BASE_URL + "/v1/organizations/{org_id}/meetings/{meeting_id}/recordings/{recording_id}",
        "get_all_recordings": constants.DYTE_PROD_BASE_URL + "/v1/organizations/{org_id}/meetings/{meeting_id}/recordings",

        # Stats for meeting endpoints.
        "get_stats_for_meeting": constants.DYTE_PROD_BASE_URL + "/v1/organizations/{org_id}/meetings/{meeting_id}/analytics",

        # Preset adding/updating endpoints.
        "get_preset": constants.DYTE_PROD_BASE_URL + "/v1/organizations/{org_id}/presets",
        "add_preset": constants.DYTE_PROD_BASE_URL + "/v1/organizations/{org_id}/preset"
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

        # Adding this check so that we don't update meeting links.
        if meeting.link:
            LOGGER.error("Meeting already has a meeting link:{}, {}".format(meeting.id, meeting.link))
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
        response = requests.request(
            "POST",
            create_meeting_endpoint,
            headers=self._get_authorization_headers(),
            json=data
        )

        try:
            response_json = response.json()
        except json.JSONDecodeError:
            LOGGER.error("Dyte meeting creation failed: {}".format(meeting.id))
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
            LOGGER.error("Dyte custom meeting creation failed")
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
            LOGGER.error("Dyte webinar creation failed")
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
            LOGGER.error("Dyte add participant failed")
            return None

        success = response_json.get("success")
        if not success:
            LOGGER.error("Dyte add participant failed: {}".format(
                response_json.get("message")
            ))
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
            LOGGER.error("Dyte get all meetings failed")
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
            LOGGER.error("Dyte get all meetings failed")
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
            LOGGER.error("Dyte webhook creation failed.")
            return None

        webhook_data = None
        if response_json["success"]:
            webhook_data = response_json["data"]["webhook"]

        return webhook_data

    def update_webhook(self, webhook_id, name, events, webhook_endpoint):
        """Update webhook on Dyte's end for dyte meeting events.

        webhook_id(uuid): Id of the webhook on Dyte's end.
        name(str): Reference name for the webhook being updated.
        events(list of Events): Events on Dyte's end for which we need a
            webhook response on the provided url.
        webhook_endpoint(url): Url on our end which need to be hit for
            a particular event.

        """

        url = self.DYTE_API_ENDPOINTS["update_webhook"].format(org_id=self.org_id, webhook_id=webhook_id)
        data = {
            "events": events,
            "name": name,
            "url": webhook_endpoint
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
            LOGGER.error("Dyte webhook update failed.")
            return None

        return response_json["success"]

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
            LOGGER.error("Dyte webhooks delete failed.")
            return None

        return response_json["success"]

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
            LOGGER.error("Dyte webhooks delete failed.")
            return None

        webhook_data = None
        if response_json["success"]:
            webhook_data = response_json["data"]["webhook"]

        return webhook_data

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
            LOGGER.error("Dyte webhooks get failed.")
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
            meeting_id=dyte_meeting.dyte_meeting_id
        )

        group_id = dyte_meeting.group_id if dyte_meeting.group_id else dyte_meeting.meeting_id
        path = constants.DYTE_MEETING_RECORDING_AWS_PATH.format(
            group_id=group_id
        )

        data = {
            "storageConfig": {
                "type": "aws",
                "accessKey": settings.DYTE_AWS_ACCESS_KEY_ID,
                "secret": settings.DYTE_AWS_SECRET_ACCESS_KEY,
                "region": settings.AWS_S3_REGION_NAME,
                "bucket": settings.AWS_STORAGE_BUCKET_NAME,
                "path": path
            },
            # Changing recording duration to 24 hrs, instead of
            # default 3 hours.
            "maxSeconds": 86400
        }

        if hasattr(dyte_meeting.group, "rtmp"):
            data["liveStreamingConfig"] = {
                "rtmpUrl": dyte_meeting.group.rtmp.link
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
            LOGGER.error("Dyte start recording failed.")
            return None

        dyte_meeting_recording = None
        if not response_json.get("success"):
            # Send the message to logger if recording didn't start.
            LOGGER.error("Dyte start recording failed: {}".format(response_json.get("message")))
            return dyte_meeting_recording

        recording_data = response_json["data"]["recording"]
        recording_id = recording_data.get("id")
        status = recording_data.get("status")

        if status and status == constants.DYTE_RECORDING_STATUS_ERRORED:
            # If recording errored for some reason, log that error.
            error_message = recording_data.get("errMessage")
            LOGGER.error(
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

    def stop_recording(self, dyte_meeting, recording_id):
        """Get a recording for a given meeting

        Args:
            dyte_meeting(DyteMeeting): DyteMeeting object
            recording_id(str): Dyte recording id

        """
        if not (dyte_meeting and recording_id):
            return None

        url = self.DYTE_API_ENDPOINTS["stop_recording"].format(
            org_id=self.org_id,
            meeting_id=dyte_meeting.dyte_meeting_id,
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
            LOGGER.error("Dyte stop recording failed.")
            return None

        recording_data = None
        if not response_json.get("success"):
            LOGGER.error("Dyte stop recording failed: {}".format(
                response_json.get("message")
            ))
            return recording_data

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
            LOGGER.error("Dyte get recording failed.")
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
            LOGGER.error("Dyte get recordings failed.")
            return None

        recording_data = None
        if response_json.get("success"):
            recording_data = response_json["data"]["recordings"]

        return recording_data

    def get_stats_for_meeting(self, webinar):
        """Get stats saved on Dyte's end for a webinar.

        Args:
            webinar(Group): Group object we are getting the data for.

        Sample data:
            {
              "success": true,
              "analytics": [
                {
                  "clientSpecificId": "6b74e36c-ba2a-4bb9-b961-40b1adfcbc11",
                  "events": [
                        {
                          "event": "PEER_JOINING",
                          "time": "2022-01-31T14:43:34.726Z",
                          "details": {}
                        }
                    ],
                    "totalMinutes": 89.38738333333333
                },
                {
                  "clientSpecificId": "cff364bf-d0fa-4216-8a60-673366477688",
                   "events": [
                        {
                            "event": "PEER_JOINING",
                            "time": "2022-01-31T14:43:44.925Z",
                            "details": {}
                        }
                    ],
                    "totalMinutes": 81.43025
                }
              ]
            }

        """
        dyte_meeting = webinar.dyte_webinar.first()
        if not dyte_meeting and dyte_meeting.dyte_meeting_id:
            return False

        url = self.DYTE_API_ENDPOINTS["get_stats_for_meeting"].format(
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
            LOGGER.error("Dyte get recordings failed.")
            return None

        stats = []
        if response_json.get("success"):
            stats = response_json.get("analytics")

        # Create a data set with the clientSpecificId and totalMinutes.
        data = []
        for stat in stats:
            user_pk = stat["clientSpecificId"]
            user = get_user_model().objects.filter(pk=user_pk).first() if user_pk else None
            data.append(
                {
                    "clientSpecificId": user_pk,
                    "user": user.__str__() if user else "",
                    "totalMinutes": stat["totalMinutes"] if stat["totalMinutes"] < 300 else 0
                }
            )

        return data

    def get_stats_for_meetings(self, webinars):
        """Get combined stats for multiple meetings.

        Args:
            webinars(Queryset/list): Queryset of list of groups.

        """
        data = []
        for webinar in webinars:
            stats = self.get_stats_for_meeting(webinar)
            data += stats

        return data

    def get_all_presets(self):
        """Gets all data related to present from Dyte's end."""
        url = self.DYTE_API_ENDPOINTS["get_preset"].format(
            org_id=self.org_id,
        )
        response = requests.request(
            "GET",
            url,
            headers=self._get_authorization_headers()
        )
        try:
            response_json = response.json()
        except json.JSONDecodeError:
            LOGGER.error("Dyte get recordings failed.")
            return None

        presets_info = response_json["data"]["presets"]
        for preset in presets_info:
            print("ID: {}".format(preset["id"]))
            print("Name: {}".format(preset["name"]))
            print("Settings URL: {}".format(preset["s3URL"]))
            print("Description: {}".format(preset["description"]))
            print("************")

        return True

    def add_update_preset(self, preset_name, properties):
        """Adds or updates a preset on Dyte's end.

        Args:
            preset_name(str): Name of the preset we are creating
                or updating.
            properties(dict): Properties we want to assign to the
                preset.

        """
        url = self.DYTE_API_ENDPOINTS["add_preset"].format(org_id=self.org_id)
        # Post data.
        data = {
            "name": preset_name,
            "description": "",
            "preset": properties,
            "version": "0.5.0"
        }
        response = requests.request(
            "POST",
            url,
            json=data,
            headers=self._get_authorization_headers()
        )
        print(response)
        try:
            response_json = response.json()
        except json.JSONDecodeError:
            return None

        print(response_json)
        return True


class DyteServiceV2:
    DYTE_API_ENDPOINTS = {
        "start_livestream": constants.DYTE_BASE_URL_V2 + "/meetings/{meeting_id}/livestreams",
        "get_active_livestream": constants.DYTE_BASE_URL_V2 + "/meetings/{meeting_id}/active-livestream",
        "stop_active_livestream": constants.DYTE_BASE_URL_V2 + "/meetings/{meeting_id}/active-livestream/stop"
    }

    def __init__(self, org_id, app_id):
        self.org_id = org_id
        self.app_id = app_id

    def _get_authorization_headers(self):
        """Create authorization headers for Dyte service."""

        token = self.org_id + ":" + self.app_id
        token_bytes = token.encode("ascii")
        base64_bytes = base64.b64encode(token_bytes)
        encrypted_token = base64_bytes.decode("ascii")

        return {
            "Accept": "application/json",
            "Authorization": "Basic {}".format(
                encrypted_token
            ),
            "Content-Type": "application/json"
        }

    def start_livestream_for_meeting(self, dyte_meeting):
        url = self.DYTE_API_ENDPOINTS["start_livestream"].format(meeting_id=dyte_meeting.dyte_meeting_id)
        response = requests.request(
            "POST",
            url,
            headers=self._get_authorization_headers(),
            json={
                "name": dyte_meeting.room_name
            }
        )
        try:
            response_json = response.json()
        except json.JSONDecodeError:
            return None

        success = response_json["success"]

        if not success:
            logging.error("LiveStream not started successfully: {meeting_id}".format(
                meeting_id=dyte_meeting.dyte_meeting_id
            ))
            return None

        data = response_json["data"]

        livestream_id = data["id"]

        print("start_livestream_for_meeting", response_json)

        models.LiveStream.objects.update_or_create(
            livestream_id=livestream_id,
            dyte_meeting=dyte_meeting,
            defaults={
                "status": data["status"],
                "ingest_server": data["ingest_server"],
                "stream_key": data["stream_key"],
                "playback_url": data["playback_url"]
            }
        )

    def stop_active_livestream_meeting(self, dyte_meeting):
        url = self.DYTE_API_ENDPOINTS["stop_active_livestream"].format(meeting_id=dyte_meeting.dyte_meeting_id)
        response = requests.request(
            "POST",
            url,
            headers=self._get_authorization_headers(),
            json={
                "name": dyte_meeting.room_name
            }
        )

        try:
            response_json = response.json()
        except json.JSONDecodeError:
            return None

        success = response_json["success"]

        if not success:
            logging.error("LiveStream not started successfully: {meeting_id}".format(
                meeting_id=dyte_meeting.dyte_meeting_id
            ))
            return None
        print("stop_active_livestream_meeting", response_json)

    def get_active_livestream(self, dyte_meeting):
        url = self.DYTE_API_ENDPOINTS["get_active_livestream"].format(meeting_id=dyte_meeting.dyte_meeting_id)
        response = requests.request(
            "GET",
            url,
            headers=self._get_authorization_headers(),
        )

        try:
            response_json = response.json()
        except json.JSONDecodeError:
            return None

        success = response_json["success"]
        data = response_json["data"]

        if not success:
            logging.error(
                "LiveStream not started successfully: {meeting_id}".format(meeting_id=dyte_meeting.dyte_meeting_id)
            )
            return None

        if data.get("message"):
            message = "Service error {error}".format(error=data.get("message"))
            logging.error(message)
            return None

        models.LiveStream.objects.update_or_create(
            livestream_id=data["id"],
            dyte_meeting=dyte_meeting,
            defaults={
                "ingest_seconds": data["ingest_seconds"],
                "viewer_seconds": data["viewer_seconds"],
                "status": data["status"],
                "ingest_server": data["ingest_server"],
                "stream_key": data["stream_key"],
                "playback_url": data["playback_url"]
            }
        )
        print("stop_active_livestream_meeting", response_json)


dyte_service = DyteService(
    constants.DYTE_ORG_ID,
    constants.DYTE_APP_ID
)

dyte_service_v2 = DyteServiceV2(
    constants.DYTE_ORG_ID,
    constants.DYTE_APP_ID
)

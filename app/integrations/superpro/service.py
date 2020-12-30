import requests
from json import JSONDecodeError

from integrations.superpro import constants


VIDEO_CALL_CREATE = "video_call_create"


class SuperProService:

    API_ENDPOINTS = {
        VIDEO_CALL_CREATE: "/videocallstart",
    }

    def __init__(self, access_token,):
        self.access_token = access_token

    def _get_authorization_headers(self):
        """Create authorization headers for FreshChat services."""
        return {
            "Accept": "application/json",
            "Authorization": "Bearer {}".format(
                self.access_token
            ),
            "Content-Type": "application/json"
        }

    def create_video_call(self, users):
        data = {
            constants.USER_ADD_KEY: []
        }

        for user in users:
            data[constants.USER_ADD_KEY].append(
                {
                    "name": user.get_display_first_name(),
                    "email": user.email,
                    "role": constants.DEFAULT_MEETING_ROLE
                }
            )

        response = requests.post(
            url=constants.SUPERPRO_BASE_URL + self.API_ENDPOINTS[VIDEO_CALL_CREATE],
            headers=self._get_authorization_headers(),
            json=data
        )
        try:
            response_json = response.json()
        except JSONDecodeError:
            response_json = {}

        return response_json.get(constants.VIDEO_CALL_ID_RESPONSE_KEY), response_json.get(constants.VIDEO_CALL_URI_RESPONSE_KEY)



# This is actual production service. It will create actual
# URI's for video calls.
superpro_service = SuperProService(
    access_token=constants.SUPERPRO_ACCESS_TOKEN,
)

import json

import requests
import sentry_sdk

from integrations.freshchat import constants
from integrations.freshchat import utils

GET_OUTBOUND_MESSAGE_ENDPOINT = "get_outbound_message"
SEND_OUTBOUND_MESSAGE_ENDPOINT = "send_outbound_message"
CREATE_USER_ENDPOINT = "create_user"
UPDATE_USER_ENDPOINT = "update_user"
GET_USER_ENDPOINT = "get_user"


class FreshChatWhatsappService:

    API_ENDPOINTS = {
        GET_OUTBOUND_MESSAGE_ENDPOINT: "/outbound-messages?request_id={request_id}",
        SEND_OUTBOUND_MESSAGE_ENDPOINT: "/outbound-messages/whatsapp",
        CREATE_USER_ENDPOINT: "/users",
        UPDATE_USER_ENDPOINT: "/users/{user_id}",
        GET_USER_ENDPOINT: "/users/{user_id}"
    }

    def __init__(self, app_id, access_token, namespace, from_phone_number, provider):
        self.app_id = app_id
        self.access_token = access_token
        self.namespace = namespace
        self.from_phone_number = from_phone_number
        self.provider = provider

    def _get_authorization_headers(self):
        """Create authorization headers for FreshChat services."""
        return {
            "Accept": "application/json",
            "Authorization": "Bearer {}".format(
                self.access_token
            ),
            "Content-Type": "application/json"
        }

    @staticmethod
    def _get_default_language_header():
        """Returns default language header for Freshchat Service."""
        return {
            "policy": "deterministic",
            "code": "en_US"
        }

    @staticmethod
    def _get_default_rich_template_data():
        return {"header": {"type": "", "media_url": ""}, "body": {"params": [{"data": ""}]}}

    def get_users(self, user_id):
        """Get freshchat users."""
        response = requests.get(
            url=constants.FRESHCHAT_BASE_URL + self.API_ENDPOINTS[GET_USER_ENDPOINT].format(user_id=user_id),
            headers=self._get_authorization_headers(),
            data={}
        )
        return response

    def create_or_update_user(self, user):
        """Creates a user entity on Freshchat.

        Args:
            user(User): User object on our end.

        Returns:
            freshchat_user(FreshChatsUser): Created/Update FreshChatUser object

        """
        data = {
            "email": user.email,
            "first_name": user.name,
            "last_name": "",
            "avatar": {
                "url": user.profile.get_photo_url()
            },
            "phone": user.get_phone_number(),
            "properties": [
                {"name": "linkedin", "value": user.profile.linkedin_url or ""}
            ]
        }

        freshchat_user = utils.get_freshchat_user(user)

        if freshchat_user:
            response = requests.put(
                url=constants.FRESHCHAT_BASE_URL + self.API_ENDPOINTS[UPDATE_USER_ENDPOINT].format(
                    user_id=freshchat_user.freshchat_user_id
                ),
                headers=self._get_authorization_headers(),
                json=data
            )
        else:
            response = requests.post(
                url=constants.FRESHCHAT_BASE_URL + self.API_ENDPOINTS[CREATE_USER_ENDPOINT],
                headers=self._get_authorization_headers(),
                json=data
            )

        if response.status_code == 201:
            response_json = response.json()
            freshchat_user = utils.create_or_update_freshchat_user(user, response_json.get('id'))
        elif response.status_code == 202:
            pass
        else:
            sentry_sdk.capture_message(
                "FreshChat Create User Failed with {}".format(response.status_code),
                level="error",
                email=user.email
            )

        return response, freshchat_user

    def get_outbound_messages(self, request_id):
        """Get outbound messages for a given request_id.

        Args:
            request_id(str): Request ID returned after an outbound message is
                send successfully.
        """
        response = requests.get(
            url=constants.FRESHCHAT_BASE_URL + self.API_ENDPOINTS[GET_OUTBOUND_MESSAGE_ENDPOINT].format(
                request_id=request_id
            ),
            headers=self._get_authorization_headers(),
            json={}
        )
        return response

    def send_outbound_message(
            self,
            user,
            template_name,
            template_data,
            rich_template_data=None
    ):
        """Sends an outbound message through Freshchat for whatsapp.

        Args:
            user(User): User's on our App.
            template_name(str): Template name as exists on Whatsapp.
            template_data(list(dict)): List of dicts, containing context
                for the template.
            rich_template_data(list(dict)): List of dicts, containing media
                for the template.

        Returns:
            Response object

        """

        data = {
            "from": {"phone_number": self.from_phone_number},
            "to": {"phone_number": user.get_phone_number()},
            "provider": self.provider,
            "data": {
                "message_template": {
                    "template_name": template_name,
                    "namespace": self.namespace,
                    "language": self._get_default_language_header(),
                    "template_data": template_data,
                    "rich_template_data": rich_template_data
                    if rich_template_data else self._get_default_rich_template_data()
                }
            }
        }

        response = requests.post(
            url=constants.FRESHCHAT_BASE_URL + self.API_ENDPOINTS[SEND_OUTBOUND_MESSAGE_ENDPOINT],
            headers=self._get_authorization_headers(),
            json=data
        )

        return response


# Use this service for sending message through FreshChat to Whatsapp.
freshchat_whatsapp_service = FreshChatWhatsappService(
    app_id=constants.FRESHCHAT_APP_ID,
    access_token=constants.FRESHCHAT_ACCESS_TOKEN,
    namespace=constants.FRESHCHAT_WHATSAPP_NAMESPACE,
    from_phone_number=constants.FRESHCHAT_MESSAGING_PHONE_NUMBER,
    provider=constants.FRESHCHAT_DEFAULT_PROVIDER
)

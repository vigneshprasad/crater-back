import requests

from intergrations.freshchat import constants
from intergrations.freshchat import utils


class FreshChatWhatsappService:

    API_ENDPOINTS = {
        "outbound_message_endpoint": "/outbound-messages/whatsapp",
        "user_creation_endpoint": "/users",
        "user_updation_endpoint": "/users/{user_id}"
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
            "avatar": {
                "url": user.profile.get_photo_url()
            },
            "phone": user.get_phone_number(),
            "properties": {}
        }

        freshchat_user = utils.get_freshchat_user(user)

        if freshchat_user:
            response = requests.put(
                url=constants.FRESHCHAT_BASE_URL + self.API_ENDPOINTS["user_updation_endpoint"].format(
                    freshchat_user.freshchat_user_id
                ),
                headers=self._get_authorization_headers(),
                data=data
            )
        else:
            response = requests.post(
                url=constants.FRESHCHAT_BASE_URL + self.API_ENDPOINTS["user_creation_endpoint"],
                headers=self._get_authorization_headers(),
                data=data
            )

        response_json = response.json()
        freshchat_user = utils.create_or_update_freshchat_user(user, response_json.get('user_id'))

        return freshchat_user

    def get_agents(self):
        response = requests.get(
            url=constants.FRESHCHAT_BASE_URL + "/agents",
            headers=self._get_authorization_headers()
        )
        print("Status", response.status_code)
        print("Response Content", response.json())
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
                    "rich_template_data": rich_template_data if rich_template_data else {"body": {"params": []}}
                }
            }
        }

        response = requests.post(
            url=constants.FRESHCHAT_BASE_URL + self.API_ENDPOINTS["outbound_message_endpoint"],
            headers=self._get_authorization_headers(),
            data=data
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

import requests

from intergrations.freshchat import constants


class FreshChatWhatsappService:

    def __init__(self, app_id, access_token, namespace, from_phone_number, provider):
        self.app_id = app_id
        self.access_token = access_token
        self.namespace = namespace
        self.from_phone_number = from_phone_number
        self.provider = provider

    def _get_authorization_headers(self):
        return {
            "Accept": "application/json",
            "Authorization": "Bearer {}".format(
                self.access_token
            ),
            "Content-Type": "application/json"
        }

    @staticmethod
    def _get_default_language_header():
        return {
            "policy": "deterministic",
            "code": "en_US"
        }

    def get_agents(self):
        response = requests.get(
            url=constants.FRESHCHAT_BASE_URL + "/agents",
            headers=self._get_authorization_headers()
        )
        print("Status", response.status_code)
        print("Response Content", response.json())
        return response

    def send_meeting_reminder_outbound_message_to_user(self, user, time):
        """Sends outbound meeting reminder to the user."""
        template_name = constants.MEETING_REMINDER_FRESHCHAT_TEMPLATE
        message_data = {
            "message_template": {
                "template_name": template_name,
                "namespace": self.namespace,
                "language": self._get_default_language_header(),
                "template_data": [
                    {
                        "data": time
                    }
                ],
                "rich_template_data": {
                    "body": {"params": []}
                }
            }
        }
        template_data = {
            "from": {
                "phone_number": self.from_phone_number
            },
            "to": {
                "phone_number": user.get_phone_number()
            },
            "provider": self.provider,
            "data": message_data
        }

        response = requests.post(
            url=constants.FRESHCHAT_BASE_URL + constants.API_ENDPOINTS["outbound_message_endpoint"],
            headers=self._get_authorization_headers(),
            data=template_data
        )

        print("Status", response.status_code)
        print("Response Content", response.json())
        return response

    def create_user(self, user):
        """Creates a user entity on Freshchat

        Args:
            user(User): User object on our end.

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
        response = requests.post(
            url=constants.FRESHCHAT_BASE_URL + constants.API_ENDPOINTS["user_creation_endpoint"],
            headers=self._get_authorization_headers(),
            data=data
        )

        print("Status", response.status_code)
        print("Response Content", response.json())
        return response


freshchat_whatsapp_service = FreshChatWhatsappService(
    app_id=constants.FRESHCHAT_APP_ID,
    access_token=constants.FRESHCHAT_ACCESS_TOKEN,
    namespace=constants.FRESHCHAT_NAMESPACE,
    from_phone_number=constants.FRESHCHAT_MESSAGING_PHONE_NUMBER,
    provider=constants.FRESHCHAT_DEFAULT_PROVIDER
)

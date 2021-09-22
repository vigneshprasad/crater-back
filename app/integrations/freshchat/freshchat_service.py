import logging

import requests
from json import JSONDecodeError

from celery import shared_task
from django.conf import settings
from django.contrib.auth import get_user_model

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
            "code": "en"
        }

    @staticmethod
    def _can_create_user(user):
        """Checks if we can create the user on FreshChat based
            on the data we have on our side for the User.

        Args:
            user(User): User object being created on Freshchat.

        """
        if not user.has_profile:
            return False

        if not user.get_phone_number():
            return False

        return True

    @staticmethod
    def _can_send_message_to_user(user):
        """Checks if we can send messages to User based
            on the data provided by the user.

        Args:
            user(User): User we are sending messages to.

        """
        if not user.has_profile:
            logging.error("Message not sent for {}. No profile".format(
                user.email
            ))
            return False

        if not user.get_phone_number():
            logging.error("Message not sent for {}. No Phone Number".format(
                user.email
            ))
            return False

        if not user.profile.opted_in_for_whatsapp:
            return False

        return True

    def get_user_details(self, user):
        """Get user details on Freshchat.

        Args:
            user(User): User object on our side.

        Returns:
            Response JSON if available.

        """
        freshchat_user = utils.get_freshchat_user(user)
        if freshchat_user and freshchat_user.freshchat_user_id:
            response = requests.get(
                url=constants.FRESHCHAT_BASE_URL + self.API_ENDPOINTS[GET_USER_ENDPOINT].format(
                    user_id=freshchat_user.freshchat_user_id
                ),
                headers=self._get_authorization_headers(),
                data={}
            )
        else:
            return {"message": "User not available on Freshchat"}

        return response.json()

    def create_or_update_user(self, user):
        """Creates or updates a user entity on Freshchat.

        Args:
            user(User): User object on our end.

        """
        # Added a Test {name} for testing environments.
        first_name = "Test {}".format(user.name) \
            if settings.ENVIRONMENT == settings.ENVIRONMENT_PREPROD else user.name

        if not self._can_create_user(user):
            return False

        data = {
            "email": user.email,
            "first_name": first_name,
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

        if freshchat_user and freshchat_user.freshchat_user_id:
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

        try:
            response_json = response.json()
        except JSONDecodeError:
            response_json = {}

        freshchat_user_id = response_json.get('id')

        if response.status_code == constants.FRESHCHAT_STATUS_CREATED:
            utils.create_or_update_freshchat_user(
                user,
                freshchat_user_id
            )
        elif response.status_code == constants.FRESHCHAT_STATUS_ACCEPTED:
            pass
            # If the status is Accepted, we don't get any response from
            # FreshChat. Not updating anything here.
        else:
            logging.error(
                "FreshChat Create/Update User Failed for {}".format(
                    user.email
                ),
                extra={
                    "status_code": response.status_code,
                }
            )
            return False

        return True

    def get_outbound_message(self, request_id):
        """Gets a single outbound message for a given request_id.

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
        if response.status_code == constants.FRESHCHAT_STATUS_SUCCESS:
            try:
                response_json = response.json()
                response_json = response_json.get('outbound_messages')[0]
            except (JSONDecodeError, IndexError):
                response_json = {}
        else:
            logging.error(
                "FreshChat Get Outbound Message Failed for {}".format(
                    request_id
                ),
                extra={
                    "status_code": response.status_code,
                }
            )
            response_json = {}

        return response_json

    def send_outbound_message(
            self,
            user,
            template_name,
            template_data,
            rich_template_data=None
    ):
        """Sends a single outbound message through Freshchat for whatsapp.

        Args:
            user(User): User's on our App.
            template_name(str): Template name as exists on Whatsapp.
            template_data(list(dict)): List of dicts, containing context
                for the template.
            rich_template_data(list(dict)): List of dicts, containing media
                for the template.

        Returns:
            Response object.

        """

        if not self._can_send_message_to_user(user):
            return False

        data = {
            "from": {"phone_number": self.from_phone_number},
            "to": [{"phone_number": user.get_phone_number()}],
            "provider": self.provider,
            "data": {
                "message_template": {
                    "storage": "none",
                    "template_name": template_name,
                    "namespace": self.namespace,
                    "language": self._get_default_language_header(),
                    "template_data": template_data,
                }
            }
        }

        if rich_template_data:
            data["data"]["message_template"] = rich_template_data

        response = requests.post(
            url=constants.FRESHCHAT_BASE_URL + self.API_ENDPOINTS[SEND_OUTBOUND_MESSAGE_ENDPOINT],
            headers=self._get_authorization_headers(),
            json=data
        )

        try:
            response_json = response.json()
        except JSONDecodeError:
            response_json = {}

        request_id = response_json.get('request_id')

        if response.status_code == constants.FRESHCHAT_STATUS_ACCEPTED:
            # Doing a delayed call for get_outbound_message and creating Message object.
            _get_and_process_outbound_message_after_delay.apply_async(
                args=(user.pk, request_id,),
                countdown=60
            )
        else:
            logging.error(
                "FreshChat Post Outbound Message Failed for {}".format(
                    user.email
                ),
                extra={
                    "status_code": response.status_code,
                }
            )
            return False

        return True


# Use this service for sending message through FreshChat to Whatsapp.
freshchat_whatsapp_service = FreshChatWhatsappService(
    app_id=constants.FRESHCHAT_APP_ID,
    access_token=constants.FRESHCHAT_ACCESS_TOKEN,
    namespace=constants.FRESHCHAT_WHATSAPP_NAMESPACE,
    from_phone_number=constants.FRESHCHAT_MESSAGING_PHONE_NUMBER,
    provider=constants.FRESHCHAT_DEFAULT_PROVIDER
)


# ------ Private Functions ------ #
@shared_task
def _get_and_process_outbound_message_after_delay(user_pk, request_id):
    if not (user_pk and request_id):
        return False
    user = get_user_model().objects.get(pk=user_pk)
    get_response_json = freshchat_whatsapp_service.get_outbound_message(
        request_id=request_id
    )
    status = get_response_json.get('status')
    message_id = get_response_json.get('message_id')
    utils.create_message(
        user,
        status,
        message_id,
        request_id,
        data=get_response_json,
    )

import logging

import requests
from django.conf import settings

LOGGER = logging.getLogger(__name__)

GET_MESSAGE_FOR_WHATSAPP_NUMBER = "get_messages_by_whatsapp_number"
SEND_TEMPLATE_MESSAGE = "send_template_message"
SEND_TEMPLATE_MESSAGES = "send_template_messages"
ADD_CONTACT_ENDPOINT = "add_contact"
UPDATE_CONTACT_ATTRIBUTE_ENDPOINT = "update_attribute_endpoint"
GET_CONTACTS = "get_contacts"


class WatiWhatsappService:

    API_ENDPOINTS = {
        # Contact endpoints.
        ADD_CONTACT_ENDPOINT: "addContact/{whatsappNumber}",
        UPDATE_CONTACT_ATTRIBUTE_ENDPOINT: "updateContactAttributes/{whatsappNumber}",
        GET_CONTACTS: "getContacts",

        # Template messages endpoints.
        GET_MESSAGE_FOR_WHATSAPP_NUMBER: "getMessages/{whatsappNumber}",
        SEND_TEMPLATE_MESSAGE: "sendTemplateMessage?whatsappNumber={}",
        SEND_TEMPLATE_MESSAGES: "sendTemplateMessages"
    }

    def __init__(self, access_token, base_url):
        self.base_url = base_url
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

    def get_messages(self, user):
        """Get messages for a user from WATI.

        Args:
            user(User): User we are getting whatsapp
                message for.

        """
        response = requests.request(
            "GET",
            url=self.base_url + self.API_ENDPOINTS[GET_MESSAGE_FOR_WHATSAPP_NUMBER].format(
                whatsappNumber=user.get_phone_number()
            ),
            headers=self._get_authorization_headers()
        )
        print(response.text)
        return True

    def send_template_message(
            self,
            user,
            template_name,
            template_data,
            broadcast_name=None,
    ):
        data = {
            "template_name": template_name,
            "broadcast_name": broadcast_name if broadcast_name else template_name,
            "parameters": template_data
        }

        response = requests.request(
            "POST",
            url=self.base_url + self.API_ENDPOINTS[SEND_TEMPLATE_MESSAGE].format(
                user.get_phone_number()
            ),
            headers=self._get_authorization_headers(),
            json=data
        )
        print(response.text)
        return True

    def send_template_messages(
            self,
            receivers,
            template_name,
            broadcast_name=None,
    ):
        data = {
            "template_name": template_name,
            "broadcast_name": broadcast_name if broadcast_name else template_name,
            "receivers": receivers,
        }

        response = requests.request(
            "POST",
            url=self.base_url + self.API_ENDPOINTS[SEND_TEMPLATE_MESSAGES],
            headers=self._get_authorization_headers(),
            json=data
        )
        print(response.text)
        return True


wati_service_9051 = WatiWhatsappService(
    base_url=settings.WATI_9051_BASE_URL,
    access_token=settings.WATI_9051_ACCESS_TOKEN
)


wati_service_8953 = WatiWhatsappService(
    base_url=settings.WATI_8953_BASE_URL,
    access_token=settings.WATI_8953_ACCESS_TOKEN
)

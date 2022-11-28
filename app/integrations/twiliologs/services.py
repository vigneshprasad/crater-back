import logging
import requests

from django.conf import settings
from twilio.base import exceptions
from twilio.rest import Client

from integrations.twiliologs import constants


class TwilioService:
    """Service for sending message from Twilio."""

    def __init__(self, account_sid, auth_token):
        self._account_sid = account_sid
        self._auth_token = auth_token
        self.client = self._get_client()
        self.from_number = settings.DEFAULT_SMS_PHONE_NUMBER

    def _get_client(self):
        """Get Twilio client for server."""
        return Client(self._account_sid, self._auth_token)

    @staticmethod
    def _can_send_message():
        """Checks based on environment if SMS sending is
            allowed or not.

        """
        return settings.ALLOW_MESSAGE_SENDING

    def send_message(self, phone_number, body):
        """Sends message through outbound API to a
            phone number.

        """
        if not self._can_send_message():
            return

        try:
            message = self.client.messages.create(
                to=phone_number,
                from_=self.from_number,
                body=body,
                status_callback=constants.SMS_CALLBACK_URL
            )
        except exceptions.TwilioRestException as e:
            error_dict = e.__dict__
            message_data = {
                "sid": None,
                "error_code": error_dict["code"],
                "error_message": error_dict["msg"],
                "status": constants.SMS_STATUS_FAILED
            }
            return message_data
        except requests.exceptions.ConnectionError as e:
            logging.error(str(e))
            return

        message_data = message._properties
        return message_data


twilio_service = TwilioService(
    settings.TWILIO_ACCOUNT_SID,
    settings.TWILIO_AUTH_TOKEN
)

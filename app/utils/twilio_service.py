from django.conf import settings
from twilio.rest import Client
from twilio.base import exceptions


class TwilioService:
    """Service for sending message from Twilio."""

    def __init__(self, account_sid, auth_token):
        self._account_sid = account_sid
        self._auth_token = auth_token
        self.client = self._get_client()
        self.from_number = settings.DEFAULT_SMS_PHONE_NUMBER

    def _get_client(self):
        return Client(self._account_sid, self._auth_token)

    @staticmethod
    def _can_send_message():
        return settings.ALLOW_MESSAGE_SENDING

    def send_message(self, phone_number, body):
        if not self._can_send_message():
            return

        try:
            message = self.client.messages.create(
                to=phone_number,
                from_=self.from_number,
                body=body
            )
        except exceptions.TwilioRestException:
            return

        return message.sid


twilio_service = TwilioService(
    settings.TWILIO_ACCOUNT_SID,
    settings.TWILIO_AUTH_TOKEN
)

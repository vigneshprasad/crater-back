from twilio.rest import Client
from django.conf import settings


class TwilioService:
    """Service for sending message from Twilio."""

    def __init__(self, account_sid, auth_token):
        self._account_sid = account_sid
        self._auth_token = auth_token
        self.client = self._get_client()
        self.from_number = settings.DEFAULT_SMS_PHONE_NUMBER

    def _get_client(self):
        return Client(self._account_sid, self._auth_token)

    def send_message(self, phone_number, body):
        message = self.client.messages.create(
            to=phone_number,
            from_=self.from_number,
            body=body
        )
        return message.sid


twilio_service = TwilioService(
    settings.TWILIO_ACCOUNT_SID,
    settings.TWILIO_AUTH_TOKEN
)

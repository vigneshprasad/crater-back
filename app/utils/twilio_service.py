from twilio.rest import Client
from django.conf import settings


class TwilioService:

    def __init__(self, account_sid, auth_token):
        self._account_sid = account_sid
        self._auth_token = auth_token
        self.client = Client(account_sid, auth_token)
        self.from_number = settings.DEFAULT_SMS_PHONE_NUMBER

    def send_message(self, phone_number, body="SMS from go beauty"):
        return self.client.messages.create(
            to=phone_number,
            from_=self.from_number,
            body=body
        )


twilio_service = TwilioService(
    settings.TWILIO_ACCOUNT_SID,
    settings.TWILIO_AUTH_TOKEN
)

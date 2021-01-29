import string

from django.conf import settings

APP_ID = settings.AGORA_APP_ID
APP_CERTIFICATE = settings.AGORA_APP_CERTIFICATE

ROLE_ATTENDEE = 0
ROLE_PUBLISHER = 1
ROLE_SUBSCRIBER = 2
ROLE_ADMIN = 101

DEFAULT_EXPIRY_TIME = 43200

ALLOWED_CHARACTERS_FOR_CHANNEL_ID = string.printable.replace(string.whitespace[1:], "")

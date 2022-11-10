import logging

from django.conf import settings
from django.contrib.auth.models import Group

from crater.auth import constants as auth_constants

LOGGER = logging.getLogger(__name__)


def can_send_whatsapp_for_user(user):
    """Checks if whatsapp is allowed for the user.

    Args:
        user(User): User we want to send whatsapp to.

    """
    if not settings.ALLOW_WHATSAPP_SENDING:
        return False

    if not user.get_phone_number():
        LOGGER.error(
            "Message not sent for {}. No Phone Number".format(
                user.__str__()
            )
        )
        return False

    if not user.has_profile:
        return True

    if not user.profile.opted_in_for_whatsapp:
        return False

    return True

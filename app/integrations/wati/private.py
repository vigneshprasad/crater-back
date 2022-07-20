import logging

from django.conf import settings


LOGGER = logging.getLogger(__name__)


def can_send_whatsapp_for_user(user):
    """Checks if whatsapp is allowed for the user.

    Args:
        user(User): User we want to send whatsapp to.

    """
    print(settings.ALLOW_WHATSAPP_SENDING)
    if not settings.ALLOW_WHATSAPP_SENDING:
        return False

    print(user.get_phone_number())
    if not user.get_phone_number():
        LOGGER.error(
            "Message not sent for {}. No Phone Number".format(
                user.__str__()
            )
        )
        return False

    print(user.has_profile)
    if not user.has_profile:
        return True

    print(user.profile.opted_in_for_whatsapp)
    if not user.profile.opted_in_for_whatsapp:
        return False

    return True

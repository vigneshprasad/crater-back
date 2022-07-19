import logging
from django.dispatch import receiver

from users import signals as user_signals
from integrations.onesignal import models


@receiver(user_signals.user_logout)
def delete_onesignal_device(sender, user, os_id, *args, **kwargs):
    """Deletes one signal device on logout.

    Args:
        sender(class): Sender class for serializer.
        user(User): User that performed the logout.
        os_id(str): OS ID for the device.

    """
    if not os_id:
        return

    try:
        device = models.OneSignalDevice.objects.get(
            user=user,
            os_id=os_id,
        )
    except models.OneSignalDevice.DoesNotExist:
        logging.info("OneSignal Device not found: {}".format(os_id))
        return

    # Delete the device on logout.
    device.delete()

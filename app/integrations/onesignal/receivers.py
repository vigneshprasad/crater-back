import logging
from django.dispatch import receiver

from users import signals as user_signals
from integrations.onesignal import models


@receiver(user_signals.user_logout)
def delete_onesignal_device(sender, instance, user, os_id, *args, **kwargs):
    try:
        device = models.OneSignalDevice.objects.get(
            user=user,
            os_id=os_id,
        )
        device.delete()

    except models.OneSignalDevice.DoesNotExist:
        logging.log("OneSignal Device not found")

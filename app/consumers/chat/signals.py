from django.contrib.auth import get_user_model
from django.db.models.signals import post_save
from django.dispatch import receiver, Signal

from consumers.chat.helpers import MessageHelper
from consumers.chat.models import Message
from consumers.chat.tasks import read_admin_messages_for_user


@receiver(post_save, sender=Message)
def send_messages(sender, instance, **kwargs):
    if instance.is_support:
        admins = get_user_model().objects.filter(is_staff=True, is_active=True)
        if instance.receiver:
            MessageHelper.send_admin_message_to_user(admins, instance)
            read_admin_messages_for_user.delay(uuid=instance.receiver.pk)
        else:
            MessageHelper.send_user_message_to_admin(admins, instance)
    else:
        MessageHelper.send_user_message_to_user(instance)


new_chat_points_signal = Signal(providing_args=[
    "user",
    "rule_key",
    "base_factor"
])
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Message
from .signals import new_chat_points_signal

NEW_CHAT_POINTS_KEY = 10

@receiver(post_save, sender=Message)
def send_new_chat_signal(sender, instance, created, *args, **kwargs):
  if created:
    message_sender = instance.sender
    message_reciever = instance.receiver
    is_new_chat = Message.objects.filter(sender=message_sender, receiver=message_reciever)
    if len(is_new_chat) == 1:
      new_chat_points_signal.send(
        sender=instance.__class__,
        user=message_sender,
        rule_key=NEW_CHAT_POINTS_KEY
      )
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Message, MessageEmailNotification
from .signals import new_chat_points_signal, create_chat_for_meeting
from .choices import MESSAGE_EMAIL_NOTIFICATION_STATE

NEW_CHAT_POINTS_KEY = 10


@receiver(post_save, sender=Message)
def send_new_chat_signal(sender, instance, created, *args, **kwargs):
    if not created:
        return

    message_sender = instance.sender
    message_receiver = instance.receiver
    is_new_chat = Message.objects.filter(sender=message_sender, receiver=message_receiver)

    MessageEmailNotification.objects.create(
        sender=message_sender,
        message=instance,
        receiver=message_receiver,
        state=MESSAGE_EMAIL_NOTIFICATION_STATE[0]
    )

    if not len(is_new_chat) == 1:
        return

    new_chat_points_signal.send(
        sender=instance.__class__,
        user=message_sender,
        rule_key=NEW_CHAT_POINTS_KEY
    )


@receiver(create_chat_for_meeting)
def create_chat_messages_for_meeting(sender, participants, *args, **kwargs):
    if len(participants) <= 1:
        return
    for message_sender in participants:
        if not (message_sender.has_profile and message_sender.profile.get_introduction()):
            continue

        for message_receiver in participants:
            if message_sender == message_receiver:
                continue
            content = "(Automated message): Hi {}, here is a quick introduction about me".format(message_receiver.name)
            Message.objects.create(
                message=content,
                sender=message_sender,
                receiver=message_receiver,
                is_support=False,
            )

            intro_content = "(Automated message): {}".format(message_sender.profile.get_introduction())
            Message.objects.create(
                message=intro_content,
                sender=message_sender,
                receiver=message_receiver,
                is_support=False,
            )


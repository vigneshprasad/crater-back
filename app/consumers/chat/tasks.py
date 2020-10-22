from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

from django.contrib.auth import get_user_model
from consumers.chat.models import Message, MessageEmailNotification
from .choices import MESSAGE_EMAIL_NOTIFICATION_STATE, CHAT_EMAIL_TEMPLATE, MESSAGE_NOTIFICATION_FROM_EMAIL
from freelance.celery import app
from freelance.settings import FRONT_URL
from celery import shared_task


@app.task
def read_admin_messages_for_user(uuid):
    messages = Message.objects.filter(sender=uuid, is_support=True, is_read=False)
    if messages:
        messages_ids = list(messages.values_list('pk', flat=True))
        messages.update(is_read=True)
        layer = get_channel_layer()
        async_to_sync(layer.group_send)(uuid, {
            'type': 'admin_read_messages_to_user',
            'messages': messages_ids,
            'user_id': uuid
        })


@shared_task(bind=True, name='send_email_for_unread_messages')
def send_email_for_unread_messages(self):
    notifications = MessageEmailNotification.objects.filter(state=MESSAGE_EMAIL_NOTIFICATION_STATE[0])
    if not notifications:
        return

    receivers = set(notifications.values_list('receiver', flat=True))

    for receiver in receivers:
        user_receiver = get_user_model().objects.get(pk=receiver)
        senders = set(notifications.filter(receiver=receiver).values_list('sender', flat=True))
        for sender in senders:
            user_sender = get_user_model().objects.get(pk=sender)
            subject = 'New Message from {}'.format(user_sender.name)
            notifications_to_send = notifications.filter(sender=sender, receiver=receiver)
            unread_count = len(notifications_to_send)
            user_receiver.send_email(
                subject=subject,
                to=[user_receiver.email],
                template_name=CHAT_EMAIL_TEMPLATE,
                content={},
                from_email=MESSAGE_NOTIFICATION_FROM_EMAIL,
                merge_vars={
                    user_receiver.email: {
                        'name': user_sender.name,
                        'unread_count': unread_count,
                        'introduction': user_sender.profile.get_introduction(),
                        'chat_link': 'https://{}/dashboard/inbox?active={}'.format(FRONT_URL, user_sender.pk),
                        'profile_link': 'https://{}/profile?p={}'.format(FRONT_URL, user_sender.pk),
                        'contact_us': 'https://{}/dashboard/help'.format(FRONT_URL),
                        'website_url': 'https://{}'.format(FRONT_URL)
                    }
                }
            )
            notifications_to_send.update(state=MESSAGE_EMAIL_NOTIFICATION_STATE[3])


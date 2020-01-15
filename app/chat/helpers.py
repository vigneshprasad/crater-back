from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

from chat.models import Message


class MessageHelper:
    @staticmethod
    def send_user_message_to_admin(admins, message):
        for admin in admins:
            layer = get_channel_layer()
            async_to_sync(layer.group_send)(str(admin.uuid), {
                'type': 'user_message_to_admin',
                'message': message.message,
                'created': message.created.strftime("%d %b, %H:%M"),
                'name': message.sender.name,
                'sender_id': str(message.sender.pk)
            })
            async_to_sync(layer.group_send)(str(admin.uuid), {
                'type': 'admin_user_notifications',
                'sender_id': str(message.sender.pk),
                'message': Message.objects.filter(sender=message.sender, is_support=True, is_read=False).last().message,
                'unread_count': Message.objects.filter(sender=message.sender, is_support=True, is_read=False).count()
            })

    @staticmethod
    def send_admin_message_to_user(admins, message):
        for admin in admins:
            layer = get_channel_layer()
            async_to_sync(layer.group_send)(str(admin.uuid), {
                'type': 'admin_message_to_user',
                'message': message.message,
                'created': message.created.strftime("%d %b %H:%M"),
                'name': message.sender.name,
                'receiver_id': str(message.receiver.pk)
            })

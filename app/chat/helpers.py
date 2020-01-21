from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.contrib.auth import get_user_model

from chat.models import Message


class MessageHelper:
    @classmethod
    def send_user_message_to_admin(cls, admins, message):
        """
        Sends messages and notifications to admins, message back to user
        :param admins: queryset of admins
        :param message: message string
        """
        layer = get_channel_layer()
        for admin in admins:
            message_fmt = cls._get_user_message_data_format(message, 'user_message_to_admin')
            async_to_sync(layer.group_send)(str(admin.uuid), message_fmt)
            _message = Message.objects.filter(sender=message.sender, is_support=True, is_read=False).last()
            notification_fmt = cls._get_user_message_data_format(_message, 'admin_user_notifications')
            notification_fmt['unread_count'] = Message.objects.filter(
                sender=message.sender, is_support=True, is_read=False
            ).count()
            async_to_sync(layer.group_send)(str(admin.uuid), notification_fmt)
        message_fmt = cls._get_user_message_data_format(message, 'user_message_to_admin')
        async_to_sync(layer.group_send)(str(message.sender.uuid), message_fmt)

    @classmethod
    def send_admin_message_to_user(cls, admins, message):
        """
        Sends message to user, message back to admin
        :param admins: queryset of admins
        :param message: message string
        """
        layer = get_channel_layer()
        message_fmt = cls._get_user_message_data_format(message, 'admin_message_to_user')
        for admin in admins:
            async_to_sync(layer.group_send)(str(admin.uuid), message_fmt)
        async_to_sync(layer.group_send)(str(message.receiver.uuid), message_fmt)

    @classmethod
    def send_read_messages_to_admin(cls, messages, user):
        """
        Send list of read message ids to admins
        :param messages: message ids
        :param user: user who read messages
        """
        admins = get_user_model().objects.filter(is_staff=True, is_active=True)
        layer = get_channel_layer()
        message_fmt = {
            'type': 'user_read_messages_to_admin',
            'messages': messages,
            'receiver_id': user
        }
        for admin in admins:
            async_to_sync(layer.group_send)(str(admin.uuid), message_fmt)

    @staticmethod
    def _get_user_message_data_format(message, _type):
        """
        Common message format for sending data in sockets (event)
        :param message: message instance from database
        :param _type: method which will be called on consumer
        :return: prepared data dictionary
        """
        return {
            'type': _type,
            'message': message.message,
            'file': message.file.url if message.file else None,
            'message_id': message.pk,
            'created': message.created.strftime("%d %b, %H:%M"),
            'sender': message.sender.name,
            'sender_id': str(message.sender.pk),
            'receiver': message.receiver.name if message.receiver else None,
            'receiver_id': str(message.receiver.pk) if message.receiver else None
        }

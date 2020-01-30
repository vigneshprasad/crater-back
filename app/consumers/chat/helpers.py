import mimetypes

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.conf import settings
from django.contrib.auth import get_user_model
from pytz import timezone
from consumers.chat.models import Message

tz = timezone(settings.TIME_ZONE)


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
            notification_fmt = cls._get_user_message_data_format(_message, 'user_notifications')
            notification_fmt['unread_count'] = Message.objects.filter(
                sender=message.sender, is_support=True, is_read=False
            ).count()
            async_to_sync(layer.group_send)(str(admin.uuid), notification_fmt)
        if message.sender not in admins:
            message_fmt = cls._get_user_message_data_format(message, 'user_message_to_admin')
            async_to_sync(layer.group_send)(str(message.sender.uuid), message_fmt)

    @classmethod
    def send_admin_message_to_user(cls, admins, message):
        """
        Sends message to user, message back to admin
        :param admins: queryset of admins
        :param message: message instance
        """
        layer = get_channel_layer()
        message_fmt = cls._get_user_message_data_format(message, 'admin_message_to_user')
        for admin in admins:
            async_to_sync(layer.group_send)(str(admin.uuid), message_fmt)
        async_to_sync(layer.group_send)(str(message.receiver.uuid), message_fmt)

    @classmethod
    def send_user_message_to_user(cls, message):
        """
        Sends message to user, message back to admin
        :param message: message instance
        """
        layer = get_channel_layer()
        message_fmt = cls._get_user_message_data_format(message, 'user_message_to_user')
        message_fmt['created'] = str(message.created.astimezone(tz).strftime('%Y-%m-%dT%H:%M:%S.%f+05:30'))
        async_to_sync(layer.group_send)(str(message.sender.uuid), message_fmt)
        async_to_sync(layer.group_send)(str(message.receiver.uuid), message_fmt)

        for user_id in cls._get_user_ids(message.receiver.pk):
            _message = Message.objects.filter(sender=message.sender, is_support=False).last()
            notification_fmt = cls._get_user_message_data_format(_message, 'user_notifications')
            notification_fmt['unread_count'] = Message.objects.filter(
                sender=message.sender, receiver=message.receiver, is_support=False, is_read=False
            ).count()
            async_to_sync(layer.group_send)(str(user_id), notification_fmt)

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

    @classmethod
    def _get_user_message_data_format(cls, message, _type):
        """
        Common message format for sending data in sockets (event)
        :param message: message instance from database
        :param _type: method which will be called on consumer
        :return: prepared data dictionary
        """
        return {
            'type': _type,
            'is_read': message.is_read,
            'message': message.message,
            'file': message.file.url if message.file else None,
            'file_format': mimetypes.guess_type(message.file.name)[0] if message.file else None,
            'message_id': message.pk,
            'created': message.created.strftime("%d %b, %H:%M"),
            'sender': message.sender.name,
            'sender_photo': message.sender.profile.photo.url if cls._has_profile_photo(message) else None,
            'sender_id': str(message.sender.pk),
            'receiver': message.receiver.name if message.receiver else None,
            'receiver_id': str(message.receiver.pk) if message.receiver else None
        }

    @staticmethod
    def _has_profile_photo(message):
        return hasattr(message.sender, 'profile') and hasattr(message.sender.profile, 'photo')

    @staticmethod
    def _get_user_ids(uuid):
        """
        Get list user ids by message receiver id
        :param uuid: receiver uuid
        :return: list of ids
        """
        return list(get_user_model().objects.filter(pk=uuid, is_active=True).values_list('pk', flat=True))

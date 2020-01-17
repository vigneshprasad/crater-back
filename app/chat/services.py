from django.contrib.auth import get_user_model
from django.db.models import Q
from django.core.cache import cache

from chat.models import Message
from channels.db import database_sync_to_async

from chat.serializers import MessageSerializer


@database_sync_to_async
def create_message(message, sender, receiver=None, is_support=False):
    """
    Create message by params
    :param message: message string
    :param sender: sender user
    :param receiver: receiver user
    :param is_support: is support message or between users, Boolean
    """
    if message:
        Message.objects.create(message=message, sender_id=sender, receiver_id=receiver, is_support=is_support)


@database_sync_to_async
def get_messages(receiver, is_support=False):
    """
    Get messages for specific receiver
    :param receiver: receiver user
    :param is_support: is support message or between users, Boolean
    :return message queryset
    """
    Message.objects.filter(receiver_id=receiver, is_support=is_support)


@database_sync_to_async
def get_read_support_messages_ids_by_user(user):
    """
    Read all messages sent to user
    :param user: receiver user
    """
    messages = Message.objects.filter(receiver_id=user, is_support=True, is_read=False)
    message_ids = list(messages.values_list('id', flat=True))
    messages.update(is_read=True)
    return message_ids


@database_sync_to_async
def get_support_admin_ids():
    """
    Get all support admins
    :return list of admin ids
    """
    return list(get_user_model().objects.filter(is_staff=True, is_active=True).values_list('pk', flat=True))


@database_sync_to_async
def get_paginated_support_messages(receiver, page):
    """
    Retrun paginated messages for user get help page
    :param receiver: user
    :param page: pagination page
    :return: queryset of messages
    """
    page_size = 10
    qs_key = receiver + '_support_messages'

    qs = Message.objects.filter(Q(receiver_id=receiver) | Q(sender_id=receiver), is_support=True)
    if page == 1:
        cache.set(qs_key, qs.reverse(), 86400)
    messages = cache.get(qs_key, Message.objects.none())[(page-1) * page_size:page * page_size]
    messages.reverse()
    return MessageSerializer(instance=messages, many=True).data

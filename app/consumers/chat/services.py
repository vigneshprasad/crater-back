from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.db.models import Q
from django.core.cache import cache

import base64
from django.core.files.base import ContentFile
from consumers.chat.models import Message, ChatStarredUser
from channels.db import database_sync_to_async

from consumers.chat.serializers import MessageSerializer, UserChatSerializer


@database_sync_to_async
def create_message(message, sender, _file=None, filename=None, receiver=None, is_support=False):
    """
    Create message by params
    :param message: message string
    :param sender: sender user
    :param receiver: receiver user
    :param _file: message file
    :param filename: message file filename
    :param is_support: is support message or between users, Boolean
    """
    if _file:
        _message = Message(
            message=message, sender_id=sender, receiver_id=receiver, is_support=is_support
        )
        _format, file_data = _file.split(';base64,')
        ext = _format.split('/')[-1]
        data = ContentFile(base64.b64decode(file_data))
        file_name = f'{filename or sender}.' + ext
        _message.file.save(file_name, data, save=True)
    elif message:
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
def get_read_user_messages_ids_by_user(user, sender):
    """
    Read all messages sent to user
    :param user: receiver user
    :param sender: sender user
    """
    messages = Message.objects.filter(receiver_id=user, sender_id=sender, is_support=False, is_read=False)
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
def get_users_ids():
    """
    Get all support admins
    :return list of admin ids
    """
    return list(get_user_model().objects.filter(is_active=True).values_list('pk', flat=True))


@database_sync_to_async
def is_admin_by_pk(uuid):
    """
    Check if user is admin
    :return Boolean
    """
    return get_user_model().objects.filter(
        Q(is_staff=True, is_active=True, groups__name__in=['support', 'admin'], uuid=uuid)
        | Q(is_superuser=True, uuid=uuid)
    ).exists()


@database_sync_to_async
def get_paginated_support_messages(receiver, page):
    """
    Returns paginated messages for user get help page
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


@database_sync_to_async
def get_paginated_user_messages(sender, receiver, page):
    """
    Returns paginated messages for user get help page
    :param sender: sender
    :param receiver: receiver
    :param page: page
    :return: queryset of messages
    """
    page_size = 10
    qs_key = receiver + '_user_messages'

    qs = Message.objects.filter(
        Q(receiver_id=sender, sender_id=receiver) | Q(receiver_id=receiver, sender_id=sender),
        is_support=False
    )
    if page == 1:
        cache.set(qs_key, qs.reverse(), 86400)
    messages = cache.get(qs_key, Message.objects.none())[(page-1) * page_size:page * page_size]
    messages.reverse()
    return MessageSerializer(instance=messages, many=True).data


@database_sync_to_async
def get_paginated_users(page=1, search=None, _filter=None, uuid=None):
    """
    Returns paginated user data
    :param page: pagination page
    :param search: search users by name
    :param _filter: filter users by all, read messages, unread messages, starred
    :param uuid: request user pk
    :return: queryset of users
    """
    page_size = 10
    qs = get_user_model().objects.filter(
        is_active=True, is_staff=False, is_superuser=False, groups__name__in=['User', 'Investor']
    ).exclude(pk=uuid)
    if qs:
        if search:
            qs = qs.filter(name__icontains=search)
        if _filter == 'read':
            """
            Exclude all users with messages to consumer user and do not have and unread message
            """
            qs = qs.filter(sender_messages__receiver_id=uuid).distinct()
            for user in qs:
                for message in user.sender_messages.all():
                    if message.receiver and str(message.receiver.pk) == str(uuid) and not message.is_read:
                        qs = qs.exclude(pk=user.pk)
                        break
        elif _filter == 'unread':
            """
            Exclude all users with messages to consumer user and who has al least one unread message
            """
            qs = qs.filter(sender_messages__is_read=False, sender_messages__receiver_id=uuid).distinct()
        elif _filter == 'starred':
            qs = qs.filter(user_stars__creator__pk=uuid).distinct()
    users = qs[(page-1) * page_size:page * page_size]
    return UserChatSerializer(instance=users, many=True, context={'user': uuid}).data


@database_sync_to_async
def star_user(creator, user):
    """
    Star user in user to user chat
    :param creator: pagination page
    :param user: search users by name
    :return: starred user
    """
    try:
        chat_starred = ChatStarredUser.objects.create(creator_id=creator, user_id=user)
    except IntegrityError:
        return None
    return str(chat_starred.user.pk)


@database_sync_to_async
def unstar_user(creator, user):
    """
    Delete Star user in user to user chat
    :param creator: pagination page
    :param user: search users by name
    :return: starred user
    """
    try:
        starred = ChatStarredUser.objects.get(creator_id=creator, user_id=user)
    except ChatStarredUser.DoesNotExist:
        return None
    pk = str(starred.user.pk)
    starred.delete()
    return pk

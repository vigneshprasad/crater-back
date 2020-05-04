import base64
import math

from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.base import ContentFile
from django.db import IntegrityError
from django.db.models import Q
from django.db.models.functions import Lower

from consumers.chat.models import Message, ChatStarredUser
from consumers.chat.serializers import MessageSerializer, UserChatSerializer
from consumers.chat.models import LastSeen


@database_sync_to_async
def create_last_seen(user_id):
    instance, created = LastSeen.objects.get_or_create(user_id=user_id)
    if not created:
        instance.save()


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
    return Message.objects.filter(receiver_id=receiver, is_support=is_support)


@database_sync_to_async
def get_inbox_messages(receiver):
    """
    Get messages for specific receiver
    :param receiver: receiver user
    :return message queryset
    """
    return MessageSerializer(Message.objects.filter(
        receiver_id=receiver, is_read=False
    ).order_by('sender_id', '-created').distinct('sender_id')[:5], many=True).data


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
def get_user_data(receiver_id, sender_id):
    """
    Read user data as photo, introduction
    :param receiver_id: receiver user primary key
    :param sender_id: sender user primary key
    return user data dict
    """
    try:
        user = get_user_model().objects.get(pk=receiver_id)
        sender = get_user_model().objects.get(pk=sender_id)
        serializer_data = UserChatSerializer(instance=user, context={'user': sender.uuid}).data
        if hasattr(user, 'profile'):
            photo = None
            try:
                photo = user.profile.photo.url
            except ValueError:
                pass
            return {
                'photo': photo,
                'introduction': user.profile.introduction,
                'name': user.name,
                'additional_information': user.profile.additional_information,
            }, serializer_data
        return {}, serializer_data
    except get_user_model().DoesNotExist:
        pass
    return {}, {}


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
    Get all users
    :return list of user ids
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
def is_starred(creator_id, user_id):
    """
    Check if user is admin
    :param creator_id: User who created star
    :param user_id User who was starred
    :return Boolean
    """
    return ChatStarredUser.objects.filter(creator=creator_id, user=user_id).exists()


@database_sync_to_async
def get_latest_message(sender_id, receiver_id):
    """
    Check if user is admin
    :param sender_id: user who sent message
    :param receiver_id ser who received message
    :return Message instance
    """
    return MessageSerializer(Message.objects.filter(
        Q(receiver_id=receiver_id, sender_id=sender_id) | Q(receiver_id=sender_id, sender_id=receiver_id),
        is_support=False
    ).last()).data


@database_sync_to_async
def get_paginated_support_messages(receiver, page):
    """
    Returns paginated messages for user get help page
    :param receiver: user
    :param page: pagination page
    :return: queryset of messages
    """
    page_size = 20
    qs_key = receiver + '_support_messages'

    qs = Message.objects.filter(Q(receiver_id=receiver) | Q(sender_id=receiver), is_support=True)
    if page == 1:
        cache.set(qs_key, qs.reverse(), 86400)
    messages = cache.get(qs_key, Message.objects.none())[(page-1) * page_size:page * page_size]
    return MessageSerializer(instance=messages, many=True).data, math.ceil(qs.count() / page_size)


@database_sync_to_async
def get_paginated_user_messages(sender, receiver, page):
    """
    Returns paginated messages for user get help page
    :param sender: sender
    :param receiver: receiver
    :param page: page
    :return: queryset of messages
    """
    page_size = 20
    qs_key = receiver + '_user_messages'

    qs = Message.objects.filter(
        Q(receiver_id=sender, sender_id=receiver) | Q(receiver_id=receiver, sender_id=sender),
        is_support=False
    )
    if page == 1:
        cache.set(qs_key, qs.reverse(), 86400)
    messages = cache.get(qs_key, Message.objects.none())
    return MessageSerializer(
        instance=messages[(page-1) * page_size:page * page_size],
        many=True,
    ).data, math.ceil(qs.count() / page_size)


@database_sync_to_async
def get_paginated_users(page=1, search=None, _filter=None, latest_messages=None, uuid=None, is_strict=False):
    """
    Returns paginated user data
    :param page: pagination page
    :param search: search users by name
    :param _filter: filter users by all, read messages, unread messages, starred
    :param latest_messages: show the users with no chat messages
    :param uuid: request user pk
    :param is_strict: flag for strict page items
    :return: queryset of users
    """
    users_page_size = 20
    messages_page_size = 20
    qs = get_user_model().objects.prefetch_related('sender_messages', 'receiver_messages').filter(
        is_active=True, is_staff=False, is_superuser=False, groups__name__in=['User', 'Investor']
    ).exclude(pk=uuid)
    if not qs:
        return None, None

    if search:
        qs = qs.filter(name__icontains=search)
    if _filter == 'read':
        """
        Exclude all users with messages to consumer user and do not have and unread message
        """
        qs = qs.filter(
            Q(sender_messages__receiver_id=uuid, sender_messages__is_support=False) |
            Q(receiver_messages__sender_id=uuid, receiver_messages__is_support=False),
        ).distinct()
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
    if latest_messages == 'all':
        """
        Search user from all users
        """
        qs = qs.order_by(Lower('name'))
        users = qs[(page - 1) * messages_page_size:page * messages_page_size]
        return UserChatSerializer(
            instance=users, many=True, context={'user': uuid}
        ).data, math.ceil(qs.count() / users_page_size)
    else:
        qs = qs.filter(
            Q(sender_messages__receiver_id=uuid, sender_messages__is_support=False) |
            Q(receiver_messages__sender_id=uuid, receiver_messages__is_support=False),
        ).distinct()
        users_data = UserChatSerializer(instance=qs, many=True, context={'user': uuid}).data
        users = [u for u in sorted(users_data, key=lambda item: item['latest_message']['created'], reverse=True)]
        if is_strict:
            return users[
                   (page - 1) * messages_page_size:page * users_page_size
                   ], math.ceil(len(users) / users_page_size)
        return users[:page * users_page_size], math.ceil(len(users) / users_page_size)


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

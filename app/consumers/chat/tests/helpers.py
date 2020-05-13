import asyncio

from django.contrib.auth.models import Group
from urllib.parse import unquote, urlparse

from asgiref.compatibility import guarantee_single_callable
from channels.db import database_sync_to_async
from channels.testing import WebsocketCommunicator

from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password

from consumers.chat.models import Message
from consumers.chat.serializers import MessageSerializer


class TestWebsocketCommunicator(WebsocketCommunicator):
    def __init__(self, application, path, headers=None, subprotocols=None, receiver_id=None, token=None):
        parsed = urlparse(path)
        self.scope = {
            'type': 'websocket',
            'path': unquote(parsed.path),
            'query_string': parsed.query.encode("utf-8"),
            'headers': headers or [],
            'subprotocols': subprotocols or [],
            'url_route': {
                'kwargs': {
                    'receiver_id': receiver_id,
                    'token': token
                }
            }
        }
        self.application = guarantee_single_callable(application)
        self.input_queue = asyncio.Queue()
        self.output_queue = asyncio.Queue()
        self.future = asyncio.ensure_future(
            self.application(self.scope, self.input_queue.get, self.output_queue.put)
        )


@database_sync_to_async
def create_user(email, is_support=False, name=''):
    return get_user_model().objects.create(
        is_active=True, email=email, password=make_password('123qaz123'), is_superuser=is_support, name=name
    )


@database_sync_to_async
def get_group(group):
    return Group.objects.get(name=group)


@database_sync_to_async
def create_user_group(user, group):
    user.groups.add(group)


@database_sync_to_async
def get_message_data(**kwargs):
    message = Message.objects.filter(**kwargs).first()
    if message:
        return MessageSerializer(message).data


@database_sync_to_async
def get_message(message):
    return Message.objects.filter(message=message).first()


@database_sync_to_async
def create_message(message, sender, receiver, is_support):
    return Message.objects.create(message=message, sender_id=sender, receiver_id=receiver, is_support=is_support)


@database_sync_to_async
def get_message_sender_pk(**kwargs):
    return Message.objects.get(**kwargs).sender.pk


@database_sync_to_async
def get_message_receiver_pk(**kwargs):
    return Message.objects.get(**kwargs).receiver.pk
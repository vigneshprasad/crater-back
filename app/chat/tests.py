import pytest
from channels.db import database_sync_to_async
from channels.testing import HttpCommunicator
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password

from chat.consumers import ChatConsumer
from chat.models import Message


@database_sync_to_async
def create_user(email, is_support=False):
    return get_user_model().objects.create(email=email, password=make_password('123qaz123'), is_superuser=is_support)


@database_sync_to_async
def get_messages_count(**kwargs):
    return Message.objects.filter(**kwargs).count()


@database_sync_to_async
def get_message_sender_pk(**kwargs):
    return Message.objects.get(**kwargs).sender.pk


@database_sync_to_async
def get_message_receiver_pk(**kwargs):
    return Message.objects.get(**kwargs).receiver.pk


@pytest.mark.asyncio
@pytest.mark.django_db
async def test_consumer_admin_send_one_message():
    message = {
        'message': 'test1',
        'type': 'send_admin_message_to_user',
    }
    user = await create_user('user1@test.com')
    admin = await create_user('admin1@test.com', is_support=True)
    ChatConsumer.user_id = admin.pk
    ChatConsumer.receiver_id = user.pk
    communicator = HttpCommunicator(ChatConsumer, "POST", f'/ws/chat/{user.pk}/{admin.pk}/')
    await communicator.send_input(message)
    await communicator.wait(timeout=1)
    assert await get_messages_count(message=str(message)) == 1


@pytest.mark.asyncio
@pytest.mark.django_db
async def test_consumer_admin_send_two_messages():
    message2 = {
        'message': 'test2',
        'type': 'send_admin_message_to_user',
    }
    message3 = {
        'message': 'test3',
        'type': 'send_admin_message_to_user',
    }
    user = await create_user('user2@test.com')
    admin = await create_user('admin2@test.com', is_support=True)
    ChatConsumer.user_id = admin.pk
    ChatConsumer.receiver_id = user.pk
    communicator = HttpCommunicator(ChatConsumer, "POST", f'/ws/chat/{user.pk}/{admin.pk}/')
    await communicator.send_input(message2)
    await communicator.send_input(message3)
    await communicator.wait(timeout=1)
    assert await get_messages_count(message=str(message2)) == 1
    assert await get_messages_count(message=str(message3)) == 1


@pytest.mark.asyncio
@pytest.mark.django_db
async def test_consumer_admin_send_message_to_user():
    message4 = {
        'message': 'test4',
        'type': 'send_admin_message_to_user',
    }
    user = await create_user('user3@test.com')
    admin = await create_user('admin3@test.com', is_support=True)
    ChatConsumer.user_id = admin.pk
    ChatConsumer.receiver_id = user.pk
    communicator = HttpCommunicator(ChatConsumer, "POST", f'/ws/chat/{user.pk}/{admin.pk}/')
    await communicator.send_input(message4)
    await communicator.wait(timeout=1)
    assert await get_message_sender_pk(message=str(message4)) == admin.pk
    assert await get_message_receiver_pk(message=str(message4)) == user.pk

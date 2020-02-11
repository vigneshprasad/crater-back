import mock
import pytest

from consumers.chat.tasks import read_admin_messages_for_user
from rest_framework_jwt.utils import jwt_encode_handler, jwt_payload_handler

from consumers.consumers import ChatConsumer
from consumers.chat.helpers import MessageHelper
from consumers.chat.tests.helpers import create_user, TestWebsocketCommunicator, get_message_data, get_group, create_user_group
from utils.file_test_service import get_test_base64_image


SOCKET_URL = '/ws/connector/'


@pytest.mark.asyncio
@pytest.mark.django_db
async def test_consumer_admin_send_message_success():
    MessageHelper.send_admin_message_to_user = mock.MagicMock()
    MessageHelper.send_user_message_to_admin = mock.MagicMock()
    MessageHelper.send_user_message_to_user = mock.MagicMock()
    read_admin_messages_for_user.delay = mock.MagicMock()
    message = {
        'message': 'test1',
        'type': 'send_admin_message_to_user',
    }
    user = await create_user('user1@test.com')
    admin = await create_user('admin1@test.com', is_support=True)

    expected_message_data = {
        'message': 'test1',
        'file': None,
        'sender': ' ',
        'receiver': ' ',
        'is_read': False,
        'is_support': True,
        'sender_id': str(admin.pk),
        'receiver_id': str(user.pk),
    }
    token = jwt_encode_handler(jwt_payload_handler(admin))
    communicator = TestWebsocketCommunicator(ChatConsumer, f'{SOCKET_URL}{user.pk}/{token}/', receiver_id=user.pk, token=token)
    connected, subprotocol = await communicator.connect()
    assert connected
    await communicator.send_json_to(message)
    await communicator.wait()
    data = await get_message_data(message=message['message'])
    assert data['message'] == expected_message_data['message']
    assert data['file'] == expected_message_data['file']
    assert data['sender'] == expected_message_data['sender']
    assert data['is_read'] == expected_message_data['is_read']
    assert data['is_support'] == expected_message_data['is_support']
    assert data['sender_id'] == expected_message_data['sender_id']
    assert data['receiver_id'] == expected_message_data['receiver_id']
    MessageHelper.send_admin_message_to_user.assert_called_once()
    MessageHelper.send_user_message_to_admin.assert_not_called()
    MessageHelper.send_user_message_to_user.assert_not_called()
    read_admin_messages_for_user.delay.assert_called_once()

    await communicator.disconnect()


@pytest.mark.asyncio
@pytest.mark.django_db
async def test_consumer_admin_send_empty_message():
    MessageHelper.send_admin_message_to_user = mock.MagicMock()
    MessageHelper.send_user_message_to_admin = mock.MagicMock()
    MessageHelper.send_user_message_to_user = mock.MagicMock()
    read_admin_messages_for_user.delay = mock.MagicMock()
    message = {
        'message': '',
        'type': 'send_admin_message_to_user',
    }
    user = await create_user('user2@test.com')
    admin = await create_user('admin2@test.com', is_support=True)
    token = jwt_encode_handler(jwt_payload_handler(admin))
    communicator = TestWebsocketCommunicator(ChatConsumer, f'{SOCKET_URL}{user.pk}/{token}/', receiver_id=user.pk, token=token)
    connected, subprotocol = await communicator.connect()
    assert connected
    await communicator.send_json_to(message)
    await communicator.wait()
    data = await get_message_data(message=message['message'])
    assert data is None
    MessageHelper.send_admin_message_to_user.assert_not_called()
    MessageHelper.send_user_message_to_admin.assert_not_called()
    MessageHelper.send_user_message_to_user.assert_not_called()
    read_admin_messages_for_user.delay.assert_not_called()

    await communicator.disconnect()


@pytest.mark.asyncio
@pytest.mark.django_db
async def test_consumer_user_is_typing():
    read_admin_messages_for_user.delay = mock.MagicMock()
    user = await create_user('user3@test.com')
    admin = await create_user('admin3@test.com', is_support=True)
    message = {
        'message': {'admin_receiver_id': str(user.pk)},
        'type': 'user_is_typing',
    }
    token = jwt_encode_handler(jwt_payload_handler(admin))
    communicator = TestWebsocketCommunicator(ChatConsumer, f'{SOCKET_URL}{user.pk}/{token}/', receiver_id=user.pk, token=token)
    connected, subprotocol = await communicator.connect()
    assert connected
    await communicator.send_json_to(message)

    await communicator.disconnect()


@pytest.mark.asyncio
@pytest.mark.django_db
async def test_consumer_user_send_message_to_user():
    MessageHelper.send_admin_message_to_user = mock.MagicMock()
    MessageHelper.send_user_message_to_admin = mock.MagicMock()
    MessageHelper.send_user_message_to_user = mock.MagicMock()
    read_admin_messages_for_user.delay = mock.MagicMock()
    user = await create_user('user4@test.com')
    receiver = await create_user('receiver@test.com')
    message = {
        'message': 'test2',
        'type': 'send_user_message_to_user',
    }
    message_set_user_chat = {
        'message': {'user': str(receiver.pk), 'page': 1},
        'type': 'set_user_chat',
    }

    expected_message_data = {
        'message': 'test2',
        'file': None,
        'sender': ' ',
        'receiver': ' ',
        'is_read': False,
        'is_support': False,
        'sender_id': str(user.pk),
        'receiver_id': str(receiver.pk)
    }

    token = jwt_encode_handler(jwt_payload_handler(user))
    communicator = TestWebsocketCommunicator(ChatConsumer, f'{SOCKET_URL}/{token}/', receiver_id=receiver.pk, token=token)
    connected, subprotocol = await communicator.connect()
    assert connected
    await communicator.send_json_to(message_set_user_chat)
    await communicator.send_json_to(message)
    await communicator.wait()
    data = await get_message_data(message=message['message'])
    assert data['message'] == expected_message_data['message']
    assert data['file'] == expected_message_data['file']
    assert data['sender'] == expected_message_data['sender']
    assert data['is_read'] == expected_message_data['is_read']
    assert data['is_support'] == expected_message_data['is_support']
    assert data['sender_id'] == expected_message_data['sender_id']
    assert data['receiver_id'] == expected_message_data['receiver_id']
    MessageHelper.send_admin_message_to_user.assert_not_called()
    MessageHelper.send_user_message_to_user.assert_called_once()
    MessageHelper.send_user_message_to_admin.assert_called_once()
    read_admin_messages_for_user.delay.assert_not_called()

    await communicator.disconnect()


@pytest.mark.asyncio
@pytest.mark.django_db
async def test_consumer_user_send_message_file_to_user():
    MessageHelper.send_admin_message_to_user = mock.MagicMock()
    MessageHelper.send_user_message_to_admin = mock.MagicMock()
    MessageHelper.send_user_message_to_user = mock.MagicMock()
    read_admin_messages_for_user.delay = mock.MagicMock()
    user = await create_user('user_file4@test.com')
    receiver = await create_user('receiver_file@test.com')
    message = {
        'message': 'test_file2',
        'file': get_test_base64_image(),
        'type': 'send_user_message_to_user',
    }
    message_set_user_chat = {
        'message': {'user': str(receiver.pk), 'page': 1},
        'type': 'set_user_chat',
    }

    expected_message_data = {
        'message': 'test_file2',
        'file': '',
        'sender': ' ',
        'receiver': ' ',
        'is_read': False,
        'is_support': False,
        'sender_id': str(user.pk),
        'receiver_id': str(receiver.pk)
    }

    token = jwt_encode_handler(jwt_payload_handler(user))
    communicator = TestWebsocketCommunicator(ChatConsumer, f'{SOCKET_URL}/{token}/', receiver_id=receiver.pk, token=token)
    connected, subprotocol = await communicator.connect()
    assert connected
    await communicator.send_json_to(message_set_user_chat)
    await communicator.send_json_to(message)
    await communicator.wait()
    data = await get_message_data(message=message['message'])
    assert data['message'] == expected_message_data['message']
    assert f'{str(user.pk)}.png' in data['file']
    assert data['sender'] == expected_message_data['sender']
    assert data['is_read'] == expected_message_data['is_read']
    assert data['is_support'] == expected_message_data['is_support']
    assert data['sender_id'] == expected_message_data['sender_id']
    assert data['receiver_id'] == expected_message_data['receiver_id']
    MessageHelper.send_admin_message_to_user.assert_not_called()
    MessageHelper.send_user_message_to_user.assert_called_once()
    MessageHelper.send_user_message_to_admin.assert_not_called()
    read_admin_messages_for_user.delay.assert_not_called()
    await communicator.disconnect()


@pytest.mark.asyncio
@pytest.mark.django_db
async def test_consumer_user_send_message_to_user():
    MessageHelper.send_admin_message_to_user = mock.MagicMock()
    MessageHelper.send_user_message_to_admin = mock.MagicMock()
    MessageHelper.send_user_message_to_user = mock.MagicMock()
    read_admin_messages_for_user.delay = mock.MagicMock()
    user = await create_user('user4@test.com')
    message = {
        'message': 'test3',
        'type': 'send_user_message_to_admin',
    }

    expected_message_data = {
        'message': 'test3',
        'file': None,
        'sender': ' ',
        'receiver': ' ',
        'is_read': False,
        'is_support': True,
        'sender_id': str(user.pk),
        'receiver_id': None
    }

    token = jwt_encode_handler(jwt_payload_handler(user))
    communicator = TestWebsocketCommunicator(ChatConsumer, f'{SOCKET_URL}/{token}/', token=token)
    connected, subprotocol = await communicator.connect()
    assert connected
    await communicator.send_json_to(message)
    await communicator.wait()
    data = await get_message_data(message=message['message'])
    assert data['message'] == expected_message_data['message']
    assert data['file'] == expected_message_data['file']
    assert data['sender'] == expected_message_data['sender']
    assert data['is_read'] == expected_message_data['is_read']
    assert data['is_support'] == expected_message_data['is_support']
    assert data['sender_id'] == expected_message_data['sender_id']
    assert data['receiver_id'] == expected_message_data['receiver_id']
    MessageHelper.send_admin_message_to_user.assert_not_called()
    MessageHelper.send_user_message_to_admin.assert_called_once()
    MessageHelper.send_user_message_to_user.assert_not_called()
    read_admin_messages_for_user.delay.assert_not_called()

    await communicator.disconnect()


@pytest.mark.asyncio
@pytest.mark.django_db
async def test_consumer_user_send_empty_message():
    MessageHelper.send_admin_message_to_user = mock.MagicMock()
    MessageHelper.send_user_message_to_admin = mock.MagicMock()
    MessageHelper.send_user_message_to_user = mock.MagicMock()
    read_admin_messages_for_user.delay = mock.MagicMock()
    user = await create_user('user5@test.com')
    receiver = await create_user('receiver5@test.com')
    message = {
        'message': '',
        'type': 'send_user_message_to_user',
    }
    message_set_user_chat = {
        'message': {'user': str(receiver.pk), 'page': 1},
        'type': 'set_user_chat',
    }
    token = jwt_encode_handler(jwt_payload_handler(user))
    communicator = TestWebsocketCommunicator(ChatConsumer, f'{SOCKET_URL}{user.pk}/{token}/', receiver_id=user.pk, token=token)
    connected, subprotocol = await communicator.connect()
    assert connected
    await communicator.send_json_to(message)
    await communicator.send_json_to(message_set_user_chat)
    await communicator.wait()
    data = await get_message_data(message=message['message'])
    assert data is None
    MessageHelper.send_admin_message_to_user.assert_not_called()
    MessageHelper.send_user_message_to_admin.assert_not_called()
    MessageHelper.send_user_message_to_user.assert_not_called()
    read_admin_messages_for_user.delay.assert_not_called()

    await communicator.disconnect()


@pytest.mark.asyncio
@pytest.mark.django_db
async def test_consumer_user_read_support_messages():
    MessageHelper.send_admin_message_to_user = mock.MagicMock()
    MessageHelper.send_user_message_to_admin = mock.MagicMock()
    MessageHelper.send_user_message_to_user = mock.MagicMock()
    read_admin_messages_for_user.delay = mock.MagicMock()
    user = await create_user('user6@test.com')
    admin = await create_user('admin6@test.com', is_support=True)
    admin_message = {
        'message': 'test6',
        'type': 'send_admin_message_to_user',
    }

    message = {
        'type': 'user_read_support_messages',
    }

    token = jwt_encode_handler(jwt_payload_handler(user))
    admin_token = jwt_encode_handler(jwt_payload_handler(admin))
    communicator = TestWebsocketCommunicator(ChatConsumer, f'{SOCKET_URL}{token}/', token=token)
    admin_communicator = TestWebsocketCommunicator(
        ChatConsumer, f'{SOCKET_URL}{token}/', receiver_id=user.pk, token=admin_token
    )
    connected, subprotocol = await communicator.connect()
    admin_connected, subprotocol = await admin_communicator.connect()
    assert connected
    assert admin_connected
    await admin_communicator.send_json_to(admin_message)
    await admin_communicator.wait()
    await communicator.send_json_to(message)
    await communicator.wait()
    data = await get_message_data(receiver=user, is_support=True)
    assert data['is_read'] is True
    MessageHelper.send_admin_message_to_user.assert_called_once()
    MessageHelper.send_user_message_to_admin.assert_not_called()
    MessageHelper.send_user_message_to_user.assert_not_called()
    read_admin_messages_for_user.delay.assert_called_once()

    await communicator.disconnect()
    await admin_communicator.disconnect()


@pytest.mark.asyncio
@pytest.mark.django_db
async def test_consumer_user_read_user_messages():
    MessageHelper.send_admin_message_to_user = mock.MagicMock()
    MessageHelper.send_user_message_to_admin = mock.MagicMock()
    MessageHelper.send_user_message_to_user = mock.MagicMock()
    read_admin_messages_for_user.delay = mock.MagicMock()
    user = await create_user('user7@test.com')
    sender = await create_user('sender7@test.com')
    admin = await create_user('admin7@test.com', is_support=True)
    admin_message = {
        'message': 'admin_test7',
        'type': 'send_admin_message_to_user',
    }

    sender_message = {
        'message': 'sender_test7',
        'type': 'send_user_message_to_user',
    }

    message = {
        'type': 'user_read_user_messages',
    }

    message_set_user_chat = {
        'message': {'user': str(user.pk), 'page': 1},
        'type': 'set_user_chat',
    }

    message_set_sender_chat = {
        'message': {'user': str(sender.pk), 'page': 1},
        'type': 'set_user_chat',
    }

    token = jwt_encode_handler(jwt_payload_handler(user))
    sender_token = jwt_encode_handler(jwt_payload_handler(sender))
    admin_token = jwt_encode_handler(jwt_payload_handler(admin))
    communicator = TestWebsocketCommunicator(ChatConsumer, f'{SOCKET_URL}{token}/', token=token)
    admin_communicator = TestWebsocketCommunicator(
        ChatConsumer, f'{SOCKET_URL}{user.pk}/{token}/', receiver_id=user.pk, token=admin_token
    )
    sender_communicator = TestWebsocketCommunicator(ChatConsumer, f'{SOCKET_URL}{token}/', token=sender_token)
    connected, subprotocol = await communicator.connect()
    admin_connected, subprotocol = await admin_communicator.connect()
    sender_connected, subprotocol = await sender_communicator.connect()
    assert connected
    assert admin_connected
    assert sender_connected

    await admin_communicator.send_json_to(admin_message)
    await sender_communicator.send_json_to(message_set_user_chat)
    await sender_communicator.send_json_to(sender_message)
    await admin_communicator.wait()
    await sender_communicator.wait()

    await communicator.send_json_to(message_set_sender_chat)
    await communicator.send_json_to(message)

    await communicator.wait()

    sender_message_data = await get_message_data(receiver=user, sender=sender)
    assert sender_message_data['is_read'] is True

    user_message_data = await get_message_data(receiver=sender, sender=user)
    assert user_message_data is None

    admin_message_data = await get_message_data(receiver=user, sender=admin)
    assert admin_message_data['is_read'] is False

    MessageHelper.send_admin_message_to_user.assert_called_once()
    MessageHelper.send_user_message_to_admin.assert_not_called()
    MessageHelper.send_user_message_to_user.assert_called_once()
    read_admin_messages_for_user.delay.assert_called_once()

    await communicator.disconnect()
    await sender_communicator.disconnect()
    await admin_communicator.disconnect()


@pytest.mark.asyncio
@pytest.mark.django_db
async def test_consumer_admin_read_user_messages():
    MessageHelper.send_admin_message_to_user = mock.MagicMock()
    MessageHelper.send_user_message_to_admin = mock.MagicMock()
    MessageHelper.send_user_message_to_user = mock.MagicMock()
    read_admin_messages_for_user.delay = mock.MagicMock()
    user = await create_user('user8@test.com')
    admin = await create_user('admin8@test.com', is_support=True)
    admin_message = {
        'message': 'admin_test8',
        'type': 'send_admin_message_to_user',
    }

    user_message = {
        'message': 'user_test8',
        'type': 'send_user_message_to_admin',
    }

    token = jwt_encode_handler(jwt_payload_handler(user))
    admin_token = jwt_encode_handler(jwt_payload_handler(admin))

    communicator = TestWebsocketCommunicator(ChatConsumer, f'{SOCKET_URL}{token}/', token=token)
    admin_communicator = TestWebsocketCommunicator(
        ChatConsumer, f'{SOCKET_URL}{user.pk}/{token}/', receiver_id=user.pk, token=admin_token
    )
    connected, subprotocol = await communicator.connect()
    admin_connected, subprotocol = await admin_communicator.connect()
    assert connected
    assert admin_connected

    await communicator.send_json_to(user_message)
    await communicator.wait()

    user_message_data = await get_message_data(message=user_message['message'])
    assert user_message_data['is_read'] is False

    await admin_communicator.send_json_to(admin_message)
    await admin_communicator.wait()

    user_message_data = await get_message_data(message=user_message['message'])
    assert user_message_data['is_read'] is False

    MessageHelper.send_admin_message_to_user.assert_called_once()
    MessageHelper.send_user_message_to_admin.assert_called_once()
    MessageHelper.send_user_message_to_user.asser_not_called()
    read_admin_messages_for_user.delay.assert_called_once()

    await communicator.disconnect()
    await admin_communicator.disconnect()


@pytest.mark.asyncio
@pytest.mark.django_db
async def test_consumer_get_support_chat_empty_messages():
    MessageHelper.send_admin_message_to_user = mock.MagicMock()
    MessageHelper.send_user_message_to_admin = mock.MagicMock()
    MessageHelper.send_user_message_to_user = mock.MagicMock()
    read_admin_messages_for_user.delay = mock.MagicMock()
    user = await create_user('user9@test.com')
    user_message = {
        'message': {'page': 1},
        'type': 'get_support_chat_messages',
    }

    token = jwt_encode_handler(jwt_payload_handler(user))

    communicator = TestWebsocketCommunicator(ChatConsumer, f'{SOCKET_URL}{token}/', token=token)
    connected, subprotocol = await communicator.connect()
    assert connected

    await communicator.send_json_to(user_message)

    response = await communicator.receive_json_from()
    assert response == {'results': [], 'type': 'get_support_chat_messages'}
    await communicator.wait()

    await communicator.disconnect()


@pytest.mark.asyncio
@pytest.mark.django_db
async def test_consumer_get_support_chat_messages():
    MessageHelper.send_admin_message_to_user = mock.MagicMock()
    MessageHelper.send_user_message_to_admin = mock.MagicMock()
    MessageHelper.send_user_message_to_user = mock.MagicMock()
    read_admin_messages_for_user.delay = mock.MagicMock()
    user = await create_user('user10@test.com')
    admin = await create_user('admin10@test.com', is_support=True)
    admin_message1 = {
        'message': 'admin_test10.1',
        'type': 'send_admin_message_to_user',
    }
    admin_message2 = {
        'message': 'admin_test10.2',
        'type': 'send_admin_message_to_user',
    }

    user_message = {
        'message': {'page': 1},
        'type': 'get_support_chat_messages',
    }

    token = jwt_encode_handler(jwt_payload_handler(user))
    admin_token = jwt_encode_handler(jwt_payload_handler(admin))

    communicator = TestWebsocketCommunicator(ChatConsumer, f'{SOCKET_URL}{token}/', token=token)
    admin_communicator = TestWebsocketCommunicator(
        ChatConsumer, f'{SOCKET_URL}{user.pk}/{token}/', receiver_id=user.pk, token=admin_token
    )
    connected, subprotocol = await communicator.connect()
    admin_connected, subprotocol = await admin_communicator.connect()
    assert connected
    assert admin_connected
    await admin_communicator.send_json_to(admin_message1)
    await admin_communicator.send_json_to(admin_message2)
    await admin_communicator.wait()

    await communicator.send_json_to(user_message)
    response = await communicator.receive_json_from()

    assert len(response['results']) == 2
    assert response['results'][0]['message'] == admin_message2['message']
    assert response['results'][1]['message'] == admin_message1['message']
    await communicator.wait()

    user_message_data = await get_message_data(message=user_message['message'])
    assert user_message_data is None

    MessageHelper.send_admin_message_to_user = mock.MagicMock()
    MessageHelper.send_user_message_to_admin = mock.MagicMock()
    MessageHelper.send_user_message_to_user = mock.MagicMock()
    read_admin_messages_for_user.delay = mock.MagicMock()

    await communicator.disconnect()
    await admin_communicator.disconnect()


@pytest.mark.asyncio
@pytest.mark.django_db
async def test_consumer_get_in_user_group_users():
    group = await get_group('User')
    user1 = await create_user('user11.1@test.com')
    await create_user_group(user1, group)
    user2 = await create_user('user11.2@test.com')
    await create_user_group(user2, group)
    await create_user('user11.3@test.com')
    await create_user('admin11@test.com', is_support=True)
    user_message = {
        'message': {'page': 1, 'latest_messages': 'all'},
        'type': 'get_all_users',
    }

    token = jwt_encode_handler(jwt_payload_handler(user1))

    communicator = TestWebsocketCommunicator(ChatConsumer, f'{SOCKET_URL}{token}/', token=token)
    connected, subprotocol = await communicator.connect()
    assert connected
    await communicator.send_json_to(user_message)
    response = await communicator.receive_json_from()
    assert len(response['results']) == 1
    assert response['results'][0]['pk'] == str(user2.pk)

    await communicator.disconnect()


@pytest.mark.asyncio
@pytest.mark.django_db
async def test_consumer_get_first_page_users():
    group = await get_group('User')
    user1 = await create_user('user12.1@test.com')
    await create_user_group(user1, group)
    user2 = await create_user('user12.2@test.com')
    await create_user_group(user2, group)
    user3 = await create_user('user12.3@test.com')
    await create_user_group(user3, group)
    user4 = await create_user('user12.4@test.com')
    await create_user_group(user4, group)
    user5 = await create_user('user12.5@test.com')
    await create_user_group(user5, group)
    user6 = await create_user('user12.6@test.com')
    await create_user_group(user6, group)
    user7 = await create_user('user12.7@test.com')
    await create_user_group(user7, group)
    user8 = await create_user('user12.8@test.com')
    await create_user_group(user8, group)
    user9 = await create_user('user12.9@test.com')
    await create_user_group(user9, group)
    user10 = await create_user('user12.10@test.com')
    await create_user_group(user10, group)
    user11 = await create_user('user12@test.com')
    await create_user_group(user11, group)
    user12 = await create_user('user12.12@test.com')
    await create_user_group(user12, group)
    user13 = await create_user('user12.13@test.com')
    await create_user_group(user13, group)
    user14 = await create_user('user12.14@test.com')
    await create_user_group(user14, group)
    user15 = await create_user('user12.15@test.com')
    await create_user_group(user15, group)
    await create_user('admin12@test.com', is_support=True)
    user_message = {
        'message': {'page': 1, 'latest_messages': 'all'},
        'type': 'get_all_users',
    }
    token = jwt_encode_handler(jwt_payload_handler(user1))

    communicator = TestWebsocketCommunicator(ChatConsumer, f'{SOCKET_URL}{token}/', token=token)
    connected, subprotocol = await communicator.connect()
    assert connected
    await communicator.send_json_to(user_message)
    response = await communicator.receive_json_from()
    assert len(response['results']) == 16
    await communicator.disconnect()


@pytest.mark.asyncio
@pytest.mark.django_db
async def test_consumer_get_second_page_users():
    group = await get_group('User')
    user1 = await create_user('user13.1@test.com', name='John')
    await create_user_group(user1, group)
    user2 = await create_user('user13.2@test.com', name='John')
    await create_user_group(user2, group)
    user3 = await create_user('user13.3@test.com', name='John')
    await create_user_group(user3, group)
    user4 = await create_user('user13.4@test.com', name='John')
    await create_user_group(user4, group)
    user5 = await create_user('user13.5@test.com', name='John')
    await create_user_group(user5, group)
    user6 = await create_user('user13.6@test.com', name='John')
    await create_user_group(user6, group)
    user7 = await create_user('user13.7@test.com', name='John')
    await create_user_group(user7, group)
    user8 = await create_user('user13.8@test.com', name='John')
    await create_user_group(user8, group)
    user9 = await create_user('user13.9@test.com', name='John')
    await create_user_group(user9, group)
    user10 = await create_user('user13.10@test.com', name='John')
    await create_user_group(user10, group)
    user11 = await create_user('user13.11@test.com', name='John')
    await create_user_group(user11, group)
    user12 = await create_user('user13.12@test.com', name='John')
    await create_user_group(user12, group)
    user13 = await create_user('user13.13@test.com', name='John')
    await create_user_group(user13, group)
    user14 = await create_user('user13.14@test.com', name='John')
    await create_user_group(user14, group)
    user15 = await create_user('user13.15@test.com', name='John')
    await create_user_group(user15, group)
    user16 = await create_user('user13.16@test.com', name='John')
    await create_user_group(user16, group)
    user17 = await create_user('user13.17@test.com', name='John')
    await create_user_group(user17, group)
    user18 = await create_user('user13.18@test.com', name='John')
    await create_user_group(user18, group)
    user19 = await create_user('user13.19@test.com', name='John')
    await create_user_group(user19, group)
    user20 = await create_user('user13.20@test.com', name='John')
    await create_user_group(user20, group)
    user21 = await create_user('user13.21@test.com', name='John')
    await create_user_group(user21, group)
    user22 = await create_user('user13.22@test.com', name='John')
    await create_user_group(user22, group)
    user23 = await create_user('user13.23@test.com', name='John')
    await create_user_group(user23, group)
    user24 = await create_user('user13.24@test.com', name='John')
    await create_user_group(user24, group)
    user25 = await create_user('user13.25@test.com', name='John')
    await create_user_group(user25, group)
    await create_user('admin13@test.com', is_support=True)
    user_message = {
        'message': {'page': 2, 'search': 'john', 'latest_messages': 'all'},
        'type': 'get_all_users',
    }
    token = jwt_encode_handler(jwt_payload_handler(user1))

    communicator = TestWebsocketCommunicator(ChatConsumer, f'{SOCKET_URL}{token}/', token=token)
    connected, subprotocol = await communicator.connect()
    assert connected
    await communicator.send_json_to(user_message)
    response = await communicator.receive_json_from()
    assert len(response['results']) == 4
    await communicator.disconnect()


@pytest.mark.asyncio
@pytest.mark.django_db
async def test_consumer_get_third_page_is_empty():
    group = await get_group('User')
    user1 = await create_user('user14.1@test.com', name='Jessica')
    await create_user_group(user1, group)
    user2 = await create_user('user14.2@test.com', name='Jessica')
    await create_user_group(user2, group)
    user3 = await create_user('user14.3@test.com', name='Jessica')
    await create_user_group(user3, group)
    user4 = await create_user('user14.4@test.com', name='Jessica')
    await create_user_group(user4, group)
    user5 = await create_user('user14.5@test.com', name='Jessica')
    await create_user_group(user5, group)
    user6 = await create_user('user14.6@test.com', name='Jessica')
    await create_user_group(user6, group)
    user7 = await create_user('user14.7@test.com', name='Jessica')
    await create_user_group(user7, group)
    user8 = await create_user('user14.8@test.com', name='Jessica')
    await create_user_group(user8, group)
    user9 = await create_user('user14.9@test.com', name='Jessica')
    await create_user_group(user9, group)
    user10 = await create_user('user14.10@test.com', name='Jessica')
    await create_user_group(user10, group)
    user11 = await create_user('user14@test.com', name='Jessica')
    await create_user_group(user11, group)
    user12 = await create_user('user14.12@test.com', name='Jessica')
    await create_user_group(user12, group)
    user13 = await create_user('user14.13@test.com', name='Jessica')
    await create_user_group(user13, group)
    user14 = await create_user('user14.14@test.com', name='Jessica')
    await create_user_group(user14, group)
    user15 = await create_user('user14.15@test.com', name='Jessica')
    await create_user_group(user15, group)
    await create_user('admin14@test.com', is_support=True, name='Jessica')
    user_message = {
        'message': {'page': 3, 'search': 'jessica', 'latest_messages': 'all'},
        'type': 'get_all_users',
    }
    token = jwt_encode_handler(jwt_payload_handler(user1))

    communicator = TestWebsocketCommunicator(ChatConsumer, f'{SOCKET_URL}{token}/', token=token)
    connected, subprotocol = await communicator.connect()
    assert connected
    await communicator.send_json_to(user_message)
    response = await communicator.receive_json_from()
    assert len(response['results']) == 0
    await communicator.disconnect()


@pytest.mark.asyncio
@pytest.mark.django_db
async def test_consumer_star_unstar_users():
    group = await get_group('User')
    user1 = await create_user('user15.1@test.com', name='Tom')
    await create_user_group(user1, group)
    user2 = await create_user('user15.2@test.com', name='Tom')
    await create_user_group(user2, group)
    user_message = {
        'message': {'user': str(user2.pk)},
        'type': 'star_user',
    }
    token = jwt_encode_handler(jwt_payload_handler(user1))

    communicator = TestWebsocketCommunicator(ChatConsumer, f'{SOCKET_URL}{token}/', token=token)
    connected, subprotocol = await communicator.connect()
    assert connected
    await communicator.send_json_to(user_message)
    response = await communicator.receive_json_from()
    assert response == {'type': 'star_user', 'user': str(user2.pk)}

    starred_message = {
        'message': {'page': 1, 'search': 'Tom', 'filter': 'starred', 'latest_messages': 'all'},
        'type': 'get_all_users',
    }
    await communicator.send_json_to(starred_message)
    response = await communicator.receive_json_from()
    assert len(response['results']) == 1
    assert response['results'][0]['pk'] == str(user2.pk)

    unstarred_user_message = {
        'message': {'user': str(user2.pk)},
        'type': 'unstar_user',
    }
    await communicator.send_json_to(unstarred_user_message)
    response = await communicator.receive_json_from()
    assert response == {'type': 'unstar_user', 'user': str(user2.pk)}

    await communicator.send_json_to(starred_message)
    response = await communicator.receive_json_from()
    assert len(response['results']) == 0

    await communicator.disconnect()

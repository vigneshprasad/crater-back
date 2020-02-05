import json
from rest_framework.renderers import JSONRenderer

from consumers.connect import ChatAuthConsumer
from consumers.chat.services import create_message, get_paginated_support_messages, \
    get_read_support_messages_ids_by_user, get_support_admin_ids, is_admin_by_pk, get_paginated_users, star_user, \
    unstar_user, get_paginated_user_messages, get_read_user_messages_ids_by_user, get_users_ids, is_starred, \
    get_latest_message, get_user_data


class ChatConsumer(ChatAuthConsumer):

    async def receive(self, text_data=None, bytes_data=None):
        """
        Receive message from socket send event and call consumer method according sent "type"
        :param text_data: sent data by socket
        :param bytes_data: bytes data
        """
        data = json.loads(text_data)
        await getattr(self, data['type'])(data.get('message'), data.get('file'), data.get('filename'))

    async def user_is_typing(self, message, *args, **kwargs):
        """
        Send message event to admin if user is typing
        :param message: message string
        """
        user_ids = await get_users_ids()
        for user_id in user_ids:
            await self.channel_layer.group_send(str(user_id), {
                'type': 'user_is_typing_to_user',
                'receiver_id': self.user_id,
                'admin_receiver_id': message.get('admin_receiver_id')
            })

    async def user_is_typing_to_user(self, event, *args, **kwargs):
        """
        Send message event to admin if user is typing
        """
        if self.receiver_id == event['receiver_id'] or self.user_id == event['admin_receiver_id']:
            await self.send(text_data=json.dumps({
                'type': 'user_is_typing',
                'receiver_id': event['receiver_id']
            }))

    async def send_admin_message_to_user(self, message, *args, **kwargs):
        """
        Send message event from admin and save this message into database
        :param message: message string
        """
        is_admin = await is_admin_by_pk(self.user_id)
        if is_admin:
            await create_message(message=message, sender=self.user_id, receiver=self.receiver_id, is_support=True)

    async def send_user_message_to_user(self, message, _file=None, filename=None, *args, **kwargs):
        """
        Send message event from user and save this message into database
        :param message: message string
        :param _file: message file
        """
        if self.receiver_id:
            await create_message(
                message=message,
                sender=self.user_id,
                _file=_file,
                receiver=self.receiver_id,
                is_support=False,
                filename=filename
            )

    async def send_user_message_to_admin(self, message, _file=None, *args, **kwargs):
        """
        Send message event from user and save this message into database
        :param message: message string
        """
        await create_message(message=message, sender=self.user_id, _file=_file, is_support=True)

    async def user_read_support_messages(self, message, *args, **kwargs):
        """
        Send message event user read the messages from admin
        :param message: message string
        """
        messages = await get_read_support_messages_ids_by_user(user=self.user_id)
        admins = await get_support_admin_ids()
        message_fmt = {
            'type': 'user_read_messages_to_admin',
            'messages': messages,
            'receiver_id': self.user_id
        }
        for admin in admins:
            await self.channel_layer.group_send(str(admin), message_fmt)

    async def user_read_user_messages(self, message, *args, **kwargs):
        """
        Send message event user read the messages from user
        :param message: message string
        """
        if self.receiver_id:
            messages = await get_read_user_messages_ids_by_user(user=self.user_id, sender=self.receiver_id)
            message_fmt = {
                'type': 'user_read_messages_to_user',
                'messages': messages,
                'receiver_id': self.user_id
            }
            await self.channel_layer.group_send(self.receiver_id, message_fmt)

    async def admin_read_messages_to_user(self, event, *args, **kwargs):
        """
        Send event to admins that user read the messages
        :param event: read messages by user
        """
        if self.user_id == event['user_id']:
            await self.send(text_data=json.dumps({
                'type': 'admin_read_messages',
                'messages': event['messages'],
                'user_id': event['user_id']
            }))

    async def user_read_messages_to_admin(self, event, *args, **kwargs):
        """
        Send event to admins that user read the messages
        :param event: read messages by user
        """
        if self.receiver_id == event['receiver_id']:
            await self.send(text_data=json.dumps({
                'type': 'user_read_messages',
                'messages': event['messages'],
                'receiver_id': event['receiver_id']
            }))

    async def user_read_messages_to_user(self, event, *args, **kwargs):
        """
        Send event to admins that user read the messages
        :param event: read messages by user
        """
        if self.receiver_id == event['receiver_id']:
            await self.send(text_data=json.dumps({
                'type': 'user_read_messages',
                'messages': event['messages'],
                'receiver_id': event['receiver_id']
            }))

    async def admin_message_to_user(self, event, *args, **kwargs):
        """
        Layer to send all messages to specific users about case if admin sent message to user
        :param event: message event data
        """
        if self.receiver_id == event['receiver_id'] or self.user_id == event['receiver_id']:
            await self.send(text_data=json.dumps({
                'type': 'admin_message',
                'message': event['message'],
                'file': event['file'],
                'file_format': event['file_format'],
                'pk': event['message_id'],
                'created': event['created'],
                'photo': event['sender_photo'],
                'sender': event['sender'],
                'sender_id': event['sender_id'],
                'receiver': event['receiver'],
                'receiver_id': event['receiver_id'],
                'is_read': event['is_read'],
                'is_support': event['is_support'],
            }))

    async def user_message_to_user(self, event, *args, **kwargs):
        """
        Layer to send all messages to specific users about case if admin sent message to user
        :param event: message event data
        """

        if (self.receiver_id == event['receiver_id'] and self.user_id == event['sender_id'])\
                or (self.receiver_id == event['sender_id'] and self.user_id == event['receiver_id']):
            await self.send(text_data=json.dumps({
                'type': 'user_message',
                'message': event['message'],
                'file': event['file'],
                'file_format': event['file_format'],
                'pk': event['message_id'],
                'created': event['created'],
                'photo': event['sender_photo'],
                'sender': event['sender'],
                'sender_id': event['sender_id'],
                'receiver': event['receiver'],
                'receiver_id': event['receiver_id'],
                'is_read': event['is_read'],
                'is_support': event['is_support'],
            }))

    async def get_support_chat_messages(self, event, *args, **kwargs):
        """
        Send paginated support messages to user
        :param event: message event data
        """
        messages = await get_paginated_support_messages(self.user_id, page=event.get('page', 1))
        results = json.loads(JSONRenderer().render(messages).decode('utf8'))
        await self.send(text_data=json.dumps({
            'type': 'get_messages',
            'results': results
        }))

    async def user_message_to_admin(self, event, *args, **kwargs):
        """
        Send message to admin chat and get help after is_support message creation(signal)
        :param event: message event data
        """
        if self.receiver_id == event['sender_id'] or self.user_id == event['sender_id']:
            await self.send(text_data=json.dumps({
                'type': 'user_message',
                'message': event['message'],
                'file': event['file'],
                'file_format': event['file_format'],
                'pk': event['message_id'],
                'created': event['created'],
                'photo': event['sender_photo'],
                'sender': event['sender'],
                'sender_id': event['sender_id'],
                'receiver': event['receiver'],
                'receiver_id': event['receiver_id'],
                'is_read': event['is_read'],
                'is_support': event['is_support'],
            }))

    async def user_notifications(self, event, *args, **kwargs):
        """
        Send notification to admin UI about some message was sent by user, with the latest message
        :param event: message event data
        """
        latest_message = await get_latest_message(event['sender_id'], self.user_id)
        latest_message_json = json.loads(JSONRenderer().render(latest_message).decode('utf8'))
        await self.send(text_data=json.dumps({
            'type': 'user_notification',
            'message': event['message'],
            'message_id': event['message_id'],
            'created': event['created'],
            'sender': event['sender'],
            'sender_id': event['sender_id'],
            'receiver': event['receiver'],
            'receiver_id': event['receiver_id'],
            'unread_count': event['unread_count'],
            'pk': event['sender_id'],
            'photo': event['sender_photo'],
            'name': event['sender'],
            'is_starred': await is_starred(self.user_id, event['sender_id']),
            'latest_message': latest_message_json
        }))

    async def get_all_users(self, event, *args, **kwargs):
        """
        Get all users to user chat
        :param event: message event data
        """
        try:
            users = await get_paginated_users(
                page=int(event.get('page', 1)),
                search=event.get('search'),
                _filter=event.get('filter'),
                latest_messages=event.get('latest_messages'),
                uuid=self.user_id,
            )
            results = json.loads(JSONRenderer().render(users).decode('utf8'))
        except ValueError:
            results = []
        await self.send(text_data=json.dumps({
            'type': 'all_users',
            'results': results
        }))

    async def star_user(self, event, *args, **kwargs):
        """
        Star user event
        :param event: message event data
        """
        user = await star_user(self.user_id, event['user'])
        await self.send(text_data=json.dumps({
            'type': 'star_user',
            'user': user
        }))

    async def unstar_user(self, event, *args, **kwargs):
        """
        Delete Star user event
        :param event: message event data
        """
        user = await unstar_user(self.user_id, event['user'])
        await self.send(text_data=json.dumps({
            'type': 'unstar_user',
            'user': user
        }))

    async def set_user_chat(self, event, *args, **kwargs):
        """
        Set chat with user. Retrieve the latest chat messages
        :param event: message event data
        """
        self.receiver_id = event['user']
        messages = await get_paginated_user_messages(sender=self.user_id, receiver=self.receiver_id, page=event['page'])
        results = json.loads(JSONRenderer().render(messages).decode('utf8'))
        user_data = await get_user_data(self.receiver_id)
        await self.send(text_data=json.dumps({
            'type': 'get_messages',
            'results': results,
            'user': self.receiver_id,
            'photo': user_data.get('photo'),
            'introduction': user_data.get('introduction'),
            'additional_information': user_data.get('additional_information'),
        }))

    async def set_admin_chat(self, event, *args, **kwargs):
        """
        Set chat with admin user. Retrieve the latest chat messages
        :param event: message event data
        """
        self.receiver_id = None
        messages = await get_paginated_support_messages(self.user_id, page=event.get('page', 1))
        results = json.loads(JSONRenderer().render(messages).decode('utf8'))
        await self.send(text_data=json.dumps({
            'type': 'get_messages',
            'results': results
        }))

    async def get_user_chat_messages(self, event, *args, **kwargs):
        """
        Set chat with user. Retrieve the latest chat messages
        :param event: message event data
        """
        messages = await get_paginated_user_messages(sender=self.user_id, receiver=self.receiver_id, page=event['page'])
        results = json.loads(JSONRenderer().render(messages).decode('utf8'))
        await self.send(text_data=json.dumps({
            'type': 'get_messages',
            'results': results
        }))

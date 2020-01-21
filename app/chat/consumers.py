import json
from rest_framework.renderers import JSONRenderer

from chat.connect import ChatAuthConsumer
from chat.services import create_message, get_paginated_support_messages, get_read_support_messages_ids_by_user, \
    get_support_admin_ids


class ChatConsumer(ChatAuthConsumer):

    async def receive(self, text_data=None, bytes_data=None):
        """
        Receive message from socket send event and call consumer method according sent "type"
        :param text_data: sent data by socket
        :param bytes_data: bytes data
        """
        data = json.loads(text_data)
        await getattr(self, data['type'])(data.get('message'))

    async def user_is_typing(self, message):
        """
        Send message event to admin if user is typing
        :param message: message string
        """
        admins = await get_support_admin_ids()
        for admin in admins:
            await self.channel_layer.group_send(str(admin), {
                'type': 'user_is_typing_to_admin',
                'receiver_id': self.user_id
            })

    async def user_is_typing_to_admin(self, event):
        """
        Send message event to admin if user is typing
        :param message: message string
        """
        if self.receiver_id == event['receiver_id']:
            await self.send(text_data=json.dumps({
                'type': 'user_is_typing',
                'receiver_id': event['receiver_id']
            }))

    async def send_admin_message_to_user(self, message):
        """
        Send message event from admin and save this message into database
        :param message: message string
        """
        await create_message(message=message, sender=self.user_id, receiver=self.receiver_id, is_support=True)

    async def send_user_message_to_admin(self, message):
        """
        Send message event from user and save this message into database
        :param message: message string
        """
        await create_message(message=message, sender=self.user_id, is_support=True)

    async def user_read_support_messages(self, message):
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

    async def admin_read_messages_to_user(self, event):
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

    async def user_read_messages_to_admin(self, event):
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

    async def admin_message_to_user(self, event):
        """
        Layer to send all messages to specific users about case if admin sent message to user
        :param event: message event data
        """

        if self.receiver_id == event['receiver_id'] or self.user_id == event['receiver_id']:
            await self.send(text_data=json.dumps({
                'type': 'admin_message',
                'message': event['message'],
                'file': event['file'],
                'message_id': event['message_id'],
                'created': event['created'],
                'sender': event['sender'],
            }))

    async def get_support_chat_messages(self, event):
        """
        Send paginated support messages to user
        :param event: message event data
        """
        messages = await get_paginated_support_messages(self.user_id, page=event['page'])
        results = json.loads(JSONRenderer().render(messages).decode('utf8'))
        await self.send(text_data=json.dumps({
            'type': 'get_messages',
            'results': results
        }))

    async def user_message_to_admin(self, event):
        """
        Send message to admin chat and get help after is_support message creation(signal)
        :param event: message event data
        """
        if self.receiver_id == event['sender_id'] or self.user_id == event['sender_id']:
            await self.send(text_data=json.dumps({
                'type': 'user_message',
                'message': event['message'],
                'file': event['file'],
                'message_id': event['message_id'],
                'created': event['created'],
                'sender': event['sender'],
                'sender_id': event['sender_id'],
                'receiver': event['receiver'],
                'receiver_id': event['receiver_id']
            }))

    async def admin_user_notifications(self, event):
        """
        Send notification to admin UI about some message was sent by user, with the latest message
        :param event: message event data
        """
        await self.send(text_data=json.dumps({
            'type': 'user_notification',
            'message': event['message'],
            'message_id': event['message_id'],
            'created': event['created'],
            'sender': event['sender'],
            'sender_id': event['sender_id'],
            'receiver': event['receiver'],
            'receiver_id': event['receiver_id'],
            'unread_count': event['unread_count']
        }))

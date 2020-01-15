import json

from chat.connect import ChatAuthConsumer
from chat.services import create_message


class ChatConsumer(ChatAuthConsumer):

    async def receive(self, text_data=None, bytes_data=None):
        data = json.loads(text_data)
        await getattr(self, data['type'])(data['message'])

    async def send_admin_message_to_user(self, message):
        await create_message(message=message, sender=self.user_id, receiver=self.receiver_id, is_support=True)

    async def send_user_message_to_admin(self, message):
        await create_message(message=message, sender=self.user_id, is_support=True)

    async def admin_message_to_user(self, event):
        if self.receiver_id == event['receiver_id']:
            await self.send(text_data=json.dumps({
                'type': 'admin_message',
                'message': event['message'],
                'created': event['created'],
                'name': event['name'],
            }))

    async def get_chat_messages(self, event):
        await self.send(text_data=json.dumps({}))

    async def user_message_to_admin(self, event):
        if self.receiver_id == event['sender_id']:
            await self.send(text_data=json.dumps({
                'type': 'user_message',
                'message': event['message'],
                'created': event['created'],
                'name': event['name'],
                'sender_id': event['sender_id'],
            }))

    async def admin_user_notifications(self, event):
        await self.send(text_data=json.dumps({
            'type': 'user_notification',
            'sender_id': event['sender_id'],
            'unread_count': event['unread_count'],
            'message': event['message']
        }))

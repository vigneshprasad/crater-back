import json

from chat.connect import ChatAuthConsumer
from chat.services import create_message


class ChatConsumer(ChatAuthConsumer):

    async def receive(self, text_data=None, bytes_data=None):
        data = json.loads(text_data)
        await self.channel_layer.group_send(
            self.user_id,
            {
                'type': data['type'],
                'message': data.get('message')
            }
        )

    async def send_message(self, event):
        message = event['message']
        await create_message(message=message, sender=self.user_id, receiver=self.receiver_id)
        await self.send(text_data=json.dumps({'message': message}))

    async def get_chat_messages(self, event):
        await self.send(text_data=json.dumps({}))


class SupportConsumer(ChatAuthConsumer):

    async def receive(self, text_data=None, bytes_data=None):
        data = json.loads(text_data)
        await self.channel_layer.group_send(
            self.user_id,
            {
                'type': data['type'],
                'message': data.get('message')
            }
        )

    async def send_support_message(self, event):
        message = event['message']
        # await create_message(message=message, sender=self.user_id, receiver=None, is_superuser=True)
        await self.send(text_data=json.dumps({'message': message}))

    async def get_chat_messages(self, event):
        await self.send(text_data=json.dumps({}))

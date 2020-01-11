from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer

from rest_framework.exceptions import ValidationError, AuthenticationFailed
from rest_framework_jwt.serializers import VerifyJSONWebTokenSerializer


class ChatAuthConsumer(AsyncWebsocketConsumer):
    user_id = None
    receiver_id = None

    async def connect(self):
        self.receiver_id = self.scope['url_route']['kwargs'].get('user_id')
        token = self.scope['url_route']['kwargs']['token']
        try:
            data = {'token': token}
            await self.is_valid_user(data)
        except (ValidationError, AuthenticationFailed) as v:
            print('>>>', v)
            return v

        await self.channel_layer.group_add(
            self.user_id,
            self.channel_name
        )
        await self.accept()

    @database_sync_to_async
    def is_valid_user(self, data):
        self.user_id = str(VerifyJSONWebTokenSerializer().validate(data)['user'].pk)

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.user_id,
            self.channel_name
        )

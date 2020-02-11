from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from jwt import InvalidAlgorithmError
from kombu.utils import json

from rest_framework.exceptions import ValidationError, AuthenticationFailed
from rest_framework_jwt.serializers import VerifyJSONWebTokenSerializer


class ChatAuthConsumer(AsyncWebsocketConsumer):
    user_id = None
    receiver_id = None

    async def connect(self):
        self.receiver_id = self.scope['url_route']['kwargs'].get('receiver_id')
        token = self.scope['url_route']['kwargs']['token']
        try:
            data = {'token': token}
            await self.is_valid_user(data)
            await self.channel_layer.group_add(
                self.user_id,
                self.channel_name
            )
            await self.accept()
        except (ValidationError, AuthenticationFailed, InvalidAlgorithmError) as v:
            await self.channel_layer.group_add('anonymous', 'anonymous')
            await self.accept()
            await self.send_no_permissions()

    @database_sync_to_async
    def is_valid_user(self, data):
        self.user_id = str(VerifyJSONWebTokenSerializer().validate(data)['user'].pk)

    async def send_no_permissions(self, *args, **kwargs):
        """
        Emit no permission event
        """
        await self.send(text_data=json.dumps({
            'type': 'access_denied',
            'message': {'status_code': 401},
            'user': 'anonymous'
        }))
        await self.close(code=401)

    async def disconnect(self, close_code):
        try:
            await self.channel_layer.group_discard(
                self.user_id,
                self.channel_name
            )
        except TypeError as ex:
            print('TypeError', ex)

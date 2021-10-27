import json

from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async

from .models import Group


class GroupChatConsumer(AsyncWebsocketConsumer):
    group_id = None
    user = None

    async def connect(self):
        self.user = self.scope["user"]

        await self.accept()

        if self.user.is_anonymous:
            await self.send_no_permissions()

        self.group_id = self.scope["url_route"]["kwargs"].get("group_id")

        # Validate group id
        group = await self.validate_group_id()
        if not group:
            await self.send_invalid_group_err()

        # Add channel name to the group
        await self.channel_layer.group_add(
            f"crater_live_{self.group_id}",
            self.channel_name
        )

    async def disconnect(self, code):
        await self.channel_layer.group_discard(
            f"crater_live_{self.group_id}",
            self.channel_name
        )

    async def receive(self, text_data=None, bytes_data=None):
        await self.send(text_data=json.dumps({
            'type': 'message',
            'data': json.loads(text_data)
        }))

    async def send_invalid_group_err(self, *args, **kwargs):
        """
        Send invalid group error
        """
        await self.send(text_data=json.dumps({
            'type': 'bad_request',
            'message': {'status_code': 400},
            'group': 'invalid'
        }))
        await self.close()

    async def send_no_permissions(self, *args, **kwargs):
        """
        Emit no permission event
        """
        await self.send(text_data=json.dumps({
            'type': 'access_denied',
            'message': {'status_code': 401},
            'user': 'anonymous'
        }))
        await self.close()

    @database_sync_to_async
    def validate_group_id(self):
        return Group.objects.filter(id=self.group_id).exists()

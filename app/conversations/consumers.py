import json

from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from rest_framework.exceptions import ValidationError

from .models import Group, GroupMessage
from .serializers import GroupMessageSerializer


class GroupChatConsumer(AsyncWebsocketConsumer):
    group = None
    user = None

    async def connect(self):
        self.user = self.scope["user"]

        await self.accept()

        if self.user.is_anonymous:
            await self.send_no_permissions()

        group_id = self.scope["url_route"]["kwargs"].get("group_id")

        # Validate group id
        try:
            await self.validate_group_id(group_id)
        except Group.DoesNotExist:
            await self.send_invalid_group_err()

        # Add channel name to the group
        await self.channel_layer.group_add(
            f"crater_live_{self.group.id}",
            self.channel_name
        )

    async def disconnect(self, code):
        await self.channel_layer.group_discard(
            f"crater_live_{self.group.id}",
            self.channel_name
        )

    async def receive(self, text_data=None, bytes_data=None):
        text_data = json.loads(text_data)

        group_message = await self.create_group_message(text_data.get("text"))
        if group_message:
            # Broadcast message on the channel group
            await self.channel_layer.group_send(
                f"crater_live_{self.group.id}",
                {
                    "type": "broadcast.message",
                    "message": json.dumps(group_message)
                }
            )

    async def broadcast_message(self, event):
        """
        Broadcast user message on the channel group
        """
        await self.send(event["message"])

    async def get_group_messages(self, event):
        """
        Retrieve group messages
        """
        pass

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
    def validate_group_id(self, group_id):
        self.group = Group.objects.get(id=group_id)

    @database_sync_to_async
    def create_group_message(self, message):
        group_message = None
        data = {
            "group": self.group.id,
            "sender": self.user.uuid,
            "message": message
        }

        try:
            serializer = GroupMessageSerializer(data=data)
            serializer.is_valid(raise_exception=True)
            serializer.save()

            group_message = serializer.data
        except ValidationError:
            pass

        return group_message

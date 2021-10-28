import json

from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async

from .models import Group
from . import services


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

        await self.get_group_messages()

    async def disconnect(self, code):
        await self.channel_layer.group_discard(
            f"crater_live_{self.group.id}",
            self.channel_name
        )

    async def receive(self, text_data=None, bytes_data=None):
        data = json.loads(text_data)

        await getattr(self, data.get("type"))(data.get("payload"))

    async def send_group_message(self, payload):
        """
        Create GroupMessage object and send it over channel layer
        """
        message = payload.get("message")
        group_message = await services.create_group_message(
            group=self.group,
            sender=self.user,
            message=message
        )

        if group_message:
            await self.channel_layer.group_send(
                f"crater_live_{self.group.id}",
                {
                    "type": "broadcast_new_group_message",
                    "message": group_message
                }
            )

    async def broadcast_new_group_message(self, event):
        """
        Broadcast message on channel group
        """
        await self.send(json.dumps({
            "type": "new_group_message",
            "payload": event["message"]
        }))

    async def get_group_messages(self):
        """
        Retrieve group messages
        """
        group_messages = await services.get_paginated_group_messages(self.group)
        # page = event.get("page")
        await self.send(json.dumps({
            "type": "group_messages_received",
            "payload": {
                "messages": group_messages,
            }
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
    def validate_group_id(self, group_id):
        self.group = Group.objects.get(id=group_id)

import json

from rest_framework.renderers import JSONRenderer
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async

from conversations import models
from conversations import services


class GroupChatConsumer(AsyncWebsocketConsumer):

    group = None
    user = None

    async def connect(self):
        """Connect to the channel layer."""
        self.user = self.scope["user"]
        await self.accept()

        if self.user.is_anonymous:
            await self.send_no_permissions()

        else:
            # Get group ID and validate.
            group_id = self.scope["url_route"]["kwargs"].get("group_id")
            try:
                await self.validate_group_id(group_id)
            except models.Group.DoesNotExist:
                await self.send_invalid_group_error()

            # Add channel name to the group.
            await self.channel_layer.group_add(
                f"crater_live_{self.group.id}",
                self.channel_name
            )

            await self.get_group_messages()

    async def disconnect(self, code):
        """Disconnect from the channel layer."""
        group_id = self.scope["url_route"]["kwargs"].get("group_id")
        await self.channel_layer.group_discard(
            f"crater_live_{group_id}",
            self.channel_name
        )

    async def receive(self, text_data=None, bytes_data=None):
        """Receive data being sent over the channel.

        Note:
            It only handles text data for now.

        """
        data = json.loads(text_data)
        await getattr(self, data.get("type"))(data.get("payload"))

    async def send_group_message(self, payload):
        """Create GroupMessage object and send it over channel layer."""
        message = payload.get("message")
        display_name = payload.get("display_name")
        group_message = await services.create_group_message(
            group=self.group,
            sender=self.user,
            message=message,
            display_name=display_name
        )

        if not group_message:
            return

        json_result = json.loads(JSONRenderer().render(group_message).decode("utf8"))
        await self.channel_layer.group_send(
            f"crater_live_{self.group.id}",
            {
                "type": "broadcast_new_group_message",
                "message": json_result
            }
        )

    async def send_group_reaction(self, payload):
        """Create GroupMessage object of type reaction and send it over channel layer."""
        reaction_id = payload.get("reaction")
        group_message = await services.create_group_message_reaction(
            group=self.group,
            sender=self.user,
            reaction_id=reaction_id,
        )

        if not group_message:
            return

        json_result = json.loads(JSONRenderer().render(group_message).decode("utf8"))
        await self.channel_layer.group_send(
            f"crater_live_{self.group.id}",
            {
                "type": "broadcast_new_group_message",
                "message": json_result
            }
        )    

    async def broadcast_new_group_message(self, event):
        """Broadcast message on channel group."""
        await self.send(json.dumps({
            "type": "new_group_message",
            "payload": event["message"]
        }))

    async def get_group_messages(self, event=None):
        """Retrieve group messages"""
        group_messages = await services.get_paginated_group_messages(self.group)
        results = json.loads(JSONRenderer().render(group_messages).decode("utf8"))
        # page = event.get("page")
        await self.send(json.dumps({
            "type": "group_messages_received",
            "payload": {
                "messages": results,
            }
        }))

    async def send_invalid_group_error(self, *args, **kwargs):
        """Send invalid group error."""
        await self.send(text_data=json.dumps({
            "type": "bad_request",
            "message": {"status_code": 400},
            "group": "invalid"
        }))
        print("triggered close")
        print(self.group.id)
        await self.close()

    async def send_no_permissions(self, *args, **kwargs):
        """Emit no permission event."""
        await self.send(text_data=json.dumps({
            "type": "access_denied",
            "message": {"status_code": 401},
            "user": "anonymous"
        }))
        await self.close()

    @database_sync_to_async
    def validate_group_id(self, group_id):
        """Validate if the group id is valid or not.

        Args:
            group_id(int): Id of the group the messages
                are being sent for.

        """
        self.group = models.Group.objects.get(id=group_id)

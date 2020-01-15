from chat.models import Message
from channels.db import database_sync_to_async

from chat.tasks import read_admin_messages_for_user


@database_sync_to_async
def create_message(message, sender, receiver=None, is_support=False):
    Message.objects.create(message=message, sender_id=sender, receiver_id=receiver, is_support=is_support)


@database_sync_to_async
def get_messages(receiver, is_support=False):
    Message.objects.filter(receiver_id=receiver, is_support=is_support)

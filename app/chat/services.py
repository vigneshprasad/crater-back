from chat.models import Message
from channels.db import database_sync_to_async


@database_sync_to_async
def create_message(message, sender, receiver, is_superuser=False):
    Message.objects.create(message=message, sender_id=sender, receiver_id=receiver, is_superuser=is_superuser)


@database_sync_to_async
def get_messages(receiver, is_superuser=False):
    Message.objects.filter(receiver_id=receiver, is_superuser=is_superuser)

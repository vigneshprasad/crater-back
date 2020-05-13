from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

from consumers.chat.models import Message
from freelance.celery import app


@app.task
def read_admin_messages_for_user(uuid):
    messages = Message.objects.filter(sender=uuid, is_support=True, is_read=False)
    if messages:
        messages_ids = list(messages.values_list('pk', flat=True))
        messages.update(is_read=True)
        layer = get_channel_layer()
        async_to_sync(layer.group_send)(uuid, {
            'type': 'admin_read_messages_to_user',
            'messages': messages_ids,
            'user_id': uuid
        })

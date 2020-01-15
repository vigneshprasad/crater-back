from chat.models import Message
from freelance.celery import app


@app.task
def read_admin_messages_for_user(uuid):
    Message.objects.filter(sender=uuid, is_support=True).update(is_read=True)

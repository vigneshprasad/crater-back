from celery.task import task
from django.contrib.auth import get_user_model

from integrations.freshchat import public as freshchat_public


@task
def send_welcome_crater_whatsapp(user_pk):
    """Send a welcome whatsapp message to the provided user.

    Args:
        user_pk(uuid): ID of User who signed up to Crater.

    """
    try:
        user = get_user_model().objects.get(pk=user_pk)
    except get_user_model().DoesNotExist:
        return

    freshchat_public.send_welcome_crater_whatsapp(user)

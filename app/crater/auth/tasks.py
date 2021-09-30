from celery.task import task

from integrations.freshchat import public as freshchat_public


@task
def send_welcome_crater_whatsapp(user):
    """Send a welcome whatsapp message to the provided user.

    Args:
        user(User): User who signed up to Crater.

    """
    freshchat_public.send_welcome_crater_whatsapp(user)

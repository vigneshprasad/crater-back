from celery.task import task

from integrations.freshchat import _freshchat_service as freshchat_service


@task
def create_or_update_freshchat_user(user):
    """Creates FreshChatUser for user"""
    freshchat_service.freshchat_whatsapp_service.create_or_update_user(
        user
    )

import logging

from celery import shared_task
from django.contrib.auth import get_user_model

from integrations.freshchat import freshchat_service as freshchat_service


@shared_task()
def create_or_update_freshchat_user(user_pk):
    """Creates FreshChatUser for user"""
    user = get_user_model().objects.get(pk=user_pk)
    # Added logging for debugging.
    logging.info(msg="Creating Freshchat User for {}".format(user.email))
    freshchat_service.freshchat_whatsapp_service.create_or_update_user(user)

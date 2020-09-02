import datetime
import logging

from celery import shared_task
from celery.schedules import crontab
from django.contrib.auth import get_user_model

from integrations.freshchat import freshchat_service as freshchat_service


@shared_task()
def create_or_update_freshchat_user(user_pk):
    """Creates FreshChatUser for user"""
    try:
        user = get_user_model().objects.get(pk=user_pk)
    except get_user_model().DoesNotExist:
        logging.info("User not found for {}, can't create Freshchat User".format(user_pk))
        return
    # Added logging for debugging.
    logging.info("Creating Freshchat User for {}".format(user.email))
    freshchat_service.freshchat_whatsapp_service.create_or_update_user(user)


# @shared_task(run_every=crontab(hour=11, minute=45))
def create_users_on_freshchat(users=None):
    """Creates Freshchat users who are not pushed to Freshchat yet.

    Args:
        users(User queryset): List of users to push onto Freshchat.

    """
    users_who_joined_today = get_user_model().filter(
        date_joined__gte=datetime.datetime.today()
    )
    users_without_freshchat_user = users_who_joined_today.exclude(
        freshchat_user__isnull=False
    )
    # Adding user's for debugging.
    users = users_without_freshchat_user if not users else users
    logging.info("Count of users without freshchat: {}".format(
        users_without_freshchat_user.count()
    ))
    for user in users:
        if not user.has_profile:
            continue
        freshchat_service.freshchat_whatsapp_service.create_or_update_user(user)

import datetime
import logging

from celery import shared_task
from django.contrib.auth import get_user_model

from communications.notifications import public as notification_public
from integrations.freshchat import freshchat_service as freshchat_service
from integrations.freshchat import models
from integrations.freshchat import constants
from integrations.freshchat import public
from resources.meetings import choices as meeting_constants
from resources.meetings import models as meeting_models
from resources.meetings import services as meeting_services


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


def get_users_for_opt_in_message():
    """Get users for opt in every sunday."""

    # Get users who got the last weeks messages.
    last_week_date = datetime.datetime.today() - datetime.timedelta(days=7)
    last_weeks_users_opt_in_message = models.Message.objects.filter(
        data__icontains=constants.MEETING_CONFIRMATION_INTENT,
        created_at__gte=last_week_date
    ).values_list('user', flat=True)

    # Add users who RSVPed attending for last weeks meetings.
    rsvped_user = []
    last_weeks_meetings = meeting_models.Meeting.objects.filter(
        start__gte=last_week_date
    )
    for meeting in last_weeks_meetings:
        for rsvp in meeting.rsvps.all():
            if rsvp.status != meeting_constants.MEETING_RSVP_STATUS_PENDING:
                rsvped_user.append(rsvp.participant.pk)

    # Merge all these users into a single list.
    users_for_opt_in = list(set(last_weeks_users_opt_in_message).union(set(rsvped_user)))

    # Remove users who have opted in for next week meeting already.
    for user_id in users_for_opt_in:
        latest_meeting_config = meeting_services.get_latest_active_meeting_config()
        if meeting_models.MeetingPreference.objects.filter(
                meeting=latest_meeting_config,
                user_id=user_id
        ):
            users_for_opt_in.remove(user_id)

    # Remove users who haven't had a meeting in past 30 days.
    last_month_date = datetime.datetime.today() - datetime.timedelta(days=30)
    for user_id in users_for_opt_in:
        if not meeting_models.Meeting.objects.filter(
            participants=user_id,
            start__gte=last_month_date
        ):
            users_for_opt_in.remove(user_id)

    # Remove users who don't have phone number.
    for user_id in users_for_opt_in:
        user = get_user_model().objects.get(pk=user_id)
        if not user.get_phone_number():
            users_for_opt_in.remove(user_id)

    emails = get_user_model().objects.filter(pk__in=users_for_opt_in).values_list('email', flat=True)

    return list(emails)


def send_opt_in_message(emails=None):
    if not emails:
        return
    users = get_user_model().objects.filter(email__in=emails)

    public.send_meeting_opt_in_messages(users=users)
    notification_public.send_optin_notifications_for_users(users=users)

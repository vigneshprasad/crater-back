import datetime
import logging

from celery.schedules import crontab
from celery.task import periodic_task

from communications.notifications import constants
from communications.notifications import models
from communications.notifications import private
from conversations import models as conversations_models


# @periodic_task(run_every=crontab(minute="*/10"))
def send_conversation_reminders_notifications(groups=None):
    """Sends notification reminders for people 10 minutes before their
        conversations.

    Args:
        groups(conversations.Group): Queryset of groups you want to
            send this reminder to. Added for testing.

    """
    now_time = datetime.datetime.now()
    start_datetime = now_time
    end_datetime = (now_time + datetime.timedelta(minutes=10))

    groups = conversations_models.Group.objects.filter(
        start__gt=start_datetime,
        start__lte=end_datetime,
    ) if not groups else groups

    notification = models.Notification.objects.get(name=constants.GROUP_REMINDER_NOTIFICATION)

    logging.info("Sending notification reminders for groups between {} - {}. Groups count: {}".format(
            start_datetime, end_datetime, groups.count()
    ))

    exclude_list = []
    for group in groups:
        for speaker in group.speakers.all():
            if speaker in exclude_list:
                continue
            private.send_notifications_for_group(speaker, notification, group)


# @periodic_task(run_every=crontab(minute="*/5"))
def send_conversation_live_reminder_notifications(groups=None):
    """Sends notification for people as soon as their meeting is live.

    Args:
        groups(conversations.Group): Queryset of groups you want to
            send this reminder to. Added for testing.

    """
    now_time = datetime.datetime.now()
    start_datetime = now_time
    end_datetime = (now_time + datetime.timedelta(minutes=5))

    groups = conversations_models.Group.objects.filter(
        start__gt=start_datetime,
        start__lte=end_datetime,
    ) if not groups else groups

    notification = models.Notification.objects.get(name=constants.GROUP_LIVE_NOTIFICATION)

    logging.info("Sending notification reminders for groups going live at {}. Groups count: {}".format(
            start_datetime, groups.count()
    ))

    exclude_list = []
    for group in groups:
        for speaker in group.speakers.all():
            if speaker in exclude_list:
                continue
            private.send_notifications_for_group(speaker, notification, group)

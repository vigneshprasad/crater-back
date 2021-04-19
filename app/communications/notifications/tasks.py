import datetime
import logging

from celery.schedules import crontab
from celery.task import periodic_task

from communications.notifications import constants
from communications.notifications import models
from communications.notifications import private
from conversations import models as conversations_models


@periodic_task(run_every=crontab(minute='*/10'))
def send_conversation_reminders_notifications(meetings=None):
    """Sends notification reminders for people 30 minutes before their meetings.

    Args:
        meetings(Meeting queryset): Queryset of meeting you want to send this
            reminder to. Added for testing.

    """
    now_time = datetime.datetime.now()
    start_datetime = now_time
    end_datetime = (now_time + datetime.timedelta(minutes=10))

    groups = conversations_models.Group.objects.filter(
        start__gt=start_datetime,
        start__lte=end_datetime,
    )
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

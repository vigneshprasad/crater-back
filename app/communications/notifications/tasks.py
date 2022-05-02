import datetime
import logging

from celery.schedules import crontab
from celery.task import periodic_task
from django.db.models import Count
from django.utils import timezone

from communications.notifications import constants, models, private
from conversations import models as conversations_models, constants as conversations_constants
from users import models as user_models, constants as user_constants


@periodic_task(run_every=crontab(minute="*/10"))
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

    notification = models.Notification.objects.filter(name=constants.GROUP_REMINDER_NOTIFICATION).first()

    if not notification:
        logging.error("Notification not present: {}".format(constants.GROUP_REMINDER_NOTIFICATION))
        return

    logging.info("Sending notification reminders for groups between {} - {}. Groups count: {}".format(
            start_datetime, end_datetime, groups.count()
    ))

    exclude_list = []
    for group in groups:
        for speaker in group.speakers.all():
            if speaker in exclude_list:
                continue
            exclude_list.append(speaker)

            notification_json = private.create_notification_json_from_notification(notification)
            notification_json["contents"]["en"] = notification_json["contents"]["en"].format(time=group.get_display_start_time(), topic=group.topic.name)
            data = {
                "obj_type": constants.OBJECT_TYPE_CONVERSATION,
                "group_id": group.id,
                "auto_connect": False
            }
            private.send_notification.delay(speaker.pk, notification_json, data=data)
            private.create_notification_log(speaker, notification, notification_json, data=data)


@periodic_task(run_every=crontab(minute="*/1"))
def send_conversation_live_reminder_notifications(groups=None):
    """Sends notification for people as soon as their meeting is live.

    Args:
        groups(conversations.Group): Queryset of groups you want to
            send this reminder to. Added for testing.

    """
    now_time = datetime.datetime.now()
    start_datetime = now_time

    groups = conversations_models.Group.objects.filter(
        start__year=start_datetime.year,
        start__month=start_datetime.month,
        start__day=start_datetime.day,
        start__hour=start_datetime.hour,
        start__minute=start_datetime.minute,
    ) if not groups else groups

    notification = models.Notification.objects.filter(name=constants.GROUP_LIVE_NOTIFICATION).first()

    if not notification:
        logging.error("Notification not present: {}".format(constants.GROUP_LIVE_NOTIFICATION))
        return

    logging.info("Sending notification reminders for groups going live at {}. Groups count: {}".format(
            start_datetime, groups.count()
    ))

    exclude_list = []

    for group in groups:
        notification_json = private.create_notification_json_from_notification(notification)
        data = {
            "obj_type": constants.OBJECT_TYPE_CONVERSATION,
            "group_id": group.id,
            "auto_connect": True
        }

        for speaker in group.speakers.all():
            if speaker in exclude_list:
                continue

            exclude_list.append(speaker)
            private.send_notification.delay(speaker.pk, notification_json, data=data)
            private.create_notification_log(speaker, notification, notification_json, data=data)


@periodic_task(run_every=crontab(hour="*/1"))
def send_groups_going_live_notifications(groups=None):
    """Sends notification for groups going live every hour.

    Args:
        groups(queryset/list): Group we want to send notification
            to. Only for testing purposes.

    """
    now = timezone.now()
    next_hour_time = now + datetime.timedelta(hours=1)

    groups_going_live = conversations_models.Group.objects.filter(
        type=conversations_constants.GROUP_TYPE_WEBINAR_ENUM,
        start__gte=now,
        start__lt=next_hour_time
    ).annotate(
        attendees_count=Count("attendees")
    ).order_by("-attendees_count")

    group_going_live_highest_rsvp = groups_going_live.first()
    if not group_going_live_highest_rsvp:
        return

    notification = models.Notification.objects.filter(name=constants.STREAM_GOING_LIVE_NOTIFICATION).first()

    if not notification:
        logging.error("Notification not present: {}".format(constants.STREAM_GOING_LIVE_NOTIFICATION))
        return

    logging.info("Sending notification reminders for groups going live during {} - {}. Group: {}".format(
            now, next_hour_time, group_going_live_highest_rsvp
    ))

    notification_json = private.create_notification_json_from_notification(notification)
    data = {
        "obj_type": constants.OBJECT_TYPE_CONVERSATION,
        "group_id": group_going_live_highest_rsvp.id,
        "auto_connect": True
    }

    # TODO(Nishant): Which users should this go to.
    all_users = user_models.User.objects.filter(
        group__name=user_constants.CRATER_CLUB_GROUP
    )
    for user in all_users:
        private.send_notification.delay(user.pk, notification_json, data=data)
        private.create_notification_log(user, notification, notification_json, data=data)

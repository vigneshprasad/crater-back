import datetime
import logging

from celery import shared_task
from django.db.models import Count
from django.utils import timezone

from communications.notifications import constants, models, private
from conversations import constants as conversation_constants, models as conversations_models
from users import constants as user_constants, models as user_models


@shared_task(bind=True)
def send_groups_going_live_notifications(groups=None):
    """Sends notification for groups going live every hour.

    Args:
        groups(queryset/list): Group we want to send notification
            to. Only for testing purposes.

    """
    now = timezone.now()
    end_time = now + datetime.timedelta(hours=2)

    groups_going_live = conversations_models.Group.objects.filter(
        type=conversation_constants.GROUP_TYPE_WEBINAR_ENUM,
        start__gte=now,
        start__lt=end_time
    ).annotate(
        attendees_count=Count("attendees")
    ).order_by("-attendees_count") if not groups else groups

    group_going_live_highest_rsvp = groups_going_live.first()
    if not group_going_live_highest_rsvp:
        return False

    stream_going_live_notification = models.Notification.objects.filter(name=constants.STREAM_GOING_LIVE_NOTIFICATION).first()

    if not stream_going_live_notification:
        logging.error("Notification not present: {}".format(constants.STREAM_GOING_LIVE_NOTIFICATION))
        return False

    logging.info("Sending notification for group going live during {} - {}. Group: {}".format(
            now, end_time, group_going_live_highest_rsvp
    ))

    stream_going_live_notification_json = private.create_notification_json_from_notification(
        stream_going_live_notification
    )
    data = {
        "obj_type": constants.OBJECT_TYPE_STREAM,
        "group_id": group_going_live_highest_rsvp.id,
        "auto_connect": True
    }

    # Sending to all users.
    users = user_models.User.objects.filter(
        group__name=user_constants.CRATER_CLUB_GROUP
    )
    user_pks = users.values_list("pk", flat=True)

    private.send_bulk_notifications(user_pks, stream_going_live_notification_json, data=data)
    private.create_notification_logs(
        users,
        stream_going_live_notification,
        stream_going_live_notification_json,
        data=data
    )

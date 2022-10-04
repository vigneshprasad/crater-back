import datetime
import logging

from celery import shared_task
from django.db.models import Count
from django.utils import timezone

from communications.notifications import constants, models, private
from conversations import constants as conversation_constants, models as conversations_models
from users import constants as user_constants, models as user_models


@shared_task()
def send_groups_going_live_notifications(notification_name, groups=None):
    """Sends notification for groups going live every hour.

    Args:
        notification_name(str): Name of notification we are sending to the
            users.
        groups(queryset/list): Group we want to send notification
            to. Only for testing purposes.

    """
    if not notification_name:
        return False

    now = timezone.now()
    end_time = now + datetime.timedelta(hours=2)

    groups_going_live = conversations_models.Group.objects.filter(
        type=conversation_constants.GROUP_TYPE_WEBINAR_ENUM,
        start__gte=now,
        start__lt=end_time,
        is_published=True,
        privacy=conversation_constants.GROUP_PRIVACY_PUBLIC
    ).annotate(
        attendees_count=Count("attendees")
    ).order_by("-attendees_count")

    group_going_live_highest_rsvp = groups_going_live.first()
    if not group_going_live_highest_rsvp:
        return False

    stream_going_live_notification = None
    stream_going_live_notification_json = None
    data = None

    if notification_name == constants.STREAM_GOING_LIVE_FIRST_NOTIFICATION:
        stream_going_live_notification = models.Notification.objects.filter(
            name=constants.STREAM_GOING_LIVE_FIRST_NOTIFICATION
        ).first()
        stream_going_live_notification_json = private.create_notification_json_from_notification(
            stream_going_live_notification
        )
        stream_going_live_notification_json["contents"]["en"] = stream_going_live_notification_json["contents"]["en"].format(
            topic_name=group_going_live_highest_rsvp.topic.name.title()
        )
        data = {
            "obj_type": constants.OBJECT_TYPE_STREAM,
            "group_id": group_going_live_highest_rsvp.id,
            "auto_connect": True
        }

    elif notification_name == constants.STREAM_GOING_LIVE_SECOND_NOTIFICATION:
        stream_going_live_notification = models.Notification.objects.filter(
            name=constants.STREAM_GOING_LIVE_SECOND_NOTIFICATION
        ).first()
        stream_going_live_notification_json = private.create_notification_json_from_notification(
            stream_going_live_notification
        )
        host = group_going_live_highest_rsvp.host
        stream_going_live_notification_json["contents"]["en"] = stream_going_live_notification_json["contents"]["en"].format(
            creator_name=host.display_name
        )
        creator = host.creator if hasattr(host, "creator") else None
        if creator:
            data = {
                "obj_type": constants.OBJECT_TYPE_CREATOR,
                "creator_id": creator.id,
                "auto_connect": True
            }

    elif notification_name == constants.STREAM_GOING_LIVE_THIRD_NOTIFICATION:
        stream_going_live_notification = models.Notification.objects.filter(
            name=constants.STREAM_GOING_LIVE_THIRD_NOTIFICATION
        ).first()
        stream_going_live_notification_json = private.create_notification_json_from_notification(
            stream_going_live_notification
        )

    if not stream_going_live_notification:
        logging.info("Sending notification for group going live during {} - {}. Group: {}".format(
                now, end_time, group_going_live_highest_rsvp
        ))
        return False

    # Sending to all users.
    users = user_models.User.objects.filter(groups__name=user_constants.CRATER_CLUB_GROUP)
    user_pks = users.values_list("pk", flat=True)

    private.send_bulk_notifications(
        user_pks=user_pks,
        notification_id=stream_going_live_notification.id,
        notification_json=stream_going_live_notification_json,
        data=data
    )

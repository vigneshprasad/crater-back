import copy
import logging

from celery.task import task
from django.contrib.auth import get_user_model

from communications.notifications import constants, models
from integrations.onesignal.services import one_signal_service
from integrations.onesignal import models as onesignal_models

LOGGER = logging.getLogger(__name__)


def create_notification_json_from_notification(notification):
    """Returns a notification json for a provided notification."""
    return {
        "headings": {
            "en": notification.headings
        },
        "contents": {
            "en": notification.contents
        },
        "small_icon": notification.small_icon,
        "large_icon": notification.large_icon,
        "android_accent_color": notification.android_accent_color,
        "buttons": notification.buttons
    }


def create_notification_logs(user_pks, notification_id, notification_json, data=None):
    """Creates notification log for a notification and json sent.

    Args:
        user_pks(Queryset/List): ID's of users the notification was sent to.
        notification_id(int): ID of notification object that was used.
        notification_json(JSON): Actual notification json sent to the client.
        data(JSON): Addition data sent to the client.

    """
    notification_logs = []
    for user_pk in user_pks:
        notification_logs.append(models.NotificationLog(
            user_id=user_pk,
            notification_id=notification_id,
            notification_json=notification_json,
            data=data
        ))
    # Bulk create all notifications.
    return models.NotificationLog.objects.bulk_create(notification_logs)


def create_notification_log(user_pk, notification_id, notification_json, data=None):
    """Creates notification log for a notification and json sent.

    Args:
        user_pk(str): ID of user the notification was sent to.
        notification_id(int): ID of notification object that was used.
        notification_json(JSON): Actual notification json sent to the client.
        data(JSON): Addition data sent to the client.

    """
    try:
        return models.NotificationLog.objects.create(
            user_id=user_pk,
            notification_id=notification_id,
            notification_json=notification_json,
            data=data
        )
    except Exception as e:
        LOGGER.error(str(e))
        return False


@task()
def send_notification(user_pk, notification_id, notification_json, data=None):
    """Sends notification to a user.

    Args:
        user_pk(str): User ID of the user notification should be sent to.
        notification_id(int): ID of notification object in our backend.
        notification_json(JSON): Actual notification json sent to the client.
        data(JSON): Extra data sent to the client.

    Returns:
        notification_json(JSON): Final JSON that was sent to the client.

    """
    initial_notification_json = copy.deepcopy(notification_json)
    user = get_user_model().objects.get(pk=user_pk)
    devices = user.get_devices()
    if not devices:
        return False

    notification_json["data"] = data

    for device in devices:
        one_signal_service.send_notification(
            device.os_id,
            notification_json=notification_json
        )

    # Create notification log for the notification sent.
    create_notification_log(
        user_pk,
        notification_id=notification_id,
        notification_json=initial_notification_json,
        data=data
    )

    return True


@task()
def send_bulk_notifications(user_pks, notification_id, notification_json, data=None):
    """Sends notification to list of users.

    Args:
        user_pks(list): List of User IDs of the users notification should be sent to.
        notification_id(int): ID of notification object in our backend.
        notification_json(JSON): Actual notification json sent to the client.
        data(JSON): Extra data sent to the client.

    Returns:
        notification_json(JSON): Final JSON that was sent to the client.

    """
    initial_notification_json = copy.deepcopy(notification_json)
    devices = onesignal_models.OneSignalDevice.objects.filter(user_id__in=user_pks)
    user_os_ids = list(devices.values_list("os_id", flat=True))
    if data:
        notification_json["data"] = data

    count = 0
    count_of_os_ids = len(user_os_ids)

    while count < count_of_os_ids:
        max_count = count + constants.MAX_PLAYER_IDS_FOR_BULK_NOTIFICATIONS
        # Sending only 2000 os_ids in one go because of max player ids limit.
        os_ids = user_os_ids[count: max_count]
        one_signal_service.send_bulk_notification(
            os_ids,
            notification_json=notification_json
        )
        count = max_count

    # Create notification log for the notifications sent.
    create_notification_logs(
        user_pks,
        notification_id=notification_id,
        notification_json=initial_notification_json,
        data=data
    )
    return True

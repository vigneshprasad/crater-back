from celery.task import task

from communications.notifications import models
from utils.one_signal_service import os_service


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


def create_notification_log(user, notification, notification_json):
    """Creates notification log for a notification and json sent.

    Args:
        user(User): User the notification was sent to.
        notification(Notification): Notification object that was used.
        notification_json(JSON): Actual notification json sent to the client.

    """
    return models.NotificationLogs.objects.create(
        user=user,
        notification=notification,
        notification_json=notification_json
    )


@task()
def send_notification(user, notification_json, data=None):
    """Sends notification to a user.

    Args:
        user(User): User the notification should be sent to.
        notification_json(JSON): Actual notification json sent to the client.
        data(JSON): Extra data sent to the client.

    Returns:
        notification_json(JSON): Final JSON that was sent to the client.

    """
    devices = user.devices.filter(is_active=True)
    notification_json["data"] = data

    for device in devices:
        os_service.send_notification(
            device.os_id,
            notification_json=notification_json
        )

    return notification_json

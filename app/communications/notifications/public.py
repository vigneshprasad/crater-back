import logging

from communications.notifications import models
from communications.notifications import constants
from communications.notifications import private


def send_conversation_create_notification_for_group(group):
    """Sends notification to all users in a group."""
    users = group.speakers.all()
    for user in users:
        send_conversation_created_notification(user, group)


def send_conversation_created_notification(user, group):
    """Sends notification for conversation created.

     Args:
         user(User): User to whom we are sending the notification.
         group(Group): Group the user is associated with.

     """
    # TODO(Nishant): Use this is group creation script.
    notification = models.Notification.objects.filter(
        name=constants.GROUP_CONVERSATION_CREATED,
        is_active=True
    ).first()

    if not notification:
        logging.error("Notification not present: {}".format(constants.GROUP_CONVERSATION_CREATED))
        return

    # Get the notification json and append variables to it.
    notification_json = private.create_notification_json_from_notification(notification)
    notification_json["contents"]["en"].format(time=group.get_display_start_time(), topic=group.topic.name)
    # Get data for the notification.
    data = {
        "obj_type": constants.OBJECT_TYPE_CONVERSATIONS,
        "group_id": group.id
    }
    sent_notification_json = private.send_notification.delay(user, notification_json, data=data)
    private.create_notification_log(user, notification, sent_notification_json)


def send_optin_notifications(user):
    """Sends notification for conversation created.

     Args:
         user(User): User to whom we are sending the notification.

     """
    # TODO(Nishant): Add this to sunday script for optin.
    notification = models.Notification.objects.filter(
        name=constants.OPTIN_NOTIFICATION,
        is_active=True
    ).first()

    if not notification:
        logging.error("Notification not present: {}".format(constants.OPTIN_NOTIFICATION))
        return

    # Create notification json and data.
    notification_json = private.create_notification_json_from_notification(notification)
    data = {
        "obj_type": constants.OBJECT_TYPE_CREATE_CONVERSATIONS
    }
    sent_notification_json = private.send_notification.delay(user, notification_json, data=data)
    private.create_notification_log(user, notification, sent_notification_json)

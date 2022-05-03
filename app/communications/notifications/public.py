import logging

from django.contrib.auth import get_user_model

from communications.notifications import models, constants, private
from crater.creator import public as creator_public


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
    notification_json["contents"]["en"] = notification_json["contents"]["en"].format(time=group.get_display_start_time(), day=group.get_display_day())
    # Get data for the notification.
    data = {
        "obj_type": constants.OBJECT_TYPE_CONVERSATION,
        "group_id": group.id
    }
    private.send_notification.delay(user.pk, notification_json, data=data)
    private.create_notification_log(user, notification, notification_json, data=data)


def send_optin_notifications_for_users(users=None):
    """Wrapper to send notification to multiple users.

    Args:
        users(List(User)): List of users we want to send
            optin notifications.

    """
    if not users:
        return False

    for user in users:
        send_optin_notifications(user)


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
        "obj_type": constants.OBJECT_TYPE_CREATE_CONVERSATION
    }
    private.send_notification.delay(user.pk, notification_json, data=data)
    private.create_notification_log(user, notification, notification_json, data=data)


def send_reminder_notifications_for_stream(group):
    """Send reminder notification to attendees and followers
        of a group.

    Args:
        group(Group): Group we are sending reminder notifications for.

    """
    followers = []
    host = group.host
    creator = creator_public.get_creator_for_user(host)

    if creator:
        # Add users followers if creator is present.
        followers = list(creator.followers.filter(
            notify=True
        ).values_list("user_id", flat=True))

    # Get attendees for the group.
    attendees = list(group.attendees.values_list("pk", flat=True))

    # Create an exhaustive list of users to send reminder to.
    users_to_remind = list(set(followers + attendees))
    users = get_user_model().objects.filter(pk__in=users_to_remind)

    for user in users:
        send_reminder_notifications_for_user_and_stream(user, group)


def send_reminder_notifications_for_user_and_stream(user, group):
    """Send reminder notification for a user and a group.

    Args:
        user(User): User we are sending the notification to.
        group(Group): Group we are sending the reminder for.

    """
    stream_reminder_notification = models.Notification.objects.filter(
        name=constants.STREAM_REMINDER_NOTIFICATION,
        is_active=True
    ).first()

    if not stream_reminder_notification:
        logging.error("Notification not present: {}".format(constants.STREAM_REMINDER_NOTIFICATION))
        return

    # Get the notification json and append variables to it.
    stream_reminder_notification_json = private.create_notification_json_from_notification(stream_reminder_notification)
    # TODO(Nishant): Add the contents here.
    stream_reminder_notification_json["contents"]["en"] = stream_reminder_notification_json["contents"]["en"].format(
        time=group.get_display_start_time(),
        day=group.get_display_day()
    )
    # Get data for the notification.
    data = {
        "obj_type": constants.OBJECT_TYPE_CONVERSATION,
        "group_id": group.id,
        "auto_connect": True
    }

    # TODO(Nishant): Check if we can convert this to bulk notifications.
    private.send_notification.delay(user.pk, stream_reminder_notification_json, data=data)
    private.create_notification_log(
        user,
        stream_reminder_notification,
        stream_reminder_notification_json,
        data=data
    )

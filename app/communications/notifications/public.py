from communications.notifications import models
from communications.notifications import constants
from communications.notifications import private


def send_conversation_created_notification(user, group):
    # TODO(Nishant): Use this is group creation script.
    notification = models.Notification.objects.get(name=constants.GROUP_CONVERSATION_CREATED)
    private.send_notifications_for_group(user, notification, group)


def send_optin_notifications(user):
    # TODO(Nishant): Add this to sunday script for optin.
    notification = models.Notification.objects.get(name=constants.OPTIN_NOTIFICATION)
    private.send_optin_notifications_for_user(user, notification)

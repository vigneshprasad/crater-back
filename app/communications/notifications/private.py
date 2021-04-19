from django.conf import settings

from utils.deep_link_service import deep_link_service
from utils.one_signal_service import os_service


def send_notifications_for_group(user, notification, group):
    group_link = "https://{}/group?id={}".format(settings.FRONT_URL, group.id)
    deeplink = deep_link_service.make_firebase_deep_link(group_link)

    content = notification.content
    content["url"] = deeplink

    player_id = user.devices.filter(is_active=True).first()
    if not player_id:
        return False

    os_service.send_push([player_id], content, data=None)


def send_optin_notifications_for_user(user, notification):
    # TODO(Nishant): Add deeplink to start conversation create.
    deeplink = ""

    content = notification.content
    content["url"] = deeplink

    player_id = user.devices.filter(is_active=True).first()
    if not player_id:
        return False

    os_service.send_push([player_id], content, data=None)

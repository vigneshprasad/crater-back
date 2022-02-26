from django.conf import settings

from conversations import constants


def get_link_for_webinar(group):
    """Returns the live/session link for a group."""
    front_url = settings.CRATER_FRONT_URL
    session_url = front_url + constants.SESSION_URL_WITH_GROUP.format(
        group_id=group.id
    )
    return session_url

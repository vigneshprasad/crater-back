import uuid

from integrations.agora.token_builder import rtc_token_builder
from integrations.agora import constants


def generate_token_for_user_and_group(user, group):
    """Generates a WebRTC token for a user and group.

    Args:
        user: User. The user trying to join the group meeting
        group: Group. The group user is trying to join.

    """
    return rtc_token_builder.build_token_with_uid(
        channel_name=_generate_channel_name(group),
        uid=user.pk,
        role=constants.ROLE_ATTENDEE
    )


def _generate_channel_name(group):
    """Generate a random string for agora channel.

    Args:
        group: Group. The group we are creating the channel
            for.

    """
    return uuid.uuid4().hex + " " + str(group.id)

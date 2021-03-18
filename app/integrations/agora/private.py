import uuid

from integrations.agora.token_builder import RtcTokenBuilder
from integrations.agora import constants, models


def generate_token_for_user_and_group(user, channel_id, channel_type=models.AgoraRTCInfo.ChannelType.GROUP):
    """Generates a WebRTC token for a user and group.

    Args:
        user: User. The user trying to join the group meeting
        channel_id: Id of channel user is trying to connect
        channel_type: Channel type either group or 1:1

    """
    rtc_info = _get_rtc_model_info(channel_id, channel_type)
    rtc_token_builder = RtcTokenBuilder()

    token = rtc_token_builder.build_token_with_account(
        channel_name=rtc_info.channel_name,
        account=user.pk,
        role=constants.ROLE_ATTENDEE
    )

    return token, rtc_info.channel_name


def _get_rtc_model_info(channel_id, channel_type):
    rtc_info, _ = models.AgoraRTCInfo.objects.get_or_create(
        channel_id=channel_id,
        type=channel_type,
        defaults={
            "channel_name": _generate_channel_name(channel_id)
        }
    )

    return rtc_info


def _generate_channel_name(channel_id):
    """Generate a random string for agora channel.

    Args:
        channel_id: Integer. id of group or 1:1 meeting

    """
    return uuid.uuid4().hex + " " + str(channel_id)

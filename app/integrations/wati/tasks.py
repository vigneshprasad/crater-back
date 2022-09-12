import pytz
from celery.task import task
from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils import timezone

from conversations import constants as conversation_constants, models as conversation_models
from integrations.wati import constants, private
from integrations.wati.services import wati_service_8953


@task
def send_stream_setup_whatsapp_to_creator(group_id):
    """Send email to creator when his stream is set up on the platform.

    Args:
        group_id(int): ID of the group we are sending the email for.

    """
    group = conversation_models.Group.objects.get(id=group_id)
    if not _can_send_setup_message_for_group(group):
        return False

    host = group.host
    creator = host.creator if hasattr(host, "creator") else None
    poc = creator.point_of_contact if creator else None
    poc_name, poc_number = (poc.display_name, poc.get_phone_number()) if \
        poc else (constants.DEFAULT_POC_NAME, constants.DEFAULT_POC_NUMBER)

    template_data = [
        {"name": "stream_image", "value": group.get_image_url()},
        {"name": "1", "value": host.display_name},
        {"name": "2", "value": group.get_display_day()},
        {"name": "3", "value": group.get_display_start_time()},
        {"name": "4", "value": poc_name},
        {"name": "5", "value": poc_number},
        {"name": "session_id", "value": group.id},
    ]

    return wati_service_8953.send_template_message(
        user=host,
        template_name=constants.STREAM_SETUP_CREATOR_8953,
        broadcast_name=constants.STREAM_SETUP_CREATOR_8953 + "_{}-{}".format(host.display_name, group.id),
        template_data=template_data
    )


@task
def send_stream_setup_whatsapp_to_followers(group_id):
    """Send email to creator when his stream is set up on the platform.

    Args:
        group_id(int): ID of the group we are sending the email for.

    """
    group = conversation_models.Group.objects.get(id=group_id)
    if not _can_send_setup_message_for_group(group):
        return False

    host = group.host
    creator = host.creator if hasattr(host, "creator") else None
    if not creator:
        return False

    host_followers_user_ids = creator.followers.filter(notify=True).values_list("user_id", flat=True)
    host_followers = list(get_user_model().objects.filter(pk__in=host_followers_user_ids))

    host_followers_list_with_one_plus_streams = []
    for follower in host_followers:
        streams_watched = follower.dyte_participant.filter(
            dyte_meeting__group__type=conversation_constants.GROUP_TYPE_WEBINAR_ENUM,
            last_online_at__isnull=False
        ).count()
        if not streams_watched:
            continue
        host_followers_list_with_one_plus_streams.append(follower)

    receivers = []
    for follower in host_followers_list_with_one_plus_streams:
        # Check if we can send whatsapp to this user.
        if not private.can_send_whatsapp_for_user(follower):
            continue

        data = {
            "whatsappNumber": follower.get_phone_number(),
            "customParams": [
                {"name": "stream_image", "value": group.get_image_url()},
                {"name": "creator_name", "value": host.display_name},
                {"name": "stream_title", "value": group.topic.name.title()},
                {"name": "stream_time", "value": group.get_display_start()},
                {"name": "1", "value": group.id}
            ]
        }
        receivers.append(data)

    if not receivers:
        return False

    return wati_service_8953.send_template_messages(
        template_name=constants.STREAM_SETUP_FOLLOWERS_8953,
        receivers=receivers,
        broadcast_name=constants.STREAM_SETUP_FOLLOWERS_8953 + "_{}-{}".format(host.display_name, group.id)
    )


def _can_send_setup_message_for_group(group):
    """Check if stream setup message can be sent
        based on group starting time.

    Args:
        group(Group): Group that was just published.

    """
    group_start = group.start
    if not timezone.is_aware(group_start):
        group_start = timezone.make_aware(group_start, timezone=pytz.timezone(settings.TIME_ZONE))

    now_time = timezone.now()
    if not timezone.is_aware(now_time):
        now_time = timezone.make_aware(now_time, timezone=pytz.timezone(settings.TIME_ZONE))

    # Don't send the email if the group start is less than now time.
    if group_start <= now_time:
        return False

    diff = now_time - group_start
    diff_minutes = diff.seconds / 60
    # If the group is marked published within 30 minutes of group start
    # don't send the published email.
    if diff_minutes < 30:
        return False

    return True

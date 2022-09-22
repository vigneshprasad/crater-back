import logging

import pytz
from django.conf import settings
from django.dispatch import receiver
from django.utils import timezone

from conversations import signals as conversations_signals
from integrations.dyte import models as dyte_models
from integrations.wati import constants, private, tasks
from integrations.wati.services import wati_service_8953

LOGGER = logging.getLogger(__name__)


@receiver(conversations_signals.group_recording_published)
def send_whatsapp_to_users_for_recording_published(sender, recording, *args, **kwargs):
    """Send email to the creator of a stream, once their recording
        is published and available to them.

    Args:
        sender(GroupRecording.__class__): Recording's class representation.
        recording(GroupRecording): Recording that was published.

    """
    group = recording.group
    attendees = group.attendees.all()

    attendees_who_missed_stream = []
    # Get all dyte participants who missed the stream.
    dyte_participant_who_missed_stream = dyte_models.DyteMeetingParticipant.objects.filter(
        dyte_meeting__group=group,
        participant__in=attendees,
        last_online_at__isnull=True
    )
    for attendee in attendees:
        if not dyte_participant_who_missed_stream.filter(
            participant=attendee,
        ).exists():
            continue
        attendees_who_missed_stream.append(attendee)

    receivers = []
    for attendee in attendees_who_missed_stream:
        # Check if we can send whatsapp to this user.
        if not private.can_send_whatsapp_for_user(attendee):
            continue

        data = {
            "whatsappNumber": attendee.get_phone_number(),
            "customParams": [
                {"name": "stream_image", "value": group.get_image_url()},
                {"name": "1", "value": group.host.display_name},
                {"name": "2", "value": group.topic.name.title()},
                {"name": "3", "value": group.id}
            ]
        }
        receivers.append(data)

    if not receivers:
        return False

    return wati_service_8953.send_template_messages(
        template_name=constants.STREAM_RECORDING_PUBLISHED_ATTENDEE_8953,
        receivers=receivers,
        broadcast_name=constants.STREAM_RECORDING_PUBLISHED_ATTENDEE_8953 + "_{}".format(group.id)
    )


@receiver(conversations_signals.group_recording_published)
def send_whatsapp_to_creator_for_recording_published(sender, recording, *args, **kwargs):
    """Send email to the creator of a stream, once their recording
        is published and available to them.

    Args:
        sender(GroupRecording.__class__): Recording's class representation.
        recording(GroupRecording): Recording that was published.

    """
    group = recording.group
    host = group.host

    template_data = [
        {"name": "1", "value": host.display_name},
        {"name": "session_id", "value": group.id}
    ]

    return wati_service_8953.send_template_message(
        user=host,
        template_name=constants.STREAM_RECORDING_PUBLISHED_CREATOR_8953,
        broadcast_name=constants.STREAM_RECORDING_PUBLISHED_CREATOR_8953 + "_{}-{}".format(group.id, host.display_name),
        template_data=template_data
    )


@receiver(conversations_signals.group_marked_published)
def send_whatsapp_for_stream_setup_to_creator(sender, group, *args, **kwargs):
    """Sends whatsapp once a creator's stream is set up on the platform.

    Args:
        sender(Group.__class__): Class repr of group that was published.
        group(Group): Group that was marked published.

    """
    if not _can_send_setup_message_for_group(group):
        return False

    tasks.send_stream_setup_whatsapp_to_creator.apply_async(
        args=(group.id, ),
        countdown=120
    )


@receiver(conversations_signals.group_marked_published)
def send_whatsapp_for_stream_setup_to_followers(sender, group, *args, **kwargs):
    """Sends whatsapp to creator's followers once their
        stream is set up on the platform.

    Args:
        sender(Group.__class__): Class repr of group that was published.
        group(Group): Group that was marked published.

    """
    if not _can_send_setup_message_for_group(group):
        return False

    tasks.send_stream_setup_whatsapp_to_followers.apply_async(
        args=(group.id, ),
        countdown=180
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

    diff = group_start - now_time
    diff_minutes = diff.total_seconds() / 60
    # If the group is marked published within 30 minutes of group start
    # don't send the published email.
    if diff_minutes < 30:
        return False

    return True

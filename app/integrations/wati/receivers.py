import logging

from django.dispatch import receiver

from conversations import signals as conversations_signals
from integrations.dyte import models as dyte_models
from integrations.wati import constants, private
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

    try:
        topic_image_url = group.topic.image.url
    except (ValueError, AttributeError) as e:
        LOGGER.error("Topic image unavailable: {}".format(group.id))
        topic_image_url = ""

    receivers = []
    for attendee in attendees_who_missed_stream:
        # Check if we can send whatsapp to this user.
        if not private.can_send_whatsapp_for_user(attendee):
            continue

        data = {
            "whatsappNumber": attendee.get_phone_number(),
            "customParams": [
                {"name": "stream_image", "value": topic_image_url},
                {"name": "1", "value": group.host.display_name},
                {"name": "2", "value": group.topic.name.title()},
                {"name": "3", "value": group.id}
            ]
        }
        receivers.append(data)

    if not receivers:
        return False

    return wati_service_8953.send_template_messages(
        template_name=constants.STREAM_MISSED_UPLOADED_ATTENDEE_8953,
        receivers=receivers,
        broadcast_name=constants.STREAM_MISSED_UPLOADED_ATTENDEE_8953 + "_{}".format(
            group.id
        )
    )

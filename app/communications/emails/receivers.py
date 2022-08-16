from django.dispatch import receiver

from communications.emails import constants, private, tasks
from conversations import signals as conversations_signals
from crater.creator import signals as creator_signals, public as creator_public


@receiver(conversations_signals.group_recording_published)
def send_email_to_creator_for_recording_published(sender, recording, *args, **kwargs):
    """Send email to the creator of a stream, once their recording
        is published and available to them.

    Args:
        sender(GroupRecording.__class__): Recording's class representation.
        recording(GroupRecording): Recording that was published.

    """
    group = recording.group
    host = group.host
    to_email = host.email
    # TODO(Nishant): What to do here is creator is not present.
    creator = host.creator if hasattr("creator", host) else None
    if not creator:
        return None

    merge_vars = {
        to_email:
            {
                "creator_page": "https://crater.club/creator/{}".format(creator.slug),
                "video_page": "https://crater.club/video/{}".format(group.id)
            }
    }

    private.send_email(
        subject="Video for stream on: {}".format(group.topic.name),
        to=[host.email],
        template_name=constants.CREATOR_RECORDING_PUBLISHED_TEMPLATE,
        merge_vars=merge_vars,
        from_email=""
    )


@receiver(creator_signals.creator_followed)
def send_email_for_50_subscribers_to_creator(sender, follower, *args, **kwargs):
    creator = follower.creator
    subscriber_count = creator_public.get_subscriber_count_for_creator(creator)
    if subscriber_count != 50:
        return

    to_email = creator.user.email
    private.send_email(
        subject="You have gained 50 followers on Crater!",
        to=[to_email],
        template_name=constants.CREATOR_50_FOLLOWERS_TEMPLATE,
        merge_vars={},
        from_email=""
    )


@receiver(conversations_signals.group_marked_published)
def send_email_for_stream_setup_to_creator(sender, group, *args, **kwargs):
    tasks.send_stream_setup_email_to_creator.apply_async(
        args=(group.id, ),
        countdown=120
    )

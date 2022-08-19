from django.dispatch import receiver
from django.utils import timezone

from communications.emails import constants, private, tasks
from conversations import signals as conversations_signals, public as conversations_public
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
    creator = host.creator if hasattr("creator", host) else None
    if not creator:
        return None

    merge_vars = {
        to_email:
            {
                "creator_page": creator.get_page_link(),
                "video_page": conversations_public.get_video_page_for_webinar(group)
            }
    }

    private.send_email_for_user(
        subject="Video for stream on: {}".format(group.topic.name),
        user=host,
        template_name=constants.CREATOR_RECORDING_PUBLISHED_TEMPLATE,
        merge_vars=merge_vars,
        from_email="hello@worknetwork.in"
    )


@receiver(creator_signals.creator_50_subscribers)
def send_email_for_50_subscribers_to_creator(sender, creator, *args, **kwargs):
    """Sends email once a creators has 50 subscribers.

    Args:
        sender(Creator.__class__): Class repr of creator that has reached
            50 subscribers.
        creator(Group): Creator that has reached 50 subscribers.

    """
    private.send_email_for_user(
        subject="You have gained 50 followers on Crater!",
        user=creator.user,
        template_name=constants.CREATOR_50_FOLLOWERS_TEMPLATE,
        merge_vars={},
        from_email=""
    )


@receiver(conversations_signals.group_marked_published)
def send_email_for_stream_setup_to_creator(sender, group, *args, **kwargs):
    """Sends email once a creators stream is set up on the platform.

    Args:
        sender(Group.__class__): Class repr of group that was published.
        group(Group): Group that was marked published.

    """
    group_start = group.start
    now_time = timezone.now()
    # Don't send the email if the group start is less than now time.
    if group_start <= now_time:
        return

    diff = now_time - group_start
    diff_minutes = diff.seconds / 60
    # If the group is marked published within 30 minutes of group start
    # don't send the published email.
    if diff_minutes < 30:
        return

    tasks.send_stream_setup_email_to_creator.apply_async(
        args=(group.id, ),
        countdown=120
    )

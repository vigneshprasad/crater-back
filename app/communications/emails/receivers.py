from django.dispatch import receiver
from django.utils import timezone

from communications.emails import constants, private, tasks
from conversations import public as conversations_public, signals as conversations_signals
from crater.creator import signals as creator_signals


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
    creator = host.creator if hasattr(host, "creator") else None
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
        subject=constants.CREATOR_RECORDING_PUBLISHED_TEMPLATE_SUBJECT,
        user=host,
        template_name=constants.CREATOR_RECORDING_PUBLISHED_TEMPLATE,
        merge_vars=merge_vars,
        from_email=constants.CREATOR_RECORDING_PUBLISHED_FROM_EMAIL
    )


@receiver(creator_signals.creator_50_subscribers)
def send_email_for_50_subscribers_to_creator(sender, creator, *args, **kwargs):
    """Sends email once a creators has 50 subscribers.

    Args:
        sender(Creator.__class__): Class repr of creator that has reached
            50 subscribers.
        creator(Group): Creator that has reached 50 subscribers.

    """
    email_log = private.get_email_log_for_user_and_template(
        user=creator.user,
        template_name=constants.CREATOR_50_FOLLOWERS_TEMPLATE
    )
    # If the email was already sent to the user, don't send it again
    # since it is a one time email.
    if email_log:
        return

    private.send_email_for_user(
        subject=constants.CREATOR_50_FOLLOWERS_TEMPLATE_SUBJECT,
        user=creator.user,
        template_name=constants.CREATOR_50_FOLLOWERS_TEMPLATE,
        merge_vars={},
        from_email=constants.CREATOR_50_FOLLOWERS_FROM_EMAIL
    )


@receiver(conversations_signals.group_marked_published)
def send_email_for_stream_setup_to_creator(sender, group, *args, **kwargs):
    """Sends email once a creator's stream is set up on the platform.

    Args:
        sender(Group.__class__): Class repr of group that was published.
        group(Group): Group that was marked published.

    """
    if not _can_send_setup_message_for_group(group):
        return False

    tasks.send_stream_setup_email_to_creator.apply_async(
        args=(group.id, ),
        countdown=120
    )


@receiver(creator_signals.analytics_enabled_for_creator)
def send_email_for_stream_setup_to_creator(sender, creator, *args, **kwargs):
    """Sends email once a creator's stream is set up on the platform.

    Args:
        sender(Creator.__class__): Class repr of creator for which analytics
            are enabled.
        creator(Creator): Creator for which analytics are enabled.

    """
    tasks.send_email_for_group_analytics_to_creator.apply_async(
        args=(creator.id, ),
        countdown=120
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

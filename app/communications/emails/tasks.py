from celery.task import task
from django.utils import timezone

from communications.emails import private, constants
from conversations import models as conversation_models, public as conversation_public
from crater.creator import models as creator_models


@task
def send_stream_setup_email_to_creator(group_id):
    """Send email to creator when his stream is set up on the platform.

    Args:
        group_id(int): ID of the group we are sending the email for.

    """
    group = conversation_models.Group.objects.get(id=group_id)

    group_start = group.start
    if not timezone.is_aware(group_start):
        group_start = timezone.make_aware(group_start, timezone=pytz.timezone(settings.TIME_ZONE))

    now_time = timezone.now()
    if not timezone.is_aware(now_time):
        now_time = timezone.make_aware(now_time, timezone=pytz.timezone(settings.TIME_ZONE))

    # Don't send the email if the group start is less than now time.
    if group_start <= now_time:
        return

    diff = now_time - group_start
    diff_minutes = diff.seconds / 60
    # If the group is marked published within 30 minutes of group start
    # don't send the published email.
    if diff_minutes < 30:
        return

    host = group.host
    to_email = host.email

    merge_vars = {
        to_email:
            {
                "date": group.get_display_start(),
                "session_img": group.get_image_url(),
                "session_page": conversation_public.get_session_link_for_webinar(group),
                "stream_page": conversation_public.get_livestream_link_for_webinar(group)
            }
    }

    private.send_email_for_user(
        subject=constants.CREATOR_STREAM_SETUP_TEMPLATE_SUBJECT,
        user=host,
        template_name=constants.CREATOR_STREAM_SETUP_TEMPLATE,
        merge_vars=merge_vars,
        from_email=constants.CREATOR_STREAM_SETUP_FROM_EMAIL
    )


@task
def send_email_for_group_analytics_to_creator(creator_id):
    """Sends email about group analytics for recently closed
        group to the host of the group.

    Args:
        creator_id(int): ID for creator we are sending the
            email to.

    """
    creator = creator_models.Creator.objects.get(id=creator_id)

    private.send_email_for_user(
        subject=constants.CREATOR_STREAM_ANALYTICS_TEMPLATE_SUBJECT,
        user=creator.user,
        template_name=constants.CREATOR_STREAM_ANALYTICS_TEMPLATE,
        merge_vars={},
        from_email=constants.CREATOR_STREAM_ANALYTICS_FROM_EMAIL
    )

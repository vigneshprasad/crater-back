from celery.task import task

from communications.emails import private, constants
from conversations import models as conversation_models, public as conversation_public


@task
def send_stream_setup_email_to_creator(group_id):
    """Send email to creator when his stream is set up on the platform.

    Args:
        group_id(int): ID of the group we are sending the email for.

    """
    group = conversation_models.Group.objects.get(id=group_id)

    host = group.host
    to_email = host.email

    merge_vars = {
        to_email:
            {
                "date": group.get_display_start(),
                "session_img": group.topic.image.url,
                "session_page": conversation_public.get_session_link_for_webinar(group),
                "stream_page": conversation_public.get_livestream_link_for_webinar(group)
            }
    }

    private.send_email_for_user(
        subject=constants.CREATOR_STREAM_SETUP_TEMPLATE_SUBJECT,
        user=host,
        template_name=constants.CREATOR_STREAM_SETUP_TEMPLATE,
        merge_vars=merge_vars,
        from_email="hello@worknetwork.in"
    )

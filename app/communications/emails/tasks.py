from celery.task import task

from communications.emails import private, constants
from conversations import models as conversation_models


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
                "session_page": "https://crater.club/session/{}".format(group.id),
                "stream_page": "https://crater.club/livestream/{}".format(group.id)
            }
    }

    private.send_email(
        subject="Your stream on Crater is setup!",
        to=[to_email],
        template_name=constants.CREATOR_STREAM_SETUP_TEMPLATE,
        merge_vars=merge_vars,
        from_email=""
    )

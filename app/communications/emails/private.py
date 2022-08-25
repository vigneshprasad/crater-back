import logging

from celery.task import task
from django.conf import settings
from django.core.mail import EmailMessage

from communications.emails import models

LOGGER = logging.getLogger(__name__)


@task
def send_email_for_user(
        subject,
        user,
        template_name,
        content=None,
        merge_vars=None,
        **kwargs
):
    # Get optional arguments from kwargs.
    to_email = user.email
    reply_to = kwargs.get("reply_to", [])
    cc = kwargs.get("cc", [])
    bcc = kwargs.get("bcc", [])
    from_email = kwargs.get("from_email", settings.DEFAULT_FROM_EMAIL)

    # Default the merge_vars to content to a dict.
    content = content or {}
    merge_vars = merge_vars or {}
    for merge_var in merge_vars.values():
        merge_var.update({"front_url": settings.FRONT_URL})

    # Get email template object.
    email_template, _ = models.EmailTemplate.objects.get_or_create(
        name=template_name,
        defaults={
            "subject": subject,
            "from_email": from_email
        }
    )

    # Create email message.
    email_message = EmailMessage(
        subject=email_template.subject or subject,
        from_email=email_template.from_email or from_email,
        to=[to_email],
        cc=cc,
        bcc=bcc,
        reply_to=reply_to
    )
    email_message.template_name = template_name
    email_message.template_content = content
    email_message.merge_vars = merge_vars

    # Create email log for the email.
    email_log = models.EmailLog.objects.create(
        user=user,
        email_template=email_template,
        metadata=merge_vars
    )

    try:
        email_message.send(fail_silently=False)
    except Exception as e:
        LOGGER.error("Email message failed: {}".format(str(e)))
        return False

    # Store ID from the Mandrill's end to the email log object.
    try:
        response = email_message.mandrill_response[0]
        mandrill_id = response["_id"]
        status = response["status"]
    except Exception as e:
        LOGGER.error("Mandrill response not found: {}".format(email_log.id))
        return False

    # Save mandrill response to email logs.
    email_log.email_message_id = mandrill_id
    email_log.status = status
    email_log.save()

    return True


def get_email_log_for_user_and_template(user, template_name):
    """Returns email logs for a user and template.

    Args:
        user(User): User the email was sent to.
        template_name(str): Template that was sent to
            the user.

    """
    try:
        email_template, _ = models.EmailTemplate.objects.get(
            name=template_name
        )
    except models.EmailTemplate.DoesNotExist:
        return

    # Get email log and confirm it was sent to the user.
    # TODO(Nishant): Confirm whether we need to check status here.
    email_log = models.EmailLog.objects.filter(
        user=user,
        email_template=email_template,
        email_message_id__isnull=False,
    ).last()

    return email_log

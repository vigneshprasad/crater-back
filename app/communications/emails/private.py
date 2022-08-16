from celery.task import task
from django.conf import settings
from django.core.mail import EmailMessage


@task
def send_email(
        subject: str,
        to: list,
        template_name: str,
        content: dict,
        merge_vars: dict,
        **kwargs
):
    # Get optional arguments from kwargs.
    reply_to = kwargs.get('reply_to', [])
    cc = kwargs.get('cc', [])
    bcc = kwargs.get('bcc', [])
    from_email = kwargs.get('from_email', settings.DEFAULT_FROM_EMAIL)

    msg = EmailMessage(
        subject=subject,
        from_email=from_email,
        to=to,
        cc=cc,
        bcc=bcc,
        reply_to=reply_to
    )
    msg.template_name = template_name
    msg.template_content = content
    msg.merge_vars = merge_vars
    msg.send()
